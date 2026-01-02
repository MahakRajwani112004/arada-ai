"""Contact Resolution Tests (Phase 3 Validation + RW1-RW3).

These tests validate the knowledge base contact resolution capabilities:
- Name → Email resolution (Yash → yash.k@magureinc.com)
- Role → Person resolution (CTO → Pranav Agarwal)
- Company → Contact resolution (Acme Corp → Yash Karande)

This is a prerequisite for all context-aware workflows.

Test Recipients (from KB):
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


class TestContactResolution:
    """Contact resolution validation tests.

    These tests must pass before running RW4-RW12 scenarios.
    """

    CATEGORY = "Contact Resolution (Phase 3 + RW1-RW3)"

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
    # Phase 3: Name Resolution Tests
    # =========================================================================
    def test_p3_1_yash_email_lookup(self):
        """P3.1: What is Yash's email?

        Should resolve Yash Karande → yash.k@magureinc.com from team directory.
        """
        query = "What is Yash's email?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="P3.1",
            test_name="test_p3_1_yash_email_lookup",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["yash.k@magureinc.com"],  # Must include exact email
        )

        assert result.status in ("pass", "partial"), f"P3.1 failed: {result.error_message}"

    def test_p3_2_pranav_email_lookup(self):
        """P3.2: What is Pranav's email?

        Should resolve Pranav Agarwal → pranav.ag@magureinc.com from team directory.
        """
        query = "What is Pranav's email?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="P3.2",
            test_name="test_p3_2_pranav_email_lookup",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["pranav.ag@magureinc.com"],  # Must include exact email
        )

        assert result.status in ("pass", "partial"), f"P3.2 failed: {result.error_message}"

    def test_p3_3_cto_lookup(self):
        """P3.3: Who is the CTO?

        Should find Pranav Agarwal as CTO from team directory.
        """
        query = "Who is the CTO?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="P3.3",
            test_name="test_p3_3_cto_lookup",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["pranav"],  # Should mention Pranav
        )

        assert result.status in ("pass", "partial"), f"P3.3 failed: {result.error_message}"

    def test_p3_4_acme_contact_lookup(self):
        """P3.4: Who manages Acme Corp?

        Should find Yash Karande as Acme Corp account manager.
        """
        query = "Who manages Acme Corp?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="P3.4",
            test_name="test_p3_4_acme_contact_lookup",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["yash"],  # Should mention Yash
        )

        assert result.status in ("pass", "partial"), f"P3.4 failed: {result.error_message}"

    def test_p3_5_globex_contact_lookup(self):
        """P3.5: Who is the contact for Globex?

        Should find Pranav Agarwal as Globex account manager.
        """
        query = "Who is the contact for Globex?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="P3.5",
            test_name="test_p3_5_globex_contact_lookup",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["pranav"],  # Should mention Pranav
        )

        assert result.status in ("pass", "partial"), f"P3.5 failed: {result.error_message}"

    # =========================================================================
    # RW1-RW3: Basic Contact Resolution Workflows
    # =========================================================================
    def test_rw1_email_lookup_basic(self):
        """RW1: What is Yash's email?

        Basic contact lookup - foundation for all email workflows.
        """
        query = "What is Yash's email?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW1",
            test_name="test_rw1_email_lookup_basic",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["yash.k@magureinc.com"],
        )

        assert result.status in ("pass", "partial"), f"RW1 failed: {result.error_message}"

    def test_rw2_role_and_email_lookup(self):
        """RW2: Who is the CTO and what's their email?

        Combined role + email lookup.
        """
        query = "Who is the CTO and what's their email?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW2",
            test_name="test_rw2_role_and_email_lookup",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["pranav", "pranav.ag@magureinc.com"],  # Should have name and email
        )

        assert result.status in ("pass", "partial"), f"RW2 failed: {result.error_message}"

    def test_rw3_company_contact_lookup(self):
        """RW3: Find contact for Acme Corp.

        Company → Internal contact resolution.
        """
        query = "Find the contact for Acme Corp"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="RW3",
            test_name="test_rw3_company_contact_lookup",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["yash"],  # Should mention Yash as account manager
        )

        assert result.status in ("pass", "partial"), f"RW3 failed: {result.error_message}"

    # =========================================================================
    # Additional Contact Resolution Scenarios
    # =========================================================================
    def test_sde_lookup(self):
        """Lookup SDE role.

        Should find Yash Karande as SDE.
        """
        query = "Who is our SDE?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="CR1",
            test_name="test_sde_lookup",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["yash"],
        )

        assert result.status in ("pass", "partial"), f"CR1 failed: {result.error_message}"

    def test_team_directory_list(self):
        """List team members.

        Should list both Yash and Pranav.
        """
        query = "List all team members in our directory"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="CR2",
            test_name="test_team_directory_list",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["yash", "pranav"],  # Should mention both
        )

        assert result.status in ("pass", "partial"), f"CR2 failed: {result.error_message}"

    def test_account_manager_by_company(self):
        """Find account manager for specific company.

        Should resolve company → account manager.
        """
        query = "Who is the account manager for Acme Corporation?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="CR3",
            test_name="test_account_manager_by_company",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["yash", "yash.k@magureinc.com"],
        )

        assert result.status in ("pass", "partial"), f"CR3 failed: {result.error_message}"
