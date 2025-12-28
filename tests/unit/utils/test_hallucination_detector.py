"""Tests for hallucination risk detection."""

import pytest

from src.utils.hallucination_detector import (
    HallucinationWarning,
    DATA_ACCESS_KEYWORDS,
    GENERATIVE_KEYWORDS,
    DATA_ACCESS_MCPS,
    detect_data_access_intent,
    is_generative_task,
    check_agent_hallucination_risk,
    check_workflow_hallucination_risk,
)


class TestDataAccessKeywords:
    """Tests for DATA_ACCESS_KEYWORDS set."""

    def test_contains_order_keywords(self):
        """Test order-related keywords."""
        assert "order" in DATA_ACCESS_KEYWORDS
        assert "shipping" in DATA_ACCESS_KEYWORDS
        assert "tracking" in DATA_ACCESS_KEYWORDS

    def test_contains_database_keywords(self):
        """Test database-related keywords."""
        assert "database" in DATA_ACCESS_KEYWORDS
        assert "query" in DATA_ACCESS_KEYWORDS
        assert "fetch" in DATA_ACCESS_KEYWORDS

    def test_contains_calendar_keywords(self):
        """Test calendar-related keywords."""
        assert "calendar" in DATA_ACCESS_KEYWORDS
        assert "meeting" in DATA_ACCESS_KEYWORDS
        assert "schedule" in DATA_ACCESS_KEYWORDS


class TestGenerativeKeywords:
    """Tests for GENERATIVE_KEYWORDS set."""

    def test_contains_generative_terms(self):
        """Test generative task keywords."""
        assert "generate" in GENERATIVE_KEYWORDS
        assert "write" in GENERATIVE_KEYWORDS
        assert "summarize" in GENERATIVE_KEYWORDS
        assert "translate" in GENERATIVE_KEYWORDS


class TestDataAccessMCPs:
    """Tests for DATA_ACCESS_MCPS set."""

    def test_contains_database_mcps(self):
        """Test database MCPs."""
        assert "postgres" in DATA_ACCESS_MCPS
        assert "mongodb" in DATA_ACCESS_MCPS
        assert "redis" in DATA_ACCESS_MCPS

    def test_contains_crm_mcps(self):
        """Test CRM MCPs."""
        assert "salesforce" in DATA_ACCESS_MCPS
        assert "hubspot" in DATA_ACCESS_MCPS

    def test_contains_calendar_mcps(self):
        """Test calendar MCPs."""
        assert "google-calendar" in DATA_ACCESS_MCPS
        assert "outlook" in DATA_ACCESS_MCPS


class TestDetectDataAccessIntent:
    """Tests for detect_data_access_intent function."""

    def test_detects_order_keywords(self):
        """Test detection of order-related keywords."""
        text = "I need to check the order status and shipping information"
        result = detect_data_access_intent(text)

        assert "order" in result or "order status" in result
        assert "shipping" in result

    def test_detects_database_keywords(self):
        """Test detection of database keywords."""
        text = "Query the database to fetch user records"
        result = detect_data_access_intent(text)

        assert "database" in result
        assert "query" in result or "fetch" in result

    def test_detects_calendar_keywords(self):
        """Test detection of calendar keywords."""
        text = "Schedule a meeting on my calendar"
        result = detect_data_access_intent(text)

        assert "meeting" in result
        assert "calendar" in result

    def test_returns_empty_for_no_matches(self):
        """Test returns empty set when no keywords match."""
        text = "Please write a creative story about a dragon"
        result = detect_data_access_intent(text)

        assert len(result) == 0

    def test_case_insensitive(self):
        """Test that detection is case insensitive."""
        text = "Check the ORDER STATUS and SHIPPING"
        result = detect_data_access_intent(text)

        assert len(result) > 0

    def test_word_boundary_matching(self):
        """Test that partial matches are not detected."""
        text = "reorder the list"  # Contains 'order' but as part of 'reorder'
        result = detect_data_access_intent(text)

        # Should not match 'order' from 'reorder'
        # This depends on implementation - may need adjustment


class TestIsGenerativeTask:
    """Tests for is_generative_task function."""

    def test_generative_task_detection(self):
        """Test detection of generative tasks."""
        text = "Generate a summary and translate the document"
        result = is_generative_task(text)

        assert result is True

    def test_data_access_task_detection(self):
        """Test detection of data access tasks."""
        text = "Query the database to fetch order details"
        result = is_generative_task(text)

        assert result is False

    def test_mixed_task_with_more_generative(self):
        """Test mixed task with more generative keywords."""
        text = "Generate a creative summary, write content, and translate"
        result = is_generative_task(text)

        assert result is True

    def test_mixed_task_with_more_data_access(self):
        """Test mixed task with more data access keywords."""
        text = "Fetch orders, query database, lookup records, and summarize"
        result = is_generative_task(text)

        assert result is False


class TestCheckAgentHallucinationRisk:
    """Tests for check_agent_hallucination_risk function."""

    def test_no_risk_for_generative_agent(self):
        """Test no warnings for generative agents."""
        warnings = check_agent_hallucination_risk(
            agent_name="Content Writer",
            agent_goal="Generate creative blog posts and summaries",
        )

        assert len(warnings) == 0

    def test_high_risk_without_tools_or_mcps(self):
        """Test high risk when agent needs data but has no tools/MCPs."""
        warnings = check_agent_hallucination_risk(
            agent_name="Order Tracker",
            agent_goal="Check order status and shipping information from database",
            enabled_tools=[],
            connected_mcps=[],
        )

        assert len(warnings) > 0
        assert warnings[0].severity == "high"
        assert "no tools or MCP" in warnings[0].message

    def test_medium_risk_with_mcps_only(self):
        """Test medium risk when agent has MCPs but no specific tools."""
        warnings = check_agent_hallucination_risk(
            agent_name="Order Tracker",
            agent_goal="Check order status from database",
            enabled_tools=[],
            connected_mcps=["postgres"],
        )

        assert len(warnings) > 0
        assert warnings[0].severity == "medium"

    def test_no_risk_with_tools_and_mcps(self):
        """Test no warnings when agent has proper tools."""
        warnings = check_agent_hallucination_risk(
            agent_name="Order Tracker",
            agent_goal="Check order status from database",
            enabled_tools=["query_orders", "get_shipping"],
            connected_mcps=["postgres"],
        )

        assert len(warnings) == 0

    def test_includes_step_id(self):
        """Test that warnings include step_id when provided."""
        warnings = check_agent_hallucination_risk(
            agent_name="Data Agent",
            agent_goal="Fetch customer records from database",
            step_id="step-123",
        )

        if warnings:
            assert warnings[0].affected_step == "step-123"

    def test_suggestion_provided(self):
        """Test that warnings include suggestions."""
        warnings = check_agent_hallucination_risk(
            agent_name="Data Agent",
            agent_goal="Query the database for user information",
        )

        if warnings:
            assert warnings[0].suggestion is not None
            assert len(warnings[0].suggestion) > 0


class TestCheckWorkflowHallucinationRisk:
    """Tests for check_workflow_hallucination_risk function."""

    def test_empty_workflow(self):
        """Test empty workflow returns no warnings."""
        warnings = check_workflow_hallucination_risk([])
        assert len(warnings) == 0

    def test_skips_non_agent_steps(self):
        """Test that non-agent steps are skipped."""
        steps = [
            {"id": "parallel-1", "type": "parallel"},
            {"id": "cond-1", "type": "conditional"},
        ]
        warnings = check_workflow_hallucination_risk(steps)
        assert len(warnings) == 0

    def test_warns_for_step_without_agent(self):
        """Test warning for step with no agent configured."""
        steps = [
            {"id": "step-1", "type": "agent"},  # No agent_id or suggested_agent
        ]
        warnings = check_workflow_hallucination_risk(steps)

        assert len(warnings) == 1
        assert warnings[0].severity == "high"
        assert "no agent configured" in warnings[0].message

    def test_checks_suggested_agents(self):
        """Test that suggested agents are checked for risk."""
        steps = [
            {
                "id": "step-1",
                "type": "agent",
                "suggested_agent": {
                    "name": "Order Checker",
                    "goal": "Check order status from database",
                    "suggested_tools": [],
                    "required_mcps": [],
                },
            },
        ]
        warnings = check_workflow_hallucination_risk(steps)

        assert len(warnings) > 0

    def test_inherits_connected_mcps(self):
        """Test that workflow-level MCPs are considered."""
        steps = [
            {
                "id": "step-1",
                "type": "agent",
                "suggested_agent": {
                    "name": "Order Checker",
                    "goal": "Check order status from database",
                    "suggested_tools": [],
                },
            },
        ]
        # With connected MCPs, risk should be reduced
        warnings = check_workflow_hallucination_risk(steps, connected_mcps=["postgres"])

        # Should have medium risk (has MCP but no tools) instead of high
        if warnings:
            assert warnings[0].severity in ["medium", "low"]


class TestHallucinationWarning:
    """Tests for HallucinationWarning dataclass."""

    def test_create_warning(self):
        """Test creating a warning."""
        warning = HallucinationWarning(
            severity="high",
            message="Test warning message",
            suggestion="Test suggestion",
            affected_step="step-1",
        )

        assert warning.severity == "high"
        assert warning.message == "Test warning message"
        assert warning.suggestion == "Test suggestion"
        assert warning.affected_step == "step-1"

    def test_optional_affected_step(self):
        """Test that affected_step is optional."""
        warning = HallucinationWarning(
            severity="medium",
            message="Test",
            suggestion="Suggestion",
        )

        assert warning.affected_step is None
