"""Email Domain Tests (E1-E14).

Tests for email-related scenarios using:
- email-agent (ToolAgent) for Outlook email operations via MCP

MCP Server: srv_0de807a6136f (outlook-email)
Tools: send_email, list_emails, search_emails, get_email

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


class TestEmailScenarios:
    """Email-only test scenarios (E1-E14).

    Status: ACTIVE - OAuth resolved, MCP servers connected
    """

    CATEGORY = "Email Scenarios (E1-E14)"

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
    # E1: Check unread emails
    # =========================================================================
    def test_e1_check_unread_emails(self):
        """E1: Check my inbox for unread emails.

        Accept any agent that lists unread emails.
        """
        query = "Check my inbox for unread emails"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E1",
            test_name="test_e1_check_unread_emails",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["email", "inbox"],  # Should mention email context
        )

        assert result.status in ("pass", "partial"), f"E1 failed: {result.error_message}"

    # =========================================================================
    # E2: Search by sender
    # =========================================================================
    def test_e2_emails_from_acme(self):
        """E2: Show me emails from Acme Corp.

        Accept any agent that searches for Acme emails.
        """
        query = "Show me emails from Acme Corp"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E2",
            test_name="test_e2_emails_from_acme",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["acme"],  # Should mention Acme
        )

        assert result.status in ("pass", "partial"), f"E2 failed: {result.error_message}"

    # =========================================================================
    # E3: Find urgent emails
    # =========================================================================
    def test_e3_find_urgent_emails(self):
        """E3: Find urgent emails.

        Accept any agent that identifies urgent emails.
        """
        query = "Find urgent emails"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E3",
            test_name="test_e3_find_urgent_emails",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["email"],  # Should be email-related
        )

        assert result.status in ("pass", "partial"), f"E3 failed: {result.error_message}"

    # =========================================================================
    # E4: Read specific email
    # =========================================================================
    def test_e4_read_manager_email(self):
        """E4: Read the email from my manager.

        Accept any agent that reads a specific email.
        """
        query = "Read the email from my manager"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E4",
            test_name="test_e4_read_manager_email",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=[],  # Flexible - depends on inbox content
        )

        assert result.status in ("pass", "partial"), f"E4 failed: {result.error_message}"

    # =========================================================================
    # E5: Send email (using test recipient)
    # =========================================================================
    def test_e5_send_email(self):
        """E5: Send email to Yash with a test message.

        Uses contact resolution from KB to resolve Yash → yash.k@magureinc.com
        """
        query = "Send an email to Yash saying 'Test message from orchestrator integration tests'"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E5",
            test_name="test_e5_send_email",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["send", "email"],  # Should confirm sending
        )

        assert result.status in ("pass", "partial"), f"E5 failed: {result.error_message}"

    # =========================================================================
    # E6: Reply with KB answer
    # =========================================================================
    def test_e6_reply_password_reset(self):
        """E6: Reply to the password reset request.

        Should find FAQ info and compose reply.
        """
        query = "Reply to the password reset request with information from our FAQ"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E6",
            test_name="test_e6_reply_password_reset",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=[],  # Flexible
        )

        assert result.status in ("pass", "partial"), f"E6 failed: {result.error_message}"

    # =========================================================================
    # E7: Forward email
    # =========================================================================
    def test_e7_forward_to_legal(self):
        """E7: Forward the contract email to legal team.

        Should find contract email and forward.
        """
        query = "Forward the contract email to the legal team"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E7",
            test_name="test_e7_forward_to_legal",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=[],  # Flexible
        )

        assert result.status in ("pass", "partial"), f"E7 failed: {result.error_message}"

    # =========================================================================
    # E8: Mark as read
    # =========================================================================
    def test_e8_mark_newsletters_read(self):
        """E8: Mark all newsletters as read.

        Should identify and mark newsletters.
        """
        query = "Mark all newsletters as read"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E8",
            test_name="test_e8_mark_newsletters_read",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=[],  # Flexible
        )

        assert result.status in ("pass", "partial"), f"E8 failed: {result.error_message}"

    # =========================================================================
    # E9: Search email content
    # =========================================================================
    def test_e9_search_proposal(self):
        """E9: Search for emails containing 'proposal'.

        Should search email content.
        """
        query = "Search for emails containing 'proposal'"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E9",
            test_name="test_e9_search_proposal",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["proposal"],  # Should mention proposal
        )

        assert result.status in ("pass", "partial"), f"E9 failed: {result.error_message}"

    # =========================================================================
    # E10: Support requests today
    # =========================================================================
    def test_e10_support_requests_today(self):
        """E10: What support requests came in today?

        Should filter by date and label.
        """
        query = "What support requests came in today?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E10",
            test_name="test_e10_support_requests_today",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=[],  # Flexible - depends on actual inbox
        )

        assert result.status in ("pass", "partial"), f"E10 failed: {result.error_message}"

    # =========================================================================
    # E11: Draft response to frustrated customer
    # =========================================================================
    def test_e11_draft_response_frustrated(self):
        """E11: Draft a response to the frustrated customer.

        Should compose empathetic response.
        """
        query = "Draft a response to the frustrated customer email"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E11",
            test_name="test_e11_draft_response_frustrated",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=[],  # Flexible
        )

        assert result.status in ("pass", "partial"), f"E11 failed: {result.error_message}"

    # =========================================================================
    # E12: Summarize unread
    # =========================================================================
    def test_e12_summarize_unread(self):
        """E12: Summarize all unread emails.

        Should list and summarize unread emails.
        """
        query = "Summarize all unread emails"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E12",
            test_name="test_e12_summarize_unread",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["email"],  # Should be email-related
        )

        assert result.status in ("pass", "partial"), f"E12 failed: {result.error_message}"

    # =========================================================================
    # E13: Find with attachments
    # =========================================================================
    def test_e13_find_with_attachments(self):
        """E13: Find emails with attachments.

        Should filter by attachment presence.
        """
        query = "Find emails with attachments"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E13",
            test_name="test_e13_find_with_attachments",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["attachment"],  # Should mention attachments
        )

        assert result.status in ("pass", "partial"), f"E13 failed: {result.error_message}"

    # =========================================================================
    # E14: Archive old emails
    # =========================================================================
    def test_e14_archive_old(self):
        """E14: Archive all emails older than 30 days.

        Should identify and archive old emails.
        """
        query = "Archive all emails older than 30 days"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="E14",
            test_name="test_e14_archive_old",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=[],  # Flexible
        )

        assert result.status in ("pass", "partial"), f"E14 failed: {result.error_message}"
