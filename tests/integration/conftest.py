"""Shared fixtures for orchestrator integration tests.

Provides:
- API client with authentication
- Test configuration
- Report data collection
- Detailed trace collection for each test case
"""

import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import pytest

from .trace_collector import (
    DetailedTestTrace,
    TraceCollector,
    get_collector,
    reset_collector,
)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class TestConfig:
    """Test configuration."""

    api_base_url: str = "http://localhost:8000/api/v1"
    orchestrator_id: str = "main-orchestrator"
    admin_email: str = "admin@magure.ai"
    admin_password: str = "admin123"
    timeout: float = 600.0  # 10 minutes per request

    # Test knowledge base
    knowledge_base_id: str = "kb-1638ec52b443"

    # MCP Server IDs
    filesystem_mcp_id: str = "srv_1dc8e1535b21"
    email_mcp_id: str = "srv_0de807a6136f"
    calendar_mcp_id: str = "srv_3110e8c1ce5b"

    # Test Recipients (for email/calendar tests)
    # These are actual team members in the knowledge base
    test_recipients: dict = None

    def __post_init__(self):
        """Initialize test recipients."""
        if self.test_recipients is None:
            self.test_recipients = {
                "yash": {
                    "name": "Yash Karande",
                    "email": "yash.k@magureinc.com",
                    "role": "SDE",
                    "accounts": ["Acme Corporation"],
                },
                "pranav": {
                    "name": "Pranav Agarwal",
                    "email": "pranav.ag@magureinc.com",
                    "role": "CTO",
                    "accounts": ["Globex International"],
                },
            }


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Provide test configuration."""
    return TestConfig(
        api_base_url=os.getenv("MAGONE_API_URL", "http://localhost:8000/api/v1"),
        orchestrator_id=os.getenv("MAGONE_ORCHESTRATOR_ID", "main-orchestrator"),
        admin_email=os.getenv("MAGONE_ADMIN_EMAIL", "admin@magure.ai"),
        admin_password=os.getenv("MAGONE_ADMIN_PASSWORD", "admin123"),
    )


# =============================================================================
# API Client
# =============================================================================

class OrchestratorAPIClient:
    """HTTP client for orchestrator API."""

    def __init__(self, config: TestConfig):
        self.config = config
        self.token: Optional[str] = None
        self.token_timestamp: Optional[float] = None
        self.request_count: int = 0
        self.client = httpx.Client(timeout=config.timeout)
        # Refresh token every 45 minutes or every 50 requests
        self.token_refresh_interval: float = 45 * 60  # 45 minutes
        self.request_refresh_threshold: int = 50

    def authenticate(self) -> str:
        """Authenticate and get access token."""
        response = self.client.post(
            f"{self.config.api_base_url}/auth/login",
            json={
                "email": self.config.admin_email,
                "password": self.config.admin_password,
            },
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        self.token_timestamp = time.time()
        self.request_count = 0
        return self.token

    def _should_refresh_token(self) -> bool:
        """Check if token should be refreshed."""
        if not self.token or not self.token_timestamp:
            return True

        # Refresh if token is older than refresh interval
        elapsed = time.time() - self.token_timestamp
        if elapsed > self.token_refresh_interval:
            return True

        # Refresh after threshold requests
        if self.request_count >= self.request_refresh_threshold:
            return True

        return False

    def _headers(self) -> Dict[str, str]:
        """Get request headers with auth token, auto-refreshing if needed."""
        if self._should_refresh_token():
            self.authenticate()
        return {"Authorization": f"Bearer {self.token}"}

    def chat(
        self,
        message: str,
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send chat message to orchestrator or specific agent.

        Args:
            message: User message
            agent_id: Agent ID (defaults to orchestrator)
            context: Optional context dict

        Returns:
            Response dict with 'response', 'metadata', etc.
        """
        agent = agent_id or self.config.orchestrator_id
        self.request_count += 1

        start_time = time.time()
        response = self.client.post(
            f"{self.config.api_base_url}/workflow/execute",
            headers=self._headers(),
            json={
                "agent_id": agent,
                "user_input": message,
            },
        )
        elapsed_ms = (time.time() - start_time) * 1000

        if response.status_code != 200:
            # Check if token expired and retry once
            if response.status_code == 401 or "expired" in response.text.lower():
                self.authenticate()
                response = self.client.post(
                    f"{self.config.api_base_url}/workflow/execute",
                    headers=self._headers(),
                    json={
                        "agent_id": agent,
                        "user_input": message,
                    },
                )
                elapsed_ms = (time.time() - start_time) * 1000
                if response.status_code == 200:
                    result = response.json()
                    result["elapsed_ms"] = elapsed_ms
                    result["success"] = True
                    return result

            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            }

        result = response.json()
        result["elapsed_ms"] = elapsed_ms
        result["success"] = True
        return result

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details."""
        response = self.client.get(
            f"{self.config.api_base_url}/agents/{agent_id}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents."""
        response = self.client.get(
            f"{self.config.api_base_url}/agents",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json().get("agents", [])

    def close(self):
        """Close HTTP client."""
        self.client.close()


@pytest.fixture(scope="session")
def api_client(test_config: TestConfig) -> OrchestratorAPIClient:
    """Provide authenticated API client."""
    client = OrchestratorAPIClient(test_config)
    client.authenticate()
    yield client
    client.close()


# =============================================================================
# Test Result Collection
# =============================================================================

@dataclass
class TestResult:
    """Single test result."""

    test_id: str
    category: str
    input_query: str
    expected_agents: List[str]
    actual_agents: List[str]
    status: str  # "pass", "fail", "partial", "skip", "error"
    response_preview: str
    elapsed_ms: float
    error_message: Optional[str] = None
    notes: Optional[str] = None
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestReport:
    """Collection of test results for reporting."""

    results: List[TestResult] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None

    def add_result(self, result: TestResult):
        """Add a test result."""
        self.results.append(result)

    def finalize(self):
        """Mark report as complete."""
        self.end_time = datetime.now().isoformat()

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "pass")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "fail")

    @property
    def partial(self) -> int:
        return sum(1 for r in self.results if r.status == "partial")

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == "skip")

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.status == "error")

    @property
    def pass_rate(self) -> float:
        executed = self.total - self.skipped
        if executed == 0:
            return 0.0
        return (self.passed / executed) * 100

    @property
    def avg_elapsed_ms(self) -> float:
        executed = [r for r in self.results if r.status != "skip"]
        if not executed:
            return 0.0
        return sum(r.elapsed_ms for r in executed) / len(executed)

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# MagoneAI Orchestrator Test Report",
            "",
            f"**Generated:** {self.end_time or datetime.now().isoformat()}",
            f"**Test Period:** {self.start_time} to {self.end_time or 'ongoing'}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Tests | {self.total} |",
            f"| Passed | {self.passed} |",
            f"| Failed | {self.failed} |",
            f"| Partial | {self.partial} |",
            f"| Errors | {self.errors} |",
            f"| Skipped | {self.skipped} |",
            f"| Pass Rate | {self.pass_rate:.1f}% |",
            f"| Avg Response Time | {self.avg_elapsed_ms:.0f}ms |",
            "",
            "---",
            "",
        ]

        # Group results by category
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = []
            categories[r.category].append(r)

        for category, results in categories.items():
            lines.append(f"## {category}")
            lines.append("")
            lines.append("| ID | Query | Expected | Actual | Status | Time |")
            lines.append("|----|-------|----------|--------|--------|------|")

            for r in results:
                status_emoji = {
                    "pass": "✅",
                    "fail": "❌",
                    "partial": "⚠️",
                    "skip": "⏭️",
                    "error": "💥",
                }.get(r.status, "❓")

                query_short = r.input_query[:40] + "..." if len(r.input_query) > 40 else r.input_query
                expected = ", ".join(r.expected_agents) or "-"
                actual = ", ".join(r.actual_agents) or "-"

                lines.append(
                    f"| {r.test_id} | {query_short} | {expected} | {actual} | "
                    f"{status_emoji} {r.status.upper()} | {r.elapsed_ms:.0f}ms |"
                )

            lines.append("")

        # Detailed results for failures
        failures = [r for r in self.results if r.status in ("fail", "error")]
        if failures:
            lines.append("---")
            lines.append("")
            lines.append("## Failed Test Details")
            lines.append("")

            for r in failures:
                lines.append(f"### {r.test_id}")
                lines.append("")
                lines.append(f"**Query:** {r.input_query}")
                lines.append("")
                lines.append(f"**Expected Agents:** {', '.join(r.expected_agents)}")
                lines.append("")
                lines.append(f"**Actual Agents:** {', '.join(r.actual_agents)}")
                lines.append("")
                if r.error_message:
                    lines.append(f"**Error:** {r.error_message}")
                    lines.append("")
                if r.response_preview:
                    lines.append(f"**Response Preview:** {r.response_preview[:200]}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        # Skipped tests summary
        skipped = [r for r in self.results if r.status == "skip"]
        if skipped:
            lines.append("## Skipped Tests (Pending Prerequisites)")
            lines.append("")
            for r in skipped:
                lines.append(f"- **{r.test_id}**: {r.notes or r.input_query[:50]}")
            lines.append("")

        return "\n".join(lines)

    def save(self, filepath: str):
        """Save report to file."""
        self.finalize()
        with open(filepath, "w") as f:
            f.write(self.to_markdown())


# Global report instance for collecting results across test modules
_report: Optional[TestReport] = None


def get_report() -> TestReport:
    """Get or create global test report."""
    global _report
    if _report is None:
        _report = TestReport()
    return _report


@pytest.fixture(scope="session")
def test_report() -> TestReport:
    """Provide test report for result collection."""
    return get_report()


# =============================================================================
# Trace Collector
# =============================================================================

@pytest.fixture(scope="session")
def trace_collector(api_client: OrchestratorAPIClient) -> TraceCollector:
    """Provide trace collector for detailed test tracing."""
    collector = reset_collector()
    collector.set_token(api_client.token)
    yield collector
    # Save all traces on teardown
    collector.save_all_traces()
    collector.save_summary()
    collector.save_markdown_report()
    collector.close()


# =============================================================================
# Test Helpers
# =============================================================================

def extract_agents_from_response(response: Dict[str, Any]) -> List[str]:
    """Extract list of agents used from response metadata."""
    agents = []

    # Check metadata for agent calls
    metadata = response.get("metadata", {})

    # Look for tool_calls that reference agents
    tool_calls = metadata.get("tool_calls", [])
    for tc in tool_calls:
        tool_name = tc.get("tool", "")
        if tool_name.startswith("agent:"):
            agents.append(tool_name.replace("agent:", ""))

    # Also check agent_chain if present
    agent_chain = metadata.get("agent_chain", [])
    agents.extend(agent_chain)

    # Check delegations
    delegations = metadata.get("delegations", [])
    for d in delegations:
        if isinstance(d, dict) and "agent_id" in d:
            agents.append(d["agent_id"])
        elif isinstance(d, str):
            agents.append(d)

    return list(dict.fromkeys(agents))  # Remove duplicates, preserve order


# Keyword synonyms and variants for flexible matching
KEYWORD_SYNONYMS = {
    "inbox": ["inbox", "unread", "emails", "mail", "mailbox"],
    "send": ["send", "sent", "sending", "deliver", "delivered"],
    "email": ["email", "mail", "message", "emails"],
    "block": ["block", "blocked", "blocking", "schedule", "scheduled", "created", "booked"],
    "focus": ["focus", "deep work", "focused", "concentration", "work session"],
    "free": ["free", "available", "open", "availability", "slot"],
    "available": ["available", "free", "open", "availability"],
    "faq": ["faq", "frequently asked", "questions", "answer", "help", "document"],
    "return": ["return", "refund", "exchange", "returns", "policy"],
    "privacy": ["privacy", "data protection", "personal data", "gdpr", "policy"],
    "meeting": ["meeting", "appointment", "event", "call", "session"],
    "recurring": ["recurring", "repeat", "weekly", "daily", "monthly"],
    # Document generation - when document is created successfully
    "document": ["document", "created", "download", "generated", "file"],
    "created": ["created", "generated", "successfully", "completed"],
}


def _check_keyword_match(keyword: str, content: str) -> bool:
    """Check if a keyword or its synonyms/variants exist in content.

    Handles:
    - Case-insensitive matching
    - Synonym matching
    - Basic word stem matching (e.g., send/sent/sending)
    """
    content_lower = content.lower()
    keyword_lower = keyword.lower()

    # Direct match
    if keyword_lower in content_lower:
        return True

    # Check synonyms
    if keyword_lower in KEYWORD_SYNONYMS:
        for synonym in KEYWORD_SYNONYMS[keyword_lower]:
            if synonym.lower() in content_lower:
                return True

    # Basic stem matching for common verb forms
    stems = [
        keyword_lower,
        keyword_lower + "s",     # plurals
        keyword_lower + "ed",    # past tense
        keyword_lower + "ing",   # gerund
        keyword_lower + "d",     # past tense (e.g., create -> created)
    ]
    # Also check if keyword ends in 'e' (e.g., schedule -> scheduled)
    if keyword_lower.endswith("e"):
        stems.append(keyword_lower[:-1] + "ing")  # schedule -> scheduling
        stems.append(keyword_lower + "d")  # schedule -> scheduled

    for stem in stems:
        if stem in content_lower:
            return True

    return False


def validate_response_quality(
    response: Dict[str, Any],
    required_keywords: Optional[List[str]] = None,
    min_length: int = 10,
) -> tuple[bool, str]:
    """Validate response quality.

    Returns:
        Tuple of (is_valid, reason)
    """
    if not response.get("success", False):
        return False, f"Request failed: {response.get('error', 'Unknown error')}"

    content = response.get("content", "")

    if not content:
        return False, "Empty response"

    if len(content) < min_length:
        return False, f"Response too short ({len(content)} chars)"

    if required_keywords:
        missing = [kw for kw in required_keywords if not _check_keyword_match(kw, content)]
        if missing:
            return False, f"Missing keywords: {missing}"

    return True, "OK"


@pytest.fixture
def response_validator():
    """Provide response validation helper."""
    return validate_response_quality


def record_detailed_trace(
    collector: TraceCollector,
    test_id: str,
    test_name: str,
    category: str,
    query: str,
    expected_agents: List[str],
    response: Dict[str, Any],
    keywords: Optional[List[str]] = None,
) -> DetailedTestTrace:
    """Record a detailed trace for a test case.

    Args:
        collector: TraceCollector instance
        test_id: Test identifier (e.g., "D1", "DW2")
        test_name: Full test name
        category: Test category
        query: Input query
        expected_agents: Expected agent IDs
        response: API response dict
        keywords: Optional validation keywords

    Returns:
        DetailedTestTrace with populated data
    """
    # Create trace
    trace = collector.create_trace(
        test_id=test_id,
        test_name=test_name,
        category=category,
        input_query=query,
        expected_agents=expected_agents,
    )

    # Populate from response
    collector.populate_from_response(trace, response)

    # Validate and set status
    is_valid, reason = validate_response_quality(response, keywords)

    if not response.get("success"):
        trace.status = "error"
        trace.error_message = response.get("error", "Unknown error")
    elif not is_valid:
        trace.status = "fail"
        trace.error_message = reason
        trace.validation_notes = reason
    else:
        # Check agent matching
        actual_set = set(trace.actual_agents)
        expected_set = set(expected_agents)

        if expected_set <= actual_set or not expected_agents:
            trace.status = "pass"
        elif any(ea in actual_set for ea in expected_agents):
            trace.status = "partial"
            trace.validation_notes = f"Expected {expected_agents}, got {trace.actual_agents}"
        else:
            trace.status = "fail"
            trace.validation_notes = f"Expected {expected_agents}, got {trace.actual_agents}"

    # Fetch workflow details from Temporal
    collector.fetch_workflow_details(trace)

    # Save individual trace immediately
    collector.save_trace(trace)

    return trace
