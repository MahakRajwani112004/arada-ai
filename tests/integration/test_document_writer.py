"""Document + Writer Tests (DW1-DW10).

Tests for document retrieval combined with content creation:
- research-agent (RAGAgent) for knowledge base search
- writer-agent (LLMAgent) for content transformation/creation

These tests validate multi-agent chains where documents are retrieved
and then transformed or formatted by the writer agent.

Each test generates:
1. A detailed JSON trace file with all execution details
2. Contributes to the summary report
"""

import pytest

from .conftest import (
    OrchestratorAPIClient,
    TestReport,
    TestResult,
    extract_agents_from_response,
    record_detailed_trace,
    validate_response_quality,
)
from .trace_collector import TraceCollector


class TestDocumentWriterScenarios:
    """Document + Writer test scenarios (DW1-DW10)."""

    CATEGORY = "Document + Writer Scenarios (DW1-DW10)"

    @pytest.fixture(autouse=True)
    def setup(
        self,
        api_client: OrchestratorAPIClient,
        test_report: TestReport,
        trace_collector: TraceCollector,
    ):
        """Setup for each test."""
        self.client = api_client
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
    # DW1: Summarize in bullet points
    # =========================================================================
    def test_dw1_handbook_bullet_summary(self):
        """DW1: Summarize the employee handbook in bullet points.

        Accept any agent combination that produces handbook summary.
        """
        query = "Summarize the employee handbook in bullet points"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW1",
            test_name="test_dw1_handbook_bullet_summary",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["employee"],  # Should reference employee content
        )

        assert result.status in ("pass", "partial"), f"DW1 failed: {result.error_message}"

    # =========================================================================
    # DW2: Simplify policy
    # =========================================================================
    def test_dw2_simplify_return_policy(self):
        """DW2: Rewrite the return policy in simpler terms.

        Accept any agent combination that simplifies the policy.
        """
        query = "Rewrite the return policy in simpler terms"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW2",
            test_name="test_dw2_simplify_return_policy",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["return"],  # Should mention return policy
        )

        assert result.status in ("pass", "partial"), f"DW2 failed: {result.error_message}"

    # =========================================================================
    # DW3: Create FAQ from KB
    # =========================================================================
    def test_dw3_create_faq_from_kb(self):
        """DW3: Create FAQ from our knowledge base articles.

        Accept any agent combination that creates FAQ content.
        """
        query = "Create a FAQ document based on our return policy and privacy policy"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW3",
            test_name="test_dw3_create_faq_from_kb",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["return", "privacy"],  # Should mention both policies
        )

        assert result.status in ("pass", "partial"), f"DW3 failed: {result.error_message}"

    # =========================================================================
    # DW4: Translate to plain English
    # =========================================================================
    def test_dw4_plain_english_privacy(self):
        """DW4: Translate the privacy policy to plain English.

        Accept any agent combination that rewrites the policy.
        """
        query = "Translate the privacy policy to plain English"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW4",
            test_name="test_dw4_plain_english_privacy",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["privacy"],  # Should mention privacy
        )

        assert result.status in ("pass", "partial"), f"DW4 failed: {result.error_message}"

    # =========================================================================
    # DW5: Executive summary from multiple docs
    # =========================================================================
    def test_dw5_executive_summary_projects(self):
        """DW5: Combine all project docs into executive summary.

        Accept any agent combination that creates a summary.
        """
        query = "Create an executive summary of Project Alpha"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW5",
            test_name="test_dw5_executive_summary_projects",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["project", "alpha"],  # Should reference Project Alpha
        )

        assert result.status in ("pass", "partial"), f"DW5 failed: {result.error_message}"

    # =========================================================================
    # DW6: Extract action items
    # =========================================================================
    def test_dw6_extract_action_items(self):
        """DW6: Extract action items from Q4 planning document.

        Accept any agent combination that extracts key initiatives/actions.
        """
        query = "Extract all action items and key initiatives from the Q4 planning document"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW6",
            test_name="test_dw6_extract_action_items",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["q4"],  # Should reference Q4 content
        )

        assert result.status in ("pass", "partial"), f"DW6 failed: {result.error_message}"

    # =========================================================================
    # DW7: Create onboarding guide
    # =========================================================================
    def test_dw7_onboarding_guide(self):
        """DW7: Create onboarding guide from handbook.

        Accept any agent combination that creates an onboarding guide.
        """
        query = "Create an onboarding guide from the employee handbook"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW7",
            test_name="test_dw7_onboarding_guide",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["onboarding"],  # Should mention onboarding
        )

        assert result.status in ("pass", "partial"), f"DW7 failed: {result.error_message}"

    # =========================================================================
    # DW8: Generate report from specs
    # =========================================================================
    def test_dw8_report_from_specs(self):
        """DW8: Generate report from project specs.

        Accept any agent combination that creates a report.
        """
        query = "Generate a report from the Project Alpha specs"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW8",
            test_name="test_dw8_report_from_specs",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["project", "alpha"],  # Should mention Project Alpha
        )

        assert result.status in ("pass", "partial"), f"DW8 failed: {result.error_message}"

    # =========================================================================
    # DW9: Make user-friendly
    # =========================================================================
    def test_dw9_user_friendly_faq(self):
        """DW9: Make the FAQ more user-friendly.

        Accept any agent combination that improves the FAQ.
        """
        query = "Rewrite our FAQ document to be more user-friendly"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW9",
            test_name="test_dw9_user_friendly_faq",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["faq"],  # Should mention FAQ
        )

        assert result.status in ("pass", "partial"), f"DW9 failed: {result.error_message}"

    # =========================================================================
    # DW10: Comparison table
    # =========================================================================
    def test_dw10_client_comparison_table(self):
        """DW10: Create comparison table of client profiles.

        Accept any agent combination that creates a comparison.
        """
        query = "Create a comparison between Acme Corp and Globex client profiles"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="DW10",
            test_name="test_dw10_client_comparison_table",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["acme"],  # Should at least mention Acme
        )

        assert result.status in ("pass", "partial"), f"DW10 failed: {result.error_message}"
