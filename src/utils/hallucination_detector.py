"""Hallucination risk detection for AI agents.

Detects when agents claim to access external data but lack the
necessary tools/MCPs to actually retrieve that data.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class HallucinationWarning:
    """Warning about potential hallucination risk."""
    severity: str  # "high", "medium", "low"
    message: str
    suggestion: str
    affected_step: Optional[str] = None


# Keywords that suggest the agent needs external data access
DATA_ACCESS_KEYWORDS = {
    # Order/E-commerce related
    "order", "orders", "order status", "shipping", "tracking", "delivery",
    "purchase", "transaction", "invoice", "payment", "refund",

    # User/Account related
    "account", "user data", "profile", "customer", "member", "subscription",
    "balance", "history", "records",

    # Database operations
    "database", "lookup", "query", "fetch", "retrieve", "search records",
    "find in", "check status", "get details", "pull data",

    # Calendar/Scheduling
    "calendar", "meeting", "appointment", "schedule", "event", "booking",

    # Email/Communication
    "email", "inbox", "messages", "notifications", "send email",

    # File/Document access
    "file", "document", "spreadsheet", "report", "download",

    # CRM/Sales
    "lead", "contact", "opportunity", "deal", "pipeline", "crm",

    # Inventory/Stock
    "inventory", "stock", "warehouse", "quantity", "availability",

    # API integrations
    "api", "external service", "third-party", "integration",
}

# Keywords that suggest read-only/generative tasks (lower risk)
GENERATIVE_KEYWORDS = {
    "generate", "write", "create content", "summarize", "explain",
    "translate", "analyze text", "creative", "brainstorm", "suggest",
    "recommend", "advice", "help with", "assist",
}

# MCP templates that provide data access
DATA_ACCESS_MCPS = {
    # Databases
    "postgres", "postgresql", "mysql", "mongodb", "sqlite", "redis",
    "supabase", "firebase", "dynamodb",

    # E-commerce
    "shopify", "stripe", "woocommerce", "magento",

    # CRM
    "salesforce", "hubspot", "pipedrive", "zoho",

    # Calendar/Email
    "google-calendar", "outlook", "gmail", "microsoft-365",

    # Communication
    "slack", "discord", "twilio", "sendgrid",

    # File storage
    "google-drive", "dropbox", "s3", "azure-blob",

    # Generic
    "rest-api", "graphql", "webhook",
}


def detect_data_access_intent(text: str) -> Set[str]:
    """Detect keywords suggesting external data access needs.

    Args:
        text: Agent description, goal, or instructions

    Returns:
        Set of detected data access keywords
    """
    text_lower = text.lower()
    detected = set()

    for keyword in DATA_ACCESS_KEYWORDS:
        # Use word boundary matching to avoid partial matches
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            detected.add(keyword)

    return detected


def is_generative_task(text: str) -> bool:
    """Check if the task is primarily generative (lower hallucination risk).

    Args:
        text: Agent description or goal

    Returns:
        True if task appears to be generative
    """
    text_lower = text.lower()

    generative_count = sum(1 for kw in GENERATIVE_KEYWORDS if kw in text_lower)
    data_access_count = sum(1 for kw in DATA_ACCESS_KEYWORDS if kw in text_lower)

    # Consider it generative if generative keywords dominate
    return generative_count > data_access_count


def check_agent_hallucination_risk(
    agent_name: str,
    agent_goal: str,
    agent_description: Optional[str] = None,
    enabled_tools: Optional[List[str]] = None,
    connected_mcps: Optional[List[str]] = None,
    step_id: Optional[str] = None,
) -> List[HallucinationWarning]:
    """Check if an agent is at risk of hallucinating data.

    Args:
        agent_name: Name of the agent
        agent_goal: The agent's goal/objective
        agent_description: Optional description
        enabled_tools: List of enabled tool names
        connected_mcps: List of connected MCP template names
        step_id: Optional workflow step ID for context

    Returns:
        List of warnings about hallucination risks
    """
    warnings = []
    enabled_tools = enabled_tools or []
    connected_mcps = connected_mcps or []

    # Combine text for analysis
    full_text = f"{agent_name} {agent_goal} {agent_description or ''}"

    # Detect data access intent
    data_keywords = detect_data_access_intent(full_text)

    if not data_keywords:
        return warnings  # No data access detected, low risk

    # Check if task is primarily generative
    if is_generative_task(full_text):
        return warnings  # Generative tasks are lower risk

    # Check if agent has tools/MCPs for data access
    has_data_tools = len(enabled_tools) > 0
    has_data_mcps = any(
        mcp.lower() in DATA_ACCESS_MCPS or
        any(data_mcp in mcp.lower() for data_mcp in DATA_ACCESS_MCPS)
        for mcp in connected_mcps
    )

    # Generate warnings based on findings
    if not has_data_tools and not has_data_mcps:
        # High risk: Claims data access but has no tools/MCPs
        keywords_str = ", ".join(sorted(data_keywords)[:5])
        warnings.append(HallucinationWarning(
            severity="high",
            message=(
                f"Agent '{agent_name}' appears to need external data access "
                f"(detected: {keywords_str}) but has no tools or MCP connections configured. "
                f"The agent will likely hallucinate fake data."
            ),
            suggestion=(
                "Connect an appropriate MCP server (e.g., database, API) or "
                "configure tools that can access the required data. "
                "Without data sources, the agent cannot retrieve real information."
            ),
            affected_step=step_id,
        ))
    elif has_data_mcps and not has_data_tools:
        # Medium risk: Has MCPs but tools might not be enabled
        warnings.append(HallucinationWarning(
            severity="medium",
            message=(
                f"Agent '{agent_name}' has MCP connections but may not have "
                f"the specific tools enabled to access the data it needs."
            ),
            suggestion=(
                "Verify that the agent has the correct tools enabled from "
                "the connected MCP servers."
            ),
            affected_step=step_id,
        ))

    return warnings


def check_workflow_hallucination_risk(
    steps: List[dict],
    connected_mcps: Optional[List[str]] = None,
) -> List[HallucinationWarning]:
    """Check all workflow steps for hallucination risks.

    Args:
        steps: List of workflow step dictionaries
        connected_mcps: List of connected MCP template names

    Returns:
        List of warnings for all steps
    """
    all_warnings = []

    for step in steps:
        step_type = step.get("type", "agent")
        if step_type != "agent":
            continue

        # Check agent_id steps
        agent_id = step.get("agent_id")
        suggested = step.get("suggested_agent")

        if suggested:
            # Check suggested agent
            warnings = check_agent_hallucination_risk(
                agent_name=suggested.get("name", "Unknown"),
                agent_goal=suggested.get("goal", ""),
                agent_description=suggested.get("description"),
                enabled_tools=suggested.get("suggested_tools", []),
                connected_mcps=suggested.get("required_mcps", []) or connected_mcps,
                step_id=step.get("id"),
            )
            all_warnings.extend(warnings)
        elif not agent_id:
            # No agent configured at all
            all_warnings.append(HallucinationWarning(
                severity="high",
                message=f"Step '{step.get('id')}' has no agent configured.",
                suggestion="Assign an agent to this step before running the workflow.",
                affected_step=step.get("id"),
            ))

    return all_warnings
