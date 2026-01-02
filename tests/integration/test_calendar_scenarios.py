"""Calendar Domain Tests (C1-C12).

Tests for calendar-related scenarios using:
- calendar-agent (ToolAgent) for Outlook calendar operations via MCP

MCP Server: srv_3110e8c1ce5b (outlook-calendar)
Tools: list_events, create_event, update_event, delete_event

Each test generates:
1. A detailed JSON trace file with all execution details
2. Contributes to the summary report
"""

import pytest

from .conftest import (
    OrchestratorAPIClient,
    TestConfig,
    TestReport,
    TestResult,
    extract_agents_from_response,
    record_detailed_trace,
    validate_response_quality,
)
from .trace_collector import TraceCollector


class TestCalendarScenarios:
    """Calendar-only test scenarios (C1-C12).

    Status: ACTIVE - OAuth resolved, MCP servers connected
    """

    CATEGORY = "Calendar Scenarios (C1-C12)"

    @pytest.fixture(autouse=True)
    def setup(
        self,
        api_client: OrchestratorAPIClient,
        test_config: TestConfig,
        test_report: TestReport,
        trace_collector: TraceCollector,
    ):
        """Setup for each test."""
        self.client = api_client
        self.config = test_config
        self.report = test_report
        self.collector = trace_collector

    def _record_result(
        self,
        test_id: str,
        test_name: str,
        query: str,
        expected_agents: list,
        response: dict,
        keywords: list = None,
    ) -> TestResult:
        """Record test result and return it.

        Also creates a detailed JSON trace for the test case.
        """
        actual_agents = extract_agents_from_response(response)
        is_valid, reason = validate_response_quality(response, keywords)

        # Determine status
        if not response.get("success"):
            status = "error"
        elif not is_valid:
            status = "fail"
        elif set(expected_agents) <= set(actual_agents) or not expected_agents:
            status = "pass"
        else:
            # Check if at least one expected agent was used
            if any(ea in actual_agents for ea in expected_agents):
                status = "partial"
            else:
                status = "fail"

        result = TestResult(
            test_id=test_id,
            category=self.CATEGORY,
            input_query=query,
            expected_agents=expected_agents,
            actual_agents=actual_agents,
            status=status,
            response_preview=response.get("content", "")[:200],
            elapsed_ms=response.get("elapsed_ms", 0),
            error_message=response.get("error") if not response.get("success") else (reason if not is_valid else None),
        )
        self.report.add_result(result)

        # Record detailed trace
        record_detailed_trace(
            collector=self.collector,
            test_id=test_id,
            test_name=test_name,
            category=self.CATEGORY,
            query=query,
            expected_agents=expected_agents,
            response=response,
            keywords=keywords,
        )

        return result

    # =========================================================================
    # C1: Today's meetings
    # =========================================================================
    def test_c1_meetings_today(self):
        """C1: What meetings do I have today?

        Accept any agent that lists today's events.
        """
        query = "What meetings do I have today?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C1",
            test_name="test_c1_meetings_today",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["meeting", "today"],  # Should reference meetings/today
        )

        assert result.status in ("pass", "partial"), f"C1 failed: {result.error_message}"

    # =========================================================================
    # C2: This week's schedule
    # =========================================================================
    def test_c2_schedule_this_week(self):
        """C2: What's on my schedule this week?

        Accept any agent that lists week's events.
        """
        query = "What's on my schedule this week?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C2",
            test_name="test_c2_schedule_this_week",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["schedule", "week"],  # Should reference schedule/week
        )

        assert result.status in ("pass", "partial"), f"C2 failed: {result.error_message}"

    # =========================================================================
    # C3: Next meeting with client
    # =========================================================================
    def test_c3_next_acme_meeting(self):
        """C3: When is my next meeting with Acme Corp?

        Accept any agent that finds Acme meeting.
        """
        query = "When is my next meeting with Acme Corp?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C3",
            test_name="test_c3_next_acme_meeting",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["acme"],  # Should mention Acme
        )

        assert result.status in ("pass", "partial"), f"C3 failed: {result.error_message}"

    # =========================================================================
    # C4: Find free slot
    # =========================================================================
    def test_c4_find_free_slot(self):
        """C4: Find a free 1-hour slot tomorrow.

        Accept any agent that finds availability.
        """
        query = "Find a free 1-hour slot tomorrow"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C4",
            test_name="test_c4_find_free_slot",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["free", "available"],  # Should reference availability
        )

        assert result.status in ("pass", "partial"), f"C4 failed: {result.error_message}"

    # =========================================================================
    # C5: Schedule meeting with contact resolution
    # =========================================================================
    def test_c5_schedule_meeting(self):
        """C5: Schedule a meeting with Pranav tomorrow at 2pm.

        Uses contact resolution from KB to resolve Pranav → pranav.ag@magureinc.com
        """
        query = "Schedule a meeting with Pranav tomorrow at 2pm about project review"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C5",
            test_name="test_c5_schedule_meeting",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["meeting", "pranav"],  # Should reference meeting and Pranav
        )

        assert result.status in ("pass", "partial"), f"C5 failed: {result.error_message}"

    # =========================================================================
    # C6: Move meeting
    # =========================================================================
    def test_c6_move_meeting(self):
        """C6: Move the Project Alpha Review to Thursday.

        Accept any agent that updates event.
        """
        query = "Move the Project Alpha Review to Thursday"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C6",
            test_name="test_c6_move_meeting",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["project", "alpha"],  # Should reference the meeting
        )

        assert result.status in ("pass", "partial"), f"C6 failed: {result.error_message}"

    # =========================================================================
    # C7: Cancel meeting
    # =========================================================================
    def test_c7_cancel_meeting(self):
        """C7: Cancel my 1:1 with Manager this week.

        Accept any agent that deletes event.
        """
        query = "Cancel my 1:1 with Manager this week"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C7",
            test_name="test_c7_cancel_meeting",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=[],  # Flexible
        )

        assert result.status in ("pass", "partial"), f"C7 failed: {result.error_message}"

    # =========================================================================
    # C8: Get attendees
    # =========================================================================
    def test_c8_q4_attendees(self):
        """C8: Who is attending the Q4 Planning Session?

        Accept any agent that gets event details.
        """
        query = "Who is attending the Q4 Planning Session?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C8",
            test_name="test_c8_q4_attendees",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["q4"],  # Should reference Q4
        )

        assert result.status in ("pass", "partial"), f"C8 failed: {result.error_message}"

    # =========================================================================
    # C9: Recurring meetings
    # =========================================================================
    def test_c9_recurring_meetings(self):
        """C9: What recurring meetings do I have?

        Accept any agent that filters recurring events.
        """
        query = "What recurring meetings do I have?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C9",
            test_name="test_c9_recurring_meetings",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["recurring"],  # Should reference recurring
        )

        assert result.status in ("pass", "partial"), f"C9 failed: {result.error_message}"

    # =========================================================================
    # C10: Block focus time
    # =========================================================================
    def test_c10_block_focus_time(self):
        """C10: Block 2 hours for deep work tomorrow morning.

        Accept any agent that creates focus time event.
        """
        query = "Block 2 hours for deep work tomorrow morning"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C10",
            test_name="test_c10_block_focus_time",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["block", "focus"],  # Should reference blocking/focus
        )

        assert result.status in ("pass", "partial"), f"C10 failed: {result.error_message}"

    # =========================================================================
    # C11: Team availability
    # =========================================================================
    def test_c11_team_availability(self):
        """C11: When am I free to meet with the dev team?

        Accept any agent that finds overlapping availability.
        """
        query = "When am I free to meet with the dev team?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C11",
            test_name="test_c11_team_availability",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["free", "available"],  # Should reference availability
        )

        assert result.status in ("pass", "partial"), f"C11 failed: {result.error_message}"

    # =========================================================================
    # C12: Client meetings this month
    # =========================================================================
    def test_c12_client_meetings_month(self):
        """C12: List all client meetings this month.

        Accept any agent that filters client meetings.
        """
        query = "List all client meetings this month"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="C12",
            test_name="test_c12_client_meetings_month",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["client", "meeting"],  # Should reference client meetings
        )

        assert result.status in ("pass", "partial"), f"C12 failed: {result.error_message}"
