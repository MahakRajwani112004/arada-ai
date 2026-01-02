"""LLM cost calculator with pricing tables for OpenAI and Anthropic."""
from typing import Dict, Tuple

# Pricing in USD per 1K tokens (as of December 2024)
# Format: {provider: {model: {"input": price, "output": price}}}
PRICING: Dict[str, Dict[str, Dict[str, float]]] = {
    "openai": {
        # GPT-4o series
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-2024-11-20": {"input": 0.0025, "output": 0.01},
        "gpt-4o-2024-08-06": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o-mini-2024-07-18": {"input": 0.00015, "output": 0.0006},
        # GPT-4 Turbo
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo-2024-04-09": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        # GPT-4 (legacy)
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        # GPT-3.5
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
        # o1 reasoning models
        "o1-preview": {"input": 0.015, "output": 0.06},
        "o1-preview-2024-09-12": {"input": 0.015, "output": 0.06},
        "o1-mini": {"input": 0.003, "output": 0.012},
        "o1-mini-2024-09-12": {"input": 0.003, "output": 0.012},
    },
    "anthropic": {
        # Claude 3.5 series
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-5-sonnet-20240620": {"input": 0.003, "output": 0.015},
        "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
        "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
        "claude-3-5-haiku-latest": {"input": 0.0008, "output": 0.004},
        # Claude 3 series
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-opus-latest": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        # Shorthand aliases
        "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    },
}

# Default pricing for unknown models (conservative estimate)
DEFAULT_PRICING = {"input": 0.01, "output": 0.03}


def get_model_pricing(provider: str, model: str) -> Dict[str, float]:
    """
    Get pricing for a specific model.

    Args:
        provider: Provider name ("openai" or "anthropic")
        model: Model name

    Returns:
        Dict with "input" and "output" prices per 1K tokens
    """
    provider_pricing = PRICING.get(provider.lower(), {})

    # Try exact match first
    if model in provider_pricing:
        return provider_pricing[model]

    # Try to find a matching prefix (for versioned model names)
    model_lower = model.lower()
    for known_model, pricing in provider_pricing.items():
        if model_lower.startswith(known_model) or known_model.startswith(model_lower):
            return pricing

    # Return default pricing if not found
    return DEFAULT_PRICING


def calculate_cost(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> int:
    """
    Calculate cost in cents for an LLM call.

    Args:
        provider: Provider name ("openai" or "anthropic")
        model: Model name
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Cost in cents (integer, rounded up)
    """
    pricing = get_model_pricing(provider, model)

    # Calculate cost in USD
    input_cost = (prompt_tokens / 1000) * pricing["input"]
    output_cost = (completion_tokens / 1000) * pricing["output"]
    total_cost = input_cost + output_cost

    # Convert to cents and round up (never underestimate cost)
    cost_cents = int(total_cost * 100 + 0.99)  # Effectively ceil

    return cost_cents


def calculate_cost_breakdown(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> Tuple[int, int, int]:
    """
    Calculate detailed cost breakdown.

    Args:
        provider: Provider name
        model: Model name
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Tuple of (input_cost_cents, output_cost_cents, total_cost_cents)
    """
    pricing = get_model_pricing(provider, model)

    input_cost = (prompt_tokens / 1000) * pricing["input"] * 100
    output_cost = (completion_tokens / 1000) * pricing["output"] * 100

    return (
        int(input_cost + 0.99),
        int(output_cost + 0.99),
        int(input_cost + output_cost + 0.99),
    )
