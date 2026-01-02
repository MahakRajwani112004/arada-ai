"""Multi-Domain Tests (DE, DC, EC, DEC, DECW).

Multi-domain test scenarios that combine:
- Documents (research-agent, file-agent)
- Email (email-agent)
- Calendar (calendar-agent)
- Writer (writer-agent)

These tests validate cross-domain orchestration capabilities.

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


class TestMultiDomainScenarios:
    """Multi-domain test scenarios.

    Status: ACTIVE - All MCP servers connected, agents created
    """

    CATEGORY = "Multi-Domain Scenarios"

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
        """Record test result and return it."""
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
    # DE: Documents + Email
    # =========================================================================
    def test_de1_find_and_email_policy(self):
        """DE1: Find our return policy and email it to Yash.

        Uses KB to find policy, resolves Yash → yash.k@magureinc.com, sends email.
        """
        query = "Find our return policy and email it to Yash"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DE1",
            test_name="test_de1_find_and_email_policy",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["return", "policy"],
        )

        assert result.status in ("pass", "partial"), f"DE1 failed: {result.error_message}"

    def test_de5_find_faq_and_reply(self):
        """DE5: Find FAQ answer and reply to support email.

        Should search KB for FAQ and compose reply.
        """
        query = "Find our FAQ about password resets and use it to reply to the support email"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DE5",
            test_name="test_de5_find_faq_and_reply",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["faq"],
        )

        assert result.status in ("pass", "partial"), f"DE5 failed: {result.error_message}"

    # =========================================================================
    # DC: Documents + Calendar
    # =========================================================================
    def test_dc1_docs_for_meeting(self):
        """DC1: What docs should I review before my Acme meeting?

        Should find Acme meeting and relevant docs.
        """
        query = "What docs should I review before my Acme meeting?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DC1",
            test_name="test_dc1_docs_for_meeting",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["acme"],
        )

        assert result.status in ("pass", "partial"), f"DC1 failed: {result.error_message}"

    def test_dc4_prepare_briefing(self):
        """DC4: Prepare briefing doc for tomorrow's client meeting.

        Should identify meeting and create briefing.
        """
        query = "Prepare a briefing document for tomorrow's client meeting"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DC4",
            test_name="test_dc4_prepare_briefing",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["briefing"],
        )

        assert result.status in ("pass", "partial"), f"DC4 failed: {result.error_message}"

    # =========================================================================
    # EC: Email + Calendar
    # =========================================================================
    def test_ec1_meeting_requests(self):
        """EC1: Check for meeting requests in my email.

        Should search emails for meeting requests.
        """
        query = "Check for meeting requests in my email"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="EC1",
            test_name="test_ec1_meeting_requests",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["meeting"],
        )

        assert result.status in ("pass", "partial"), f"EC1 failed: {result.error_message}"

    def test_ec6_reschedule_notify(self):
        """EC6: Reschedule meeting and notify attendees.

        Should update calendar and send notification emails.
        """
        query = "Reschedule the Project Alpha Review to next Friday and notify the attendees"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="EC6",
            test_name="test_ec6_reschedule_notify",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["project", "alpha"],
        )

        assert result.status in ("pass", "partial"), f"EC6 failed: {result.error_message}"

    # =========================================================================
    # DEC: Documents + Email + Calendar
    # =========================================================================
    def test_dec1_full_meeting_prep(self):
        """DEC1: Prepare for Acme meeting: find docs, check emails, confirm time.

        Full meeting preparation across all domains.
        """
        query = "Prepare me for my Acme Corp meeting: find relevant docs, check recent emails, and confirm the meeting time"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DEC1",
            test_name="test_dec1_full_meeting_prep",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["acme"],
        )

        assert result.status in ("pass", "partial"), f"DEC1 failed: {result.error_message}"

    # =========================================================================
    # DECW: Full Stack with Writer
    # =========================================================================
    def test_decw1_complete_meeting_prep(self):
        """DECW1: Prepare fully for client meeting: docs, emails, agenda, send prep to team.

        Complete meeting preparation with all agents.
        """
        query = "Prepare fully for my next client meeting: gather relevant docs and emails, create an agenda, and send the prep summary to Pranav"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DECW1",
            test_name="test_decw1_complete_meeting_prep",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["meeting"],
        )

        assert result.status in ("pass", "partial"), f"DECW1 failed: {result.error_message}"

    def test_decw5_weekly_update(self):
        """DECW5: Create weekly team update: calendar events, doc changes, email highlights.

        Comprehensive weekly digest.
        """
        query = "Create a weekly team update summarizing my calendar events, recent document changes, and important emails, then send it to Yash"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DECW5",
            test_name="test_decw5_weekly_update",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["weekly", "update"],
        )

        assert result.status in ("pass", "partial"), f"DECW5 failed: {result.error_message}"
