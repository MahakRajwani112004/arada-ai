"""Detailed trace collector for orchestrator integration tests.

Captures:
- Full API response with metadata
- Temporal workflow history
- Agent execution chains
- MCP tool calls
- Input/output at each step
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class ToolCallTrace:
    """Single tool call trace."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    duration_ms: Optional[float] = None


@dataclass
class AgentExecutionTrace:
    """Single agent execution trace."""
    agent_id: str
    agent_type: Optional[str] = None
    input_query: str = ""
    output_content: str = ""
    success: bool = True
    error: Optional[str] = None
    tool_calls: List[ToolCallTrace] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    child_agents: List["AgentExecutionTrace"] = field(default_factory=list)


@dataclass
class WorkflowHistoryEvent:
    """Temporal workflow history event."""
    event_id: int
    event_type: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetailedTestTrace:
    """Complete trace for a single test case."""
    test_id: str
    test_name: str
    category: str
    timestamp: str

    # Input
    input_query: str
    expected_agents: List[str]

    # API Response
    api_response: Dict[str, Any] = field(default_factory=dict)
    workflow_id: Optional[str] = None

    # Execution Details
    actual_agents: List[str] = field(default_factory=list)
    agent_chain: List[AgentExecutionTrace] = field(default_factory=list)
    total_tool_calls: int = 0

    # Temporal Details
    workflow_status: Optional[str] = None
    workflow_history: List[WorkflowHistoryEvent] = field(default_factory=list)
    activities_executed: List[Dict[str, Any]] = field(default_factory=list)

    # Performance
    total_elapsed_ms: float = 0.0

    # Result
    final_output: str = ""
    success: bool = False
    status: str = "unknown"
    error_message: Optional[str] = None
    validation_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "category": self.category,
            "timestamp": self.timestamp,
            "input": {
                "query": self.input_query,
                "expected_agents": self.expected_agents,
            },
            "api_response": self.api_response,
            "workflow_id": self.workflow_id,
            "execution": {
                "actual_agents": self.actual_agents,
                "agent_chain": [self._trace_to_dict(a) for a in self.agent_chain],
                "total_tool_calls": self.total_tool_calls,
            },
            "temporal": {
                "workflow_status": self.workflow_status,
                "activities_executed": self.activities_executed,
                "workflow_history_summary": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp,
                    }
                    for e in self.workflow_history[:50]  # Limit history
                ],
            },
            "performance": {
                "total_elapsed_ms": self.total_elapsed_ms,
            },
            "result": {
                "final_output": self.final_output[:5000] if self.final_output else "",  # Truncate
                "success": self.success,
                "status": self.status,
                "error_message": self.error_message,
                "validation_notes": self.validation_notes,
            },
        }
        return result

    def _trace_to_dict(self, trace: AgentExecutionTrace) -> Dict[str, Any]:
        """Convert AgentExecutionTrace to dict."""
        return {
            "agent_id": trace.agent_id,
            "agent_type": trace.agent_type,
            "input_query": trace.input_query[:1000] if trace.input_query else "",
            "output_content": trace.output_content[:2000] if trace.output_content else "",
            "success": trace.success,
            "error": trace.error,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "arguments": tc.arguments,
                    "result": self._truncate_result(tc.result),
                    "success": tc.success,
                    "duration_ms": tc.duration_ms,
                }
                for tc in trace.tool_calls
            ],
            "metadata": trace.metadata,
            "child_agents": [self._trace_to_dict(c) for c in trace.child_agents],
        }

    def _truncate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Truncate large result values."""
        truncated = {}
        for k, v in result.items():
            if isinstance(v, str) and len(v) > 1000:
                truncated[k] = v[:1000] + "... [truncated]"
            elif isinstance(v, dict):
                truncated[k] = self._truncate_result(v)
            else:
                truncated[k] = v
        return truncated


class TraceCollector:
    """Collects detailed traces for test cases."""

    def __init__(self, output_dir: str = "test_traces"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.traces: List[DetailedTestTrace] = []
        self.api_base_url = os.getenv("MAGONE_API_URL", "http://localhost:8000/api/v1")
        self.token: Optional[str] = None
        self._client = httpx.Client(timeout=60.0)

    def set_token(self, token: str):
        """Set auth token for API calls."""
        self.token = token

    def _headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def create_trace(
        self,
        test_id: str,
        test_name: str,
        category: str,
        input_query: str,
        expected_agents: List[str],
    ) -> DetailedTestTrace:
        """Create a new trace for a test case."""
        trace = DetailedTestTrace(
            test_id=test_id,
            test_name=test_name,
            category=category,
            timestamp=datetime.now().isoformat(),
            input_query=input_query,
            expected_agents=expected_agents,
        )
        self.traces.append(trace)
        return trace

    def populate_from_response(
        self,
        trace: DetailedTestTrace,
        response: Dict[str, Any],
    ):
        """Populate trace from API response."""
        trace.api_response = response
        trace.workflow_id = response.get("workflow_id")
        trace.total_elapsed_ms = response.get("elapsed_ms", 0)
        trace.success = response.get("success", False)
        trace.final_output = response.get("content", "")

        if not trace.success:
            trace.error_message = response.get("error")

        # Extract agents from metadata
        metadata = response.get("metadata", {})
        trace.actual_agents = self._extract_agents_from_metadata(metadata)

        # Build agent chain from metadata
        trace.agent_chain = self._build_agent_chain(metadata)

        # Count tool calls
        trace.total_tool_calls = self._count_tool_calls(metadata)

    def _extract_agents_from_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract agent IDs from metadata."""
        agents = []

        # Check tool_calls for agent: tools
        tool_calls = metadata.get("tool_calls", [])
        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            if tool_name.startswith("agent:"):
                agents.append(tool_name.replace("agent:", ""))

        # Check agent_chain
        agent_chain = metadata.get("agent_chain", [])
        agents.extend(agent_chain)

        # Check agent_results (orchestrator mode)
        agent_results = metadata.get("agent_results", [])
        for ar in agent_results:
            if isinstance(ar, dict):
                agent_name = ar.get("agent", "")
                if agent_name.startswith("agent:"):
                    agents.append(agent_name.replace("agent:", ""))

        # Check delegations
        delegations = metadata.get("delegations", [])
        for d in delegations:
            if isinstance(d, dict) and "agent_id" in d:
                agents.append(d["agent_id"])
            elif isinstance(d, str):
                agents.append(d)

        return list(dict.fromkeys(agents))  # Remove duplicates, preserve order

    def _build_agent_chain(self, metadata: Dict[str, Any]) -> List[AgentExecutionTrace]:
        """Build agent execution chain from metadata."""
        chain = []

        # From agent_results (orchestrator)
        agent_results = metadata.get("agent_results", [])
        for ar in agent_results:
            if isinstance(ar, dict):
                result = ar.get("result", {})
                agent_name = ar.get("agent", "unknown")
                agent_id = agent_name.replace("agent:", "") if agent_name.startswith("agent:") else agent_name

                trace = AgentExecutionTrace(
                    agent_id=agent_id,
                    input_query=ar.get("query", ""),
                    output_content=result.get("content", ""),
                    success=result.get("success", False),
                    error=result.get("error"),
                    metadata=result.get("metadata", {}),
                )
                chain.append(trace)

        # From tool_calls
        tool_calls = metadata.get("tool_calls", [])
        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            if tool_name.startswith("agent:"):
                agent_id = tool_name.replace("agent:", "")
                result = tc.get("result", {})

                trace = AgentExecutionTrace(
                    agent_id=agent_id,
                    input_query=str(tc.get("args", {})),
                    output_content=result.get("content", "") if isinstance(result, dict) else str(result),
                    success=result.get("success", False) if isinstance(result, dict) else True,
                    error=result.get("error") if isinstance(result, dict) else None,
                )

                # Check for nested tool calls in this agent's result
                if isinstance(result, dict) and "metadata" in result:
                    nested_metadata = result["metadata"]
                    nested_tool_calls = nested_metadata.get("tool_calls", [])
                    for ntc in nested_tool_calls:
                        trace.tool_calls.append(ToolCallTrace(
                            tool_name=ntc.get("tool", ""),
                            arguments=ntc.get("args", {}),
                            result=ntc.get("result", {}),
                            success=ntc.get("result", {}).get("success", True) if isinstance(ntc.get("result"), dict) else True,
                        ))

                chain.append(trace)
            else:
                # Regular tool call, not an agent
                # Find if there's an existing trace to add this to
                if chain:
                    chain[-1].tool_calls.append(ToolCallTrace(
                        tool_name=tool_name,
                        arguments=tc.get("args", {}),
                        result=tc.get("result", {}),
                        success=tc.get("result", {}).get("success", True) if isinstance(tc.get("result"), dict) else True,
                    ))

        return chain

    def _count_tool_calls(self, metadata: Dict[str, Any]) -> int:
        """Count total tool calls from metadata."""
        count = len(metadata.get("tool_calls", []))

        # Count nested tool calls in agent results
        for ar in metadata.get("agent_results", []):
            if isinstance(ar, dict):
                result = ar.get("result", {})
                if isinstance(result, dict):
                    nested_metadata = result.get("metadata", {})
                    count += len(nested_metadata.get("tool_calls", []))

        return count

    def fetch_workflow_details(self, trace: DetailedTestTrace):
        """Fetch workflow details from Temporal via API."""
        if not trace.workflow_id:
            return

        try:
            # Get workflow status
            response = self._client.get(
                f"{self.api_base_url}/workflow/status/{trace.workflow_id}",
                headers=self._headers(),
            )

            if response.status_code == 200:
                status_data = response.json()
                trace.workflow_status = status_data.get("status")
        except Exception as e:
            trace.workflow_status = f"Error fetching: {e}"

    def save_trace(self, trace: DetailedTestTrace):
        """Save individual trace to JSON file."""
        filename = f"{trace.test_id}_{trace.timestamp.replace(':', '-').replace('.', '-')}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(trace.to_dict(), f, indent=2, default=str)

        return filepath

    def save_all_traces(self):
        """Save all traces and summary."""
        saved_files = []

        for trace in self.traces:
            filepath = self.save_trace(trace)
            saved_files.append(str(filepath))

        return saved_files

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all traces."""
        total = len(self.traces)
        passed = sum(1 for t in self.traces if t.status == "pass")
        failed = sum(1 for t in self.traces if t.status == "fail")
        errors = sum(1 for t in self.traces if t.status == "error")
        skipped = sum(1 for t in self.traces if t.status == "skip")
        partial = sum(1 for t in self.traces if t.status == "partial")

        # Group by category
        by_category = {}
        for t in self.traces:
            if t.category not in by_category:
                by_category[t.category] = {"total": 0, "passed": 0, "failed": 0}
            by_category[t.category]["total"] += 1
            if t.status == "pass":
                by_category[t.category]["passed"] += 1
            elif t.status in ("fail", "error"):
                by_category[t.category]["failed"] += 1

        # Calculate averages
        executed = [t for t in self.traces if t.status != "skip"]
        avg_elapsed = sum(t.total_elapsed_ms for t in executed) / len(executed) if executed else 0
        avg_tool_calls = sum(t.total_tool_calls for t in executed) / len(executed) if executed else 0

        summary = {
            "generated_at": datetime.now().isoformat(),
            "totals": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "partial": partial,
                "pass_rate": (passed / (total - skipped) * 100) if (total - skipped) > 0 else 0,
            },
            "by_category": by_category,
            "performance": {
                "avg_elapsed_ms": round(avg_elapsed, 2),
                "avg_tool_calls": round(avg_tool_calls, 2),
            },
            "test_results": [
                {
                    "test_id": t.test_id,
                    "category": t.category,
                    "status": t.status,
                    "success": t.success,
                    "elapsed_ms": t.total_elapsed_ms,
                    "agents_used": t.actual_agents,
                    "tool_calls": t.total_tool_calls,
                    "error": t.error_message,
                }
                for t in self.traces
            ],
        }

        return summary

    def save_summary(self) -> str:
        """Save summary to JSON file."""
        summary = self.generate_summary()
        filepath = self.output_dir / "test_summary.json"

        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        return str(filepath)

    def generate_markdown_report(self) -> str:
        """Generate markdown summary report."""
        summary = self.generate_summary()

        lines = [
            "# MagoneAI Orchestrator Detailed Test Report",
            "",
            f"**Generated:** {summary['generated_at']}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Tests | {summary['totals']['total']} |",
            f"| Passed | {summary['totals']['passed']} |",
            f"| Failed | {summary['totals']['failed']} |",
            f"| Errors | {summary['totals']['errors']} |",
            f"| Partial | {summary['totals']['partial']} |",
            f"| Skipped | {summary['totals']['skipped']} |",
            f"| Pass Rate | {summary['totals']['pass_rate']:.1f}% |",
            f"| Avg Response Time | {summary['performance']['avg_elapsed_ms']:.0f}ms |",
            f"| Avg Tool Calls | {summary['performance']['avg_tool_calls']:.1f} |",
            "",
            "---",
            "",
            "## Results by Category",
            "",
        ]

        for cat, stats in summary["by_category"].items():
            pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            lines.append(f"### {cat}")
            lines.append("")
            lines.append(f"- **Total:** {stats['total']}")
            lines.append(f"- **Passed:** {stats['passed']}")
            lines.append(f"- **Failed:** {stats['failed']}")
            lines.append(f"- **Pass Rate:** {pass_rate:.1f}%")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## Detailed Test Results",
            "",
            "| Test ID | Status | Time | Agents Used | Tool Calls | Error |",
            "|---------|--------|------|-------------|------------|-------|",
        ])

        status_emoji = {
            "pass": "✅",
            "fail": "❌",
            "partial": "⚠️",
            "skip": "⏭️",
            "error": "💥",
        }

        for t in summary["test_results"]:
            emoji = status_emoji.get(t["status"], "❓")
            agents = ", ".join(t["agents_used"]) if t["agents_used"] else "-"
            error = t["error"][:50] + "..." if t["error"] and len(t["error"]) > 50 else (t["error"] or "-")
            lines.append(
                f"| {t['test_id']} | {emoji} {t['status'].upper()} | {t['elapsed_ms']:.0f}ms | {agents} | {t['tool_calls']} | {error} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Individual Test Files",
            "",
            "Detailed JSON traces for each test case are available in the `test_traces/` directory.",
            "",
        ])

        return "\n".join(lines)

    def save_markdown_report(self, filename: str = "orchestrator_test_report.md") -> str:
        """Save markdown report."""
        report = self.generate_markdown_report()
        filepath = Path(filename)

        with open(filepath, "w") as f:
            f.write(report)

        return str(filepath)

    def close(self):
        """Close HTTP client."""
        self._client.close()


# Global collector instance
_collector: Optional[TraceCollector] = None


def get_collector() -> TraceCollector:
    """Get or create global trace collector."""
    global _collector
    if _collector is None:
        _collector = TraceCollector()
    return _collector


def reset_collector():
    """Reset the global collector."""
    global _collector
    if _collector:
        _collector.close()
    _collector = TraceCollector()
    return _collector
