"""Hallucination Checker Activity for Temporal workflows.

Verifies that an agent's response is grounded in the provided context
(retrieved documents, tool results) and flags ungrounded claims.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import activity

from src.llm import LLMClient, LLMMessage
from src.models.llm_config import LLMConfig


@dataclass
class HallucinationCheckerInput:
    """Input for hallucination checking activity."""

    # The agent's response to check
    agent_response: str

    # Retrieved context from RAG (if any)
    retrieved_context: Optional[str] = None

    # Results from tool calls (if any)
    tool_results: Optional[List[Dict[str, Any]]] = None

    # User ID for analytics
    user_id: str = ""

    # Original user query (for context)
    user_query: Optional[str] = None

    # Optional: Checker model override
    checker_model: str = "gpt-4o-mini"
    checker_provider: str = "openai"


@dataclass
class HallucinationCheckerOutput:
    """Output from hallucination checking activity."""

    # Whether the response is fully grounded
    is_grounded: bool

    # List of claims that appear ungrounded
    ungrounded_claims: List[str] = field(default_factory=list)

    # Suggested fix (rewritten response grounded in facts)
    suggested_fix: Optional[str] = None

    # Confidence in the assessment (0-1)
    confidence: float = 0.0

    # Explanation of the assessment
    reason: str = ""


HALLUCINATION_CHECKER_PROMPT = """You are a hallucination detection assistant. Your job is to catch factual errors where an AI agent's response CONTRADICTS the provided context.

You will be given:
1. The agent's response
2. Retrieved context (documents from knowledge base)
3. Tool results (outputs from tool/API calls)
4. Original user query

Your task is to:
1. Identify factual claims in the agent's response
2. Check if any claim DIRECTLY CONTRADICTS the provided context or tool results
3. Only flag claims that are demonstrably WRONG based on the evidence

CRITICAL RULES:
- ONLY flag claims that CONTRADICT the context (e.g., context says "price is $10" but response says "$20")
- DO NOT flag claims that are simply MISSING from the context - the LLM may have valid knowledge beyond what was retrieved
- DO NOT flag additional information the LLM provides that doesn't conflict with context
- Generic greetings, transitions, and formatting are NOT claims to check
- Claims based on common knowledge are acceptable
- Be very conservative - only flag clear, direct contradictions
- When in doubt, mark as grounded

Respond in this exact JSON format:
{
  "is_grounded": true/false,
  "ungrounded_claims": ["claim1", "claim2"],
  "suggested_fix": "corrected response or null",
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}"""


@activity.defn
async def check_hallucination(input: HallucinationCheckerInput) -> HallucinationCheckerOutput:
    """Check if the agent's response contains hallucinations."""
    activity.logger.info(
        f"Checking hallucination: response_length={len(input.agent_response)}, "
        f"has_context={input.retrieved_context is not None}, "
        f"has_tools={input.tool_results is not None}"
    )

    # If no context provided, skip check (can't detect hallucinations without ground truth)
    if not input.retrieved_context and not input.tool_results:
        return HallucinationCheckerOutput(
            is_grounded=True,
            reason="No context provided to check against - assuming valid",
            confidence=0.5,
        )

    config = LLMConfig(
        provider=input.checker_provider,
        model=input.checker_model,
        temperature=0.0,  # Deterministic
        max_tokens=512,
    )

    provider = LLMClient.get_provider(config)

    # Format context
    context_parts = []
    if input.retrieved_context:
        context_parts.append(f"## Retrieved Documents\n{input.retrieved_context}")
    if input.tool_results:
        import json
        tools_text = "\n".join([
            f"- {r.get('tool', 'unknown')}: {json.dumps(r.get('result', r.get('output', {})))}"
            for r in input.tool_results
        ])
        context_parts.append(f"## Tool Results\n{tools_text}")

    context_text = "\n\n".join(context_parts)

    user_prompt = f"""## User Query
{input.user_query or 'Not provided'}

{context_text}

## Agent's Response
{input.agent_response}

Check if the response is grounded in the provided context."""

    messages = [
        LLMMessage(role="system", content=HALLUCINATION_CHECKER_PROMPT),
        LLMMessage(role="user", content=user_prompt),
    ]

    response = await provider.complete(
        messages=messages,
        user_id=input.user_id,
    )

    activity.logger.info(f"Hallucination checker response: {response.content[:200]}")

    # Parse JSON response
    try:
        import json
        content = response.content.strip()

        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        return HallucinationCheckerOutput(
            is_grounded=result.get("is_grounded", True),
            ungrounded_claims=result.get("ungrounded_claims", []),
            suggested_fix=result.get("suggested_fix"),
            confidence=result.get("confidence", 0.8),
            reason=result.get("reason", ""),
        )

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        activity.logger.warning(f"Failed to parse hallucination checker response: {e}")
        # Default to grounded if parsing fails (don't block normal flow)
        return HallucinationCheckerOutput(
            is_grounded=True,
            reason=f"Parse error: {e}",
            confidence=0.5,
        )
