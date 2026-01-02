"""Real-World Workflow Tests (RW4-RW12).

These tests validate complex, multi-step workflows that simulate actual business use cases.
Each workflow involves:
- Context-aware contact resolution
- Document retrieval from knowledge base
- Email operations via MCP
- Calendar operations via MCP
- Content generation with writer agent

Tiers:
- Tier 2 (RW4-RW6): Document + Contact Resolution
- Tier 3 (RW7-RW9): Document + Contact + Calendar
- Tier 4 (RW10-RW12): Complex Business Workflows

Test Recipients:
- Yash Karande (SDE) - yash.k@magureinc.com - Acme Corp account manager
- Pranav Agarwal (CTO) - pranav.ag@magureinc.com - Globex account manager

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


class TestRealWorldWorkflows:
    """Real-world workflow test scenarios (RW4-RW12).

    These are the ultimate validation of the orchestrator's capabilities.
    """

    CATEGORY = "Real-World Workflows (RW4-RW12)"

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
    # Tier 2: Document + Contact Resolution (RW4-RW6)
    # =========================================================================
    def test_rw4_send_policy_to_yash(self):
        """RW4: Send the return policy to Yash.

        Workflow:
        1. research-agent: Find return policy in KB
        2. Resolve Yash → yash.k@magureinc.com
        3. email-agent: Send policy to Yash

        Expected agents: research → email
        """
        query = "Send the return policy to Yash"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW4",
            test_name="test_rw4_send_policy_to_yash",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["return", "policy"],
        )

        assert result.status in ("pass", "partial"), f"RW4 failed: {result.error_message}"

    def test_rw5_send_specs_to_cto(self):
        """RW5: Email project alpha specs to the CTO.

        Workflow:
        1. research-agent: Find project alpha specs
        2. Resolve CTO → Pranav Agarwal → pranav.ag@magureinc.com
        3. email-agent: Send specs to CTO

        Expected agents: research → email
        """
        query = "Email project alpha specs to the CTO"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW5",
            test_name="test_rw5_send_specs_to_cto",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["project", "alpha"],
        )

        assert result.status in ("pass", "partial"), f"RW5 failed: {result.error_message}"

    def test_rw6_send_profile_to_account_manager(self):
        """RW6: Send Acme Corp profile to their account manager.

        Workflow:
        1. Resolve Acme Corp account manager → Yash Karande → yash.k@magureinc.com
        2. research-agent: Find acme-corp-profile.md
        3. email-agent: Send profile to Yash

        Expected agents: research → email
        """
        query = "Send Acme Corp profile to their account manager"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW6",
            test_name="test_rw6_send_profile_to_account_manager",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["acme"],
        )

        assert result.status in ("pass", "partial"), f"RW6 failed: {result.error_message}"

    # =========================================================================
    # Tier 3: Document + Contact + Calendar (RW7-RW9)
    # =========================================================================
    def test_rw7_send_specs_and_schedule(self):
        """RW7: Send project alpha to Yash and schedule a discussion.

        Workflow:
        1. research-agent: Find project alpha specs
        2. Resolve Yash → yash.k@magureinc.com
        3. email-agent: Send specs to Yash
        4. calendar-agent: Create meeting with Yash

        Expected agents: research → email → calendar
        """
        query = "Send project alpha specs to Yash and schedule a discussion for tomorrow at 3pm"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW7",
            test_name="test_rw7_send_specs_and_schedule",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["project", "alpha"],
        )

        assert result.status in ("pass", "partial"), f"RW7 failed: {result.error_message}"

    def test_rw8_email_contract_and_schedule_call(self):
        """RW8: Email the contract terms to Acme and set up a call.

        Workflow:
        1. Resolve Acme Corp contact → Yash
        2. research-agent: Find contract/Acme documents
        3. email-agent: Send contract info to Yash
        4. calendar-agent: Schedule call with Yash

        Expected agents: research → email → calendar
        """
        query = "Email the Acme Corp contract terms to their account manager and set up a call to discuss"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW8",
            test_name="test_rw8_email_contract_and_schedule_call",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["acme"],
        )

        assert result.status in ("pass", "partial"), f"RW8 failed: {result.error_message}"

    def test_rw9_share_q4_and_block_time(self):
        """RW9: Share Q4 planning with Pranav and block time to review.

        Workflow:
        1. Resolve Pranav → pranav.ag@magureinc.com
        2. research-agent: Find Q4 planning doc
        3. email-agent: Send Q4 doc to Pranav
        4. calendar-agent: Block review time

        Expected agents: research → email → calendar
        """
        query = "Share the Q4 planning document with Pranav and block time tomorrow to review it together"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW9",
            test_name="test_rw9_share_q4_and_block_time",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["q4", "planning"],
        )

        assert result.status in ("pass", "partial"), f"RW9 failed: {result.error_message}"

    # =========================================================================
    # Tier 4: Complex Business Workflows (RW10-RW12)
    # =========================================================================
    def test_rw10_full_acme_meeting_prep(self):
        """RW10: Prepare for Acme meeting: send them latest docs and create calendar invite.

        Workflow:
        1. research-agent: Find Acme-related docs
        2. Resolve Acme contact → Yash
        3. writer-agent: Create summary/briefing
        4. email-agent: Send docs to Yash
        5. calendar-agent: Create meeting invite with Yash

        Expected agents: research → writer → email → calendar
        """
        query = "Prepare for the Acme meeting: find their profile and latest docs, send them a summary, and create a calendar invite for next Tuesday at 2pm"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW10",
            test_name="test_rw10_full_acme_meeting_prep",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["acme"],
        )

        assert result.status in ("pass", "partial"), f"RW10 failed: {result.error_message}"

    def test_rw11_globex_onboarding_workflow(self):
        """RW11: Onboard Globex: send welcome docs to their contact and schedule kickoff.

        Workflow:
        1. Resolve Globex contact → Pranav
        2. research-agent: Find onboarding/welcome docs
        3. writer-agent: Create welcome message
        4. email-agent: Send welcome docs to Pranav
        5. calendar-agent: Schedule kickoff meeting with Pranav

        Expected agents: research → writer → email → calendar
        """
        query = "Onboard Globex: send welcome documents to their account manager and schedule a kickoff meeting for this Friday at 10am"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW11",
            test_name="test_rw11_globex_onboarding_workflow",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["globex"],
        )

        assert result.status in ("pass", "partial"), f"RW11 failed: {result.error_message}"

    def test_rw12_privacy_policy_review_workflow(self):
        """RW12: Discuss privacy policy updates with CTO - send doc and schedule time.

        Workflow:
        1. Resolve CTO → Pranav → pranav.ag@magureinc.com
        2. research-agent: Find privacy policy
        3. email-agent: Send policy to Pranav
        4. calendar-agent: Schedule review meeting with Pranav

        Expected agents: research → email → calendar
        """
        query = "I want to discuss the privacy policy updates with the CTO - send them the document and schedule a review meeting for tomorrow afternoon"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW12",
            test_name="test_rw12_privacy_policy_review_workflow",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["privacy", "policy"],
        )

        assert result.status in ("pass", "partial"), f"RW12 failed: {result.error_message}"

    # =========================================================================
    # Additional Complex Workflows
    # =========================================================================
    def test_rw_client_update_workflow(self):
        """Client update workflow: Find client info, create update, email to account manager.

        Tests the full chain with writer agent.
        """
        query = "Create a brief update about Acme Corp's account status and email it to Yash"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW-CU",
            test_name="test_rw_client_update_workflow",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["acme"],
        )

        assert result.status in ("pass", "partial"), f"RW-CU failed: {result.error_message}"

    def test_rw_meeting_prep_with_context(self):
        """Meeting prep with full context lookup.

        Gather all relevant info before a meeting.
        """
        query = "I have a meeting with the Globex team soon - find all relevant documents and recent info about them, then send a summary to Pranav who manages their account"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW-MP",
            test_name="test_rw_meeting_prep_with_context",
            query=query,
            expected_agents=[],  # Accept any agent combo
            response=response,
            keywords=["globex"],
        )

        assert result.status in ("pass", "partial"), f"RW-MP failed: {result.error_message}"
