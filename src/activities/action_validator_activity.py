"""Action Validator Activity for Temporal workflows.

This activity validates whether an agent's response correctly completed
the expected action (e.g., called a tool when required).

Uses a fast LLM (gpt-4o-mini) to analyze the response and determine
if a retry with forced tool_choice is needed.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import activity

from src.llm import LLMClient, LLMMessage
from src.models.llm_config import LLMConfig


@dataclass
class ActionValidatorInput:
    """Input for action validation activity."""

    # What the agent is supposed to do
    agent_description: str

    # Available tools the agent could call
    available_tools: List[Dict[str, Any]]  # [{name, description}, ...]

    # The user's request
    user_input: str

    # The agent's response
    agent_response: str

    # Whether any tool calls were made
    tool_calls_made: List[Dict[str, Any]]  # [{name, arguments}, ...]

    # User ID for analytics
    user_id: str

    # Optional: Validator model override (default: gpt-4o-mini)
    validator_model: str = "gpt-4o-mini"
    validator_provider: str = "openai"


@dataclass
class ActionValidatorOutput:
    """Output from action validation activity."""

    # Whether the action was completed correctly
    is_valid: bool

    # Whether to retry with forced tool_choice
    should_retry_with_tool: bool

    # Which tool should be forced (if should_retry_with_tool is True)
    suggested_tool: Optional[str] = None

    # Explanation of the validation result
    reason: str = ""


VALIDATOR_SYSTEM_PROMPT = """You are an action validation assistant. Your job is to determine if an AI agent correctly completed the expected action based on its response.

You will be given:
1. Agent's purpose/description
2. Available tools the agent can use
3. User's request
4. Agent's response
5. Tools that were called (if any)

Your task is to determine:
1. Did the agent complete the expected action?
2. If a tool should have been called but wasn't, which tool?

IMPORTANT RULES:
- If the agent is still gathering information (asking questions), this is VALID - no tool call expected yet
- If the agent says it WILL generate/create something but didn't actually call the tool, this is INVALID
- If the agent says it "has created" or "generated" something without calling a tool, this is INVALID
- Tool calls are required for ACTUAL document generation, file creation, email sending, etc.

Respond in this exact JSON format:
{
  "is_valid": true/false,
  "should_retry_with_tool": true/false,
  "suggested_tool": "tool_name_or_null",
  "reason": "brief explanation"
}"""


@activity.defn
async def validate_action(input: ActionValidatorInput) -> ActionValidatorOutput:
    """
    Validate whether an agent's response correctly completed the expected action.

    Uses a fast LLM to analyze the response and determine if tool calling was needed.
    """
    activity.logger.info(
        f"Validating action: tools_available={len(input.available_tools)}, "
        f"tools_called={len(input.tool_calls_made)}"
    )

    # Build config for fast/cheap validation model
    config = LLMConfig(
        provider=input.validator_provider,
        model=input.validator_model,
        temperature=0.0,  # Deterministic
        max_tokens=256,  # Short response needed
    )

    provider = LLMClient.get_provider(config)

    # Format tools list
    tools_list = "\n".join([
        f"- {t['name']}: {t.get('description', 'No description')}"
        for t in input.available_tools
    ]) if input.available_tools else "No tools available"

    # Format tool calls made
    if input.tool_calls_made:
        calls_made = "\n".join([
            f"- {tc['name']}({tc.get('arguments', {})})"
            for tc in input.tool_calls_made
        ])
    else:
        calls_made = "No tools were called"

    # Build validation prompt
    user_prompt = f"""## Agent's Purpose
{input.agent_description}

## Available Tools
{tools_list}

## User's Request
{input.user_input}

## Agent's Response
{input.agent_response}

## Tools Called
{calls_made}

Based on this information, did the agent correctly complete the expected action?"""

    messages = [
        LLMMessage(role="system", content=VALIDATOR_SYSTEM_PROMPT),
        LLMMessage(role="user", content=user_prompt),
    ]

    response = await provider.complete(
        messages=messages,
        user_id=input.user_id,
    )

    activity.logger.info(f"Validator response: {response.content[:200]}")

    # Parse the JSON response
    try:
        import json
        # Try to extract JSON from the response
        content = response.content.strip()

        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        return ActionValidatorOutput(
            is_valid=result.get("is_valid", True),
            should_retry_with_tool=result.get("should_retry_with_tool", False),
            suggested_tool=result.get("suggested_tool"),
            reason=result.get("reason", ""),
        )

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        activity.logger.warning(f"Failed to parse validator response: {e}")
        # Default to valid if parsing fails (don't block normal flow)
        return ActionValidatorOutput(
            is_valid=True,
            should_retry_with_tool=False,
            reason=f"Validation parse error: {e}",
        )
