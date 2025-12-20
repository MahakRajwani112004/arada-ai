"""DateTime tool for current time and date operations."""
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class DateTimeTool(BaseTool):
    """Tool for getting current date/time information."""

    @property
    def definition(self) -> ToolDefinition:
        """Return datetime tool definition."""
        return ToolDefinition(
            name="datetime",
            description="Get current date, time, or calculate date differences. Returns ISO format.",
            parameters=[
                ToolParameter(
                    name="operation",
                    type="string",
                    description="The operation to perform",
                    required=True,
                    enum=["now", "today", "add_days", "format"],
                ),
                ToolParameter(
                    name="timezone",
                    type="string",
                    description="Timezone (e.g., 'UTC', 'America/New_York'). Defaults to UTC.",
                    required=False,
                    default="UTC",
                ),
                ToolParameter(
                    name="days",
                    type="number",
                    description="Number of days for add_days operation",
                    required=False,
                ),
                ToolParameter(
                    name="format",
                    type="string",
                    description="Output format for 'format' operation (e.g., '%Y-%m-%d')",
                    required=False,
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute datetime operation."""
        operation = kwargs.get("operation", "now")
        timezone_str = kwargs.get("timezone", "UTC")

        try:
            tz = ZoneInfo(timezone_str)
        except Exception:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid timezone: {timezone_str}",
            )

        now = datetime.now(tz)

        if operation == "now":
            return ToolResult(
                success=True,
                output=now.isoformat(),
            )

        if operation == "today":
            return ToolResult(
                success=True,
                output=now.date().isoformat(),
            )

        if operation == "add_days":
            days = kwargs.get("days", 0)
            if not isinstance(days, (int, float)):
                return ToolResult(
                    success=False,
                    output=None,
                    error="'days' must be a number",
                )
            result_date = now + timedelta(days=int(days))
            return ToolResult(
                success=True,
                output=result_date.isoformat(),
            )

        if operation == "format":
            format_str = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
            try:
                return ToolResult(
                    success=True,
                    output=now.strftime(format_str),
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Invalid format: {str(e)}",
                )

        return ToolResult(
            success=False,
            output=None,
            error=f"Unknown operation: {operation}",
        )
