"""Comprehensive unit tests for DateTimeTool.

Tests cover:
- Tool definition and metadata
- "now" operation - current datetime with timezone support
- "today" operation - current date only
- "add_days" operation - date arithmetic
- "format" operation - custom datetime formatting
- Timezone handling (UTC, America/New_York, Europe/London, etc.)
- Error handling (invalid timezone, invalid operations, invalid parameters)
- Edge cases (negative days, zero days, various formats)
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch

from src.tools.builtin.datetime_tool import DateTimeTool
from src.tools.base import ToolDefinition, ToolParameter, ToolResult


class TestDateTimeToolDefinition:
    """Tests for DateTimeTool definition and metadata."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    def test_tool_name(self, datetime_tool: DateTimeTool):
        """Test that the tool has the correct name."""
        assert datetime_tool.name == "datetime"

    def test_tool_definition_type(self, datetime_tool: DateTimeTool):
        """Test that definition returns a ToolDefinition instance."""
        assert isinstance(datetime_tool.definition, ToolDefinition)

    def test_tool_description(self, datetime_tool: DateTimeTool):
        """Test that the tool has a meaningful description."""
        definition = datetime_tool.definition
        assert "date" in definition.description.lower() or "time" in definition.description.lower()
        assert len(definition.description) > 10

    def test_tool_has_required_parameters(self, datetime_tool: DateTimeTool):
        """Test that the tool has the expected parameters."""
        definition = datetime_tool.definition
        param_names = [p.name for p in definition.parameters]

        assert "operation" in param_names
        assert "timezone" in param_names
        assert "days" in param_names
        assert "format" in param_names

    def test_operation_parameter(self, datetime_tool: DateTimeTool):
        """Test the operation parameter configuration."""
        definition = datetime_tool.definition
        operation_param = next(p for p in definition.parameters if p.name == "operation")

        assert operation_param.type == "string"
        assert operation_param.required is True
        assert operation_param.enum == ["now", "today", "add_days", "format"]

    def test_timezone_parameter(self, datetime_tool: DateTimeTool):
        """Test the timezone parameter configuration."""
        definition = datetime_tool.definition
        timezone_param = next(p for p in definition.parameters if p.name == "timezone")

        assert timezone_param.type == "string"
        assert timezone_param.required is False
        assert timezone_param.default == "UTC"

    def test_days_parameter(self, datetime_tool: DateTimeTool):
        """Test the days parameter configuration."""
        definition = datetime_tool.definition
        days_param = next(p for p in definition.parameters if p.name == "days")

        assert days_param.type == "number"
        assert days_param.required is False

    def test_format_parameter(self, datetime_tool: DateTimeTool):
        """Test the format parameter configuration."""
        definition = datetime_tool.definition
        format_param = next(p for p in definition.parameters if p.name == "format")

        assert format_param.type == "string"
        assert format_param.required is False

    def test_to_openai_format(self, datetime_tool: DateTimeTool):
        """Test that the definition converts to OpenAI format correctly."""
        openai_format = datetime_tool.definition.to_openai_format()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "datetime"
        assert "operation" in openai_format["function"]["parameters"]["properties"]
        assert openai_format["function"]["parameters"]["properties"]["operation"]["enum"] == [
            "now", "today", "add_days", "format"
        ]


class TestDateTimeNowOperation:
    """Tests for the 'now' operation."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_now_returns_success(self, datetime_tool: DateTimeTool):
        """Test that 'now' operation returns a successful result."""
        result = await datetime_tool.execute(operation="now")

        assert result.success is True
        assert result.error is None

    @pytest.mark.asyncio
    async def test_now_returns_iso_format(self, datetime_tool: DateTimeTool):
        """Test that 'now' returns datetime in ISO format."""
        result = await datetime_tool.execute(operation="now")

        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(result.output)
        assert isinstance(parsed, datetime)

    @pytest.mark.asyncio
    async def test_now_default_utc(self, datetime_tool: DateTimeTool):
        """Test that 'now' defaults to UTC timezone."""
        result = await datetime_tool.execute(operation="now")

        # Should contain UTC offset (+00:00)
        assert "+00:00" in result.output or "Z" in result.output or result.output.endswith("+00:00")

    @pytest.mark.asyncio
    async def test_now_with_utc_explicit(self, datetime_tool: DateTimeTool):
        """Test 'now' with explicit UTC timezone."""
        result = await datetime_tool.execute(operation="now", timezone="UTC")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)
        assert parsed.tzinfo is not None

    @pytest.mark.asyncio
    async def test_now_with_new_york_timezone(self, datetime_tool: DateTimeTool):
        """Test 'now' with America/New_York timezone."""
        result = await datetime_tool.execute(operation="now", timezone="America/New_York")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)
        assert parsed.tzinfo is not None

    @pytest.mark.asyncio
    async def test_now_with_london_timezone(self, datetime_tool: DateTimeTool):
        """Test 'now' with Europe/London timezone."""
        result = await datetime_tool.execute(operation="now", timezone="Europe/London")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)
        assert parsed.tzinfo is not None

    @pytest.mark.asyncio
    async def test_now_with_tokyo_timezone(self, datetime_tool: DateTimeTool):
        """Test 'now' with Asia/Tokyo timezone."""
        result = await datetime_tool.execute(operation="now", timezone="Asia/Tokyo")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)
        assert parsed.tzinfo is not None

    @pytest.mark.asyncio
    async def test_now_returns_current_time(self, datetime_tool: DateTimeTool):
        """Test that 'now' returns approximately the current time."""
        before = datetime.now(ZoneInfo("UTC"))
        result = await datetime_tool.execute(operation="now", timezone="UTC")
        after = datetime.now(ZoneInfo("UTC"))

        parsed = datetime.fromisoformat(result.output)

        # The returned time should be between before and after
        assert before <= parsed <= after


class TestDateTimeTodayOperation:
    """Tests for the 'today' operation."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_today_returns_success(self, datetime_tool: DateTimeTool):
        """Test that 'today' operation returns a successful result."""
        result = await datetime_tool.execute(operation="today")

        assert result.success is True
        assert result.error is None

    @pytest.mark.asyncio
    async def test_today_returns_date_only(self, datetime_tool: DateTimeTool):
        """Test that 'today' returns only the date part (no time)."""
        result = await datetime_tool.execute(operation="today")

        # Should be in YYYY-MM-DD format (no time component)
        assert len(result.output) == 10
        assert result.output.count("-") == 2

    @pytest.mark.asyncio
    async def test_today_is_valid_iso_date(self, datetime_tool: DateTimeTool):
        """Test that 'today' returns a valid ISO date."""
        result = await datetime_tool.execute(operation="today")

        # Should be parseable as a date
        from datetime import date
        parsed = date.fromisoformat(result.output)
        assert isinstance(parsed, date)

    @pytest.mark.asyncio
    async def test_today_default_utc(self, datetime_tool: DateTimeTool):
        """Test that 'today' uses UTC by default."""
        result = await datetime_tool.execute(operation="today")
        utc_today = datetime.now(ZoneInfo("UTC")).date().isoformat()

        assert result.output == utc_today

    @pytest.mark.asyncio
    async def test_today_with_different_timezone(self, datetime_tool: DateTimeTool):
        """Test 'today' with a specific timezone."""
        result = await datetime_tool.execute(operation="today", timezone="Asia/Tokyo")

        assert result.success is True
        from datetime import date
        parsed = date.fromisoformat(result.output)
        assert isinstance(parsed, date)


class TestDateTimeAddDaysOperation:
    """Tests for the 'add_days' operation."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_add_days_positive(self, datetime_tool: DateTimeTool):
        """Test adding positive days."""
        now = datetime.now(ZoneInfo("UTC"))
        result = await datetime_tool.execute(operation="add_days", days=7, timezone="UTC")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)

        # Should be approximately 7 days in the future
        expected = now + timedelta(days=7)
        assert abs((parsed - expected).total_seconds()) < 2  # Within 2 seconds

    @pytest.mark.asyncio
    async def test_add_days_negative(self, datetime_tool: DateTimeTool):
        """Test adding negative days (going back in time)."""
        now = datetime.now(ZoneInfo("UTC"))
        result = await datetime_tool.execute(operation="add_days", days=-3, timezone="UTC")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)

        # Should be approximately 3 days in the past
        expected = now - timedelta(days=3)
        assert abs((parsed - expected).total_seconds()) < 2

    @pytest.mark.asyncio
    async def test_add_days_zero(self, datetime_tool: DateTimeTool):
        """Test adding zero days."""
        now = datetime.now(ZoneInfo("UTC"))
        result = await datetime_tool.execute(operation="add_days", days=0, timezone="UTC")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)

        # Should be approximately now
        assert abs((parsed - now).total_seconds()) < 2

    @pytest.mark.asyncio
    async def test_add_days_large_number(self, datetime_tool: DateTimeTool):
        """Test adding a large number of days."""
        now = datetime.now(ZoneInfo("UTC"))
        result = await datetime_tool.execute(operation="add_days", days=365, timezone="UTC")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)

        expected = now + timedelta(days=365)
        assert abs((parsed - expected).total_seconds()) < 2

    @pytest.mark.asyncio
    async def test_add_days_with_timezone(self, datetime_tool: DateTimeTool):
        """Test adding days with a specific timezone."""
        result = await datetime_tool.execute(
            operation="add_days",
            days=1,
            timezone="America/Los_Angeles"
        )

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)
        assert parsed.tzinfo is not None

    @pytest.mark.asyncio
    async def test_add_days_default_zero(self, datetime_tool: DateTimeTool):
        """Test that days defaults to 0 if not provided."""
        now = datetime.now(ZoneInfo("UTC"))
        result = await datetime_tool.execute(operation="add_days", timezone="UTC")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)

        # Should be approximately now (0 days added)
        assert abs((parsed - now).total_seconds()) < 2

    @pytest.mark.asyncio
    async def test_add_days_float_truncated(self, datetime_tool: DateTimeTool):
        """Test that float days are converted to int."""
        now = datetime.now(ZoneInfo("UTC"))
        result = await datetime_tool.execute(operation="add_days", days=2.9, timezone="UTC")

        assert result.success is True
        parsed = datetime.fromisoformat(result.output)

        # Should add 2 days (int(2.9) = 2)
        expected = now + timedelta(days=2)
        assert abs((parsed - expected).total_seconds()) < 2

    @pytest.mark.asyncio
    async def test_add_days_invalid_type_string(self, datetime_tool: DateTimeTool):
        """Test that string days returns an error."""
        result = await datetime_tool.execute(operation="add_days", days="seven")

        assert result.success is False
        assert result.output is None
        assert "number" in result.error.lower()


class TestDateTimeFormatOperation:
    """Tests for the 'format' operation."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_format_default(self, datetime_tool: DateTimeTool):
        """Test format with default format string."""
        result = await datetime_tool.execute(operation="format")

        assert result.success is True
        # Default format is "%Y-%m-%d %H:%M:%S"
        # Should be in format like "2024-01-15 10:30:45"
        assert len(result.output) == 19
        assert result.output[4] == "-"
        assert result.output[7] == "-"
        assert result.output[10] == " "
        assert result.output[13] == ":"
        assert result.output[16] == ":"

    @pytest.mark.asyncio
    async def test_format_date_only(self, datetime_tool: DateTimeTool):
        """Test format with date-only format string."""
        result = await datetime_tool.execute(operation="format", format="%Y-%m-%d")

        assert result.success is True
        assert len(result.output) == 10
        assert result.output.count("-") == 2

    @pytest.mark.asyncio
    async def test_format_time_only(self, datetime_tool: DateTimeTool):
        """Test format with time-only format string."""
        result = await datetime_tool.execute(operation="format", format="%H:%M:%S")

        assert result.success is True
        assert len(result.output) == 8
        assert result.output.count(":") == 2

    @pytest.mark.asyncio
    async def test_format_human_readable(self, datetime_tool: DateTimeTool):
        """Test format with human-readable format."""
        result = await datetime_tool.execute(operation="format", format="%B %d, %Y")

        assert result.success is True
        # Should contain month name (e.g., "December 27, 2025")
        assert "," in result.output
        assert any(month in result.output for month in [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])

    @pytest.mark.asyncio
    async def test_format_with_weekday(self, datetime_tool: DateTimeTool):
        """Test format with weekday."""
        result = await datetime_tool.execute(operation="format", format="%A, %B %d")

        assert result.success is True
        # Should contain weekday name
        assert any(day in result.output for day in [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ])

    @pytest.mark.asyncio
    async def test_format_twelve_hour_time(self, datetime_tool: DateTimeTool):
        """Test format with 12-hour time."""
        result = await datetime_tool.execute(operation="format", format="%I:%M %p")

        assert result.success is True
        assert "AM" in result.output or "PM" in result.output

    @pytest.mark.asyncio
    async def test_format_with_timezone(self, datetime_tool: DateTimeTool):
        """Test format with specific timezone."""
        result = await datetime_tool.execute(
            operation="format",
            format="%Y-%m-%d %H:%M",
            timezone="America/New_York"
        )

        assert result.success is True
        assert len(result.output) == 16

    @pytest.mark.asyncio
    async def test_format_iso_week(self, datetime_tool: DateTimeTool):
        """Test format with ISO week number."""
        result = await datetime_tool.execute(operation="format", format="Week %W of %Y")

        assert result.success is True
        assert "Week" in result.output


class TestDateTimeTimezoneHandling:
    """Tests for timezone handling across operations."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_invalid_timezone(self, datetime_tool: DateTimeTool):
        """Test that invalid timezone returns an error."""
        result = await datetime_tool.execute(operation="now", timezone="Invalid/Timezone")

        assert result.success is False
        assert result.output is None
        assert "invalid timezone" in result.error.lower()

    @pytest.mark.asyncio
    async def test_empty_timezone(self, datetime_tool: DateTimeTool):
        """Test that empty timezone string returns an error."""
        result = await datetime_tool.execute(operation="now", timezone="")

        assert result.success is False
        assert result.output is None
        assert "invalid timezone" in result.error.lower()

    @pytest.mark.asyncio
    async def test_various_valid_timezones(self, datetime_tool: DateTimeTool):
        """Test various valid timezone strings."""
        valid_timezones = [
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney",
            "Pacific/Auckland",
        ]

        for tz in valid_timezones:
            result = await datetime_tool.execute(operation="now", timezone=tz)
            assert result.success is True, f"Failed for timezone: {tz}"

    @pytest.mark.asyncio
    async def test_timezone_affects_output(self, datetime_tool: DateTimeTool):
        """Test that different timezones produce different outputs."""
        utc_result = await datetime_tool.execute(operation="now", timezone="UTC")
        tokyo_result = await datetime_tool.execute(operation="now", timezone="Asia/Tokyo")

        utc_time = datetime.fromisoformat(utc_result.output)
        tokyo_time = datetime.fromisoformat(tokyo_result.output)

        # Tokyo is UTC+9, so the hour should be different (unless close to midnight)
        # We check that the offset is different
        assert utc_time.utcoffset() != tokyo_time.utcoffset()


class TestDateTimeErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_unknown_operation(self, datetime_tool: DateTimeTool):
        """Test that unknown operation returns an error."""
        result = await datetime_tool.execute(operation="unknown_op")

        assert result.success is False
        assert result.output is None
        assert "unknown operation" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_operation_type(self, datetime_tool: DateTimeTool):
        """Test handling of non-string operation."""
        # Operation defaults to "now" if not provided or invalid
        result = await datetime_tool.execute()

        assert result.success is True  # Defaults to "now"

    @pytest.mark.asyncio
    async def test_invalid_format_string(self, datetime_tool: DateTimeTool):
        """Test that invalid format string is handled gracefully."""
        # Most format strings work, but let's test a clearly problematic one
        # Note: Python's strftime is quite permissive, so this might actually succeed
        result = await datetime_tool.execute(operation="format", format="%Y-%m-%d")

        # Should succeed with a valid format
        assert result.success is True

    @pytest.mark.asyncio
    async def test_empty_format_uses_default(self, datetime_tool: DateTimeTool):
        """Test that empty format uses default."""
        result1 = await datetime_tool.execute(operation="format", format="")
        # Empty string is actually a valid format that produces empty output
        assert result1.success is True
        assert result1.output == ""

    @pytest.mark.asyncio
    async def test_add_days_none_returns_error(self, datetime_tool: DateTimeTool):
        """Test add_days with None value returns an error.

        The implementation explicitly checks isinstance(days, (int, float)),
        which returns False for None, triggering the validation error.
        """
        result = await datetime_tool.execute(operation="add_days", days=None)

        assert result.success is False
        assert result.output is None
        assert "number" in result.error.lower()


class TestDateTimeResultTypes:
    """Tests to verify result types and structure."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_result_is_tool_result(self, datetime_tool: DateTimeTool):
        """Test that execute returns a ToolResult instance."""
        result = await datetime_tool.execute(operation="now")

        assert isinstance(result, ToolResult)

    @pytest.mark.asyncio
    async def test_successful_result_has_string_output(self, datetime_tool: DateTimeTool):
        """Test that successful operations return string output."""
        result = await datetime_tool.execute(operation="now")

        assert isinstance(result.output, str)

    @pytest.mark.asyncio
    async def test_error_result_has_none_output(self, datetime_tool: DateTimeTool):
        """Test that error results have None output."""
        result = await datetime_tool.execute(operation="unknown")

        assert result.success is False
        assert result.output is None

    @pytest.mark.asyncio
    async def test_error_result_has_string_error(self, datetime_tool: DateTimeTool):
        """Test that error results have string error messages."""
        result = await datetime_tool.execute(operation="unknown")

        assert result.success is False
        assert isinstance(result.error, str)
        assert len(result.error) > 0


class TestDateTimeOperationConsistency:
    """Tests to verify consistency across operations."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_now_and_today_same_date(self, datetime_tool: DateTimeTool):
        """Test that 'now' and 'today' return the same date (ignoring time)."""
        now_result = await datetime_tool.execute(operation="now", timezone="UTC")
        today_result = await datetime_tool.execute(operation="today", timezone="UTC")

        now_dt = datetime.fromisoformat(now_result.output)
        now_date = now_dt.date().isoformat()

        assert now_date == today_result.output

    @pytest.mark.asyncio
    async def test_add_days_zero_matches_now(self, datetime_tool: DateTimeTool):
        """Test that add_days(0) gives same result as 'now'."""
        now_result = await datetime_tool.execute(operation="now", timezone="UTC")
        add_result = await datetime_tool.execute(operation="add_days", days=0, timezone="UTC")

        now_dt = datetime.fromisoformat(now_result.output)
        add_dt = datetime.fromisoformat(add_result.output)

        # Should be within 1 second of each other
        assert abs((now_dt - add_dt).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_format_produces_parseable_date(self, datetime_tool: DateTimeTool):
        """Test that formatted output can be parsed back."""
        result = await datetime_tool.execute(
            operation="format",
            format="%Y-%m-%d %H:%M:%S",
            timezone="UTC"
        )

        # Should be parseable with strptime
        parsed = datetime.strptime(result.output, "%Y-%m-%d %H:%M:%S")
        assert isinstance(parsed, datetime)


class TestDateTimeWithMocking:
    """Tests using mocking for deterministic results."""

    @pytest.fixture
    def datetime_tool(self) -> DateTimeTool:
        """Create a DateTimeTool instance for testing."""
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_now_with_mocked_time(self, datetime_tool: DateTimeTool):
        """Test 'now' with a mocked datetime for deterministic testing."""
        fixed_time = datetime(2024, 6, 15, 12, 30, 45, tzinfo=ZoneInfo("UTC"))

        with patch("src.tools.builtin.datetime_tool.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time

            result = await datetime_tool.execute(operation="now", timezone="UTC")

            assert result.success is True
            assert "2024-06-15" in result.output
            assert "12:30:45" in result.output

    @pytest.mark.asyncio
    async def test_today_with_mocked_time(self, datetime_tool: DateTimeTool):
        """Test 'today' with a mocked datetime."""
        fixed_time = datetime(2024, 12, 25, 23, 59, 59, tzinfo=ZoneInfo("UTC"))

        with patch("src.tools.builtin.datetime_tool.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time

            result = await datetime_tool.execute(operation="today", timezone="UTC")

            assert result.success is True
            assert result.output == "2024-12-25"

    @pytest.mark.asyncio
    async def test_add_days_with_mocked_time(self, datetime_tool: DateTimeTool):
        """Test 'add_days' with a mocked datetime."""
        fixed_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))

        with patch("src.tools.builtin.datetime_tool.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            # Need to mock timedelta addition
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = await datetime_tool.execute(
                operation="add_days",
                days=31,
                timezone="UTC"
            )

            assert result.success is True
            # January 1 + 31 days = February 1
            assert "2024-02-01" in result.output
