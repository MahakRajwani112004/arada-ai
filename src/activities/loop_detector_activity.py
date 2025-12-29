"""Loop Detector Activity for Temporal workflows.

Detects when an agent is asking for information that has already been
provided in the conversation history, preventing infinite question loops.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from temporalio import activity

from src.llm import LLMClient, LLMMessage
from src.models.llm_config import LLMConfig


@dataclass
class LoopDetectorInput:
    """Input for loop detection activity."""

    # Full conversation history
    conversation_history: List[Dict[str, str]]

    # The agent's current response
    current_response: str

    # User ID for analytics
    user_id: str

    # Optional: Detector model override
    detector_model: str = "gpt-4o-mini"
    detector_provider: str = "openai"


@dataclass
class LoopDetectorOutput:
    """Output from loop detection activity."""

    # Whether a loop was detected
    is_loop: bool

    # Explanation of why this is/isn't a loop
    reason: str

    # If loop detected, what information was already provided
    already_answered_with: Optional[str] = None

    # Suggested action (e.g., "proceed", "use_previous_answer")
    suggested_action: str = "proceed"


LOOP_DETECTOR_PROMPT = """You are a loop detection assistant. Your job is to determine if an AI agent is asking for information that has already been provided in the conversation.

You will be given:
1. The full conversation history
2. The agent's current response

Your task is to determine:
1. Is the agent asking a question or requesting information?
2. If yes, has that exact information already been provided in the conversation?

IMPORTANT RULES:
- Only flag as a loop if the EXACT information requested has been provided
- Clarifying questions for different/additional information are NOT loops
- If the agent is providing a response (not asking), this is NOT a loop
- Be conservative - only flag clear loops

Respond in this exact JSON format:
{
  "is_loop": true/false,
  "reason": "brief explanation",
  "already_answered_with": "the previous answer if is_loop is true, otherwise null",
  "suggested_action": "proceed" or "use_previous_answer"
}"""


@activity.defn
async def detect_loop(input: LoopDetectorInput) -> LoopDetectorOutput:
    """Detect if the agent is in a question loop."""
    activity.logger.info(
        f"Detecting loop: history_length={len(input.conversation_history)}"
    )

    # If no conversation history, can't be a loop
    if not input.conversation_history:
        return LoopDetectorOutput(
            is_loop=False,
            reason="No conversation history to check against",
            suggested_action="proceed",
        )

    config = LLMConfig(
        provider=input.detector_provider,
        model=input.detector_model,
        temperature=0.0,  # Deterministic
        max_tokens=256,
    )

    provider = LLMClient.get_provider(config)

    # Format conversation history (last 10 messages for context)
    history_text = "\n".join([
        f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
        for msg in input.conversation_history[-10:]
    ])

    user_prompt = f"""## Conversation History
{history_text}

## Agent's Current Response
{input.current_response}

Is this a loop (asking for information already provided)?"""

    messages = [
        LLMMessage(role="system", content=LOOP_DETECTOR_PROMPT),
        LLMMessage(role="user", content=user_prompt),
    ]

    response = await provider.complete(
        messages=messages,
        user_id=input.user_id,
    )

    activity.logger.info(f"Loop detector response: {response.content[:200]}")

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

        return LoopDetectorOutput(
            is_loop=result.get("is_loop", False),
            reason=result.get("reason", ""),
            already_answered_with=result.get("already_answered_with"),
            suggested_action=result.get("suggested_action", "proceed"),
        )

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        activity.logger.warning(f"Failed to parse loop detector response: {e}")
        # Default to no loop if parsing fails (don't block normal flow)
        return LoopDetectorOutput(
            is_loop=False,
            reason=f"Parse error: {e}",
            suggested_action="proceed",
        )
