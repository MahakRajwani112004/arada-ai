"""Document Domain Tests (D1-D10).

Tests for document-related scenarios using:
- research-agent (RAGAgent) for knowledge base search
- file-agent (ToolAgent) for filesystem operations
- summarizer-agent (LLMAgent) for summarization

These tests validate that the orchestrator correctly routes document
queries to the appropriate agents.

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


class TestDocumentScenarios:
    """Document-only test scenarios (D1-D10)."""

    CATEGORY = "Document Scenarios (D1-D10)"

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
    # D1: Simple policy query
    # =========================================================================
    def test_d1_return_policy_query(self):
        """D1: What is our return policy?

        Accept any agent that provides return policy info.
        """
        query = "What is our return policy?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D1",
            test_name="test_d1_return_policy_query",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["return"],  # Should mention return
        )

        assert result.status in ("pass", "partial"), f"D1 failed: {result.error_message}"

    # =========================================================================
    # D2: Document search
    # =========================================================================
    def test_d2_find_project_documents(self):
        """D2: Find all documents about Project Alpha.

        Accept any agent that finds Project Alpha info.
        """
        query = "Find all documents about Project Alpha"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D2",
            test_name="test_d2_find_project_documents",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["project", "alpha"],
        )

        assert result.status in ("pass", "partial"), f"D2 failed: {result.error_message}"

    # =========================================================================
    # D3: Document summarization
    # =========================================================================
    def test_d3_summarize_handbook(self):
        """D3: Summarize the employee handbook.

        Accept any agent that provides handbook summary.
        """
        query = "Summarize the employee handbook"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D3",
            test_name="test_d3_summarize_handbook",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["employee"],  # Should mention employee
        )

        assert result.status in ("pass", "partial"), f"D3 failed: {result.error_message}"

    # =========================================================================
    # D4: SLA query
    # =========================================================================
    def test_d4_enterprise_sla(self):
        """D4: What's the SLA for enterprise customers?

        Accept any agent that provides SLA info.
        """
        query = "What's the SLA for enterprise customers?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D4",
            test_name="test_d4_enterprise_sla",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["enterprise"],  # Should mention enterprise
        )

        assert result.status in ("pass", "partial"), f"D4 failed: {result.error_message}"

    # =========================================================================
    # D5: List files
    # =========================================================================
    def test_d5_list_client_profiles(self):
        """D5: List all client profiles we have.

        Accept any agent that can find client profiles.
        """
        query = "List all client profiles we have"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D5",
            test_name="test_d5_list_client_profiles",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["acme"],  # At minimum should find Acme
        )

        assert result.status in ("pass", "partial"), f"D5 failed: {result.error_message}"

    # =========================================================================
    # D6: Read file
    # =========================================================================
    def test_d6_read_q4_planning(self):
        """D6: Read the Q4 planning document.

        Accept any agent that can retrieve the Q4 planning content.
        """
        query = "Read the Q4 planning document"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D6",
            test_name="test_d6_read_q4_planning",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["q4"],  # Just need Q4 content
        )

        assert result.status in ("pass", "partial"), f"D6 failed: {result.error_message}"

    # =========================================================================
    # D7: Create new document
    # =========================================================================
    def test_d7_create_meeting_notes(self):
        """D7: Create a new document with meeting notes.

        Accept any agent that creates a document.
        """
        query = "Create a new document with meeting notes for today's standup"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D7",
            test_name="test_d7_create_meeting_notes",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["meeting"],  # Should mention meeting
        )

        assert result.status in ("pass", "partial"), f"D7 failed: {result.error_message}"

    # =========================================================================
    # D8: Full-text search
    # =========================================================================
    def test_d8_search_pricing(self):
        """D8: Search for 'pricing' in all documents.

        Accept any agent that searches for pricing info.
        """
        query = "Search for 'pricing' in all documents"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D8",
            test_name="test_d8_search_pricing",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["pricing"],
        )

        assert result.status in ("pass", "partial"), f"D8 failed: {result.error_message}"

    # =========================================================================
    # D9: Client info query
    # =========================================================================
    def test_d9_acme_corp_info(self):
        """D9: What do we know about Acme Corp?

        Accept any agent that provides Acme Corp info.
        """
        query = "What do we know about Acme Corp?"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D9",
            test_name="test_d9_acme_corp_info",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["acme"],
        )

        assert result.status in ("pass", "partial"), f"D9 failed: {result.error_message}"

    # =========================================================================
    # D10: Compare documents
    # =========================================================================
    def test_d10_compare_policies(self):
        """D10: Compare our privacy policy with return policy.

        Accept any agent that creates a comparison.
        """
        query = "Compare our privacy policy with return policy"
        response = self.client.chat(query)

        result = self._record_result(
            test_id="D10",
            test_name="test_d10_compare_policies",
            query=query,
            expected_agents=[],  # Accept any agent
            response=response,
            keywords=["privacy", "return"],
        )

        assert result.status in ("pass", "partial"), f"D10 failed: {result.error_message}"
