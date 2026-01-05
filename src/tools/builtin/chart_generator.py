"""Chart Generator Tool for Arada AI Real Estate Analytics."""

import base64
import io
import json
from typing import Any

from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class ChartGeneratorTool(BaseTool):
    """Tool for generating charts and visualizations from data."""

    CHART_TYPES = {
        "bar": "Bar chart for comparing categories",
        "line": "Line chart for trends over time",
        "pie": "Pie chart for showing proportions",
        "horizontal_bar": "Horizontal bar chart for rankings",
        "area": "Area chart for cumulative trends",
        "scatter": "Scatter plot for correlations",
    }

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="chart_generator",
            description="""Generate charts and visualizations from data.

Available chart types:
- bar: Compare categories (e.g., bookings by development)
- line: Show trends over time (e.g., monthly sales)
- pie: Show proportions (e.g., channel mix)
- horizontal_bar: Rankings (e.g., top performers)
- area: Cumulative trends
- scatter: Correlations

Returns:
- ASCII representation of the chart for text display
- Chart configuration for frontend rendering
- Data summary and insights""",
            parameters=[
                ToolParameter(
                    name="chart_type",
                    type="string",
                    description="Type of chart to generate",
                    required=True,
                    enum=["bar", "line", "pie", "horizontal_bar", "area", "scatter"],
                ),
                ToolParameter(
                    name="data",
                    type="array",
                    description="Data points as array of objects with 'label' and 'value' keys",
                    required=True,
                ),
                ToolParameter(
                    name="title",
                    type="string",
                    description="Chart title",
                    required=True,
                ),
                ToolParameter(
                    name="x_label",
                    type="string",
                    description="Label for X-axis",
                    required=False,
                ),
                ToolParameter(
                    name="y_label",
                    type="string",
                    description="Label for Y-axis",
                    required=False,
                ),
                ToolParameter(
                    name="show_values",
                    type="boolean",
                    description="Whether to show values on the chart",
                    required=False,
                ),
                ToolParameter(
                    name="color_scheme",
                    type="string",
                    description="Color scheme: 'default', 'blue', 'green', 'gradient'",
                    required=False,
                    enum=["default", "blue", "green", "gradient"],
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Generate a chart from the provided data."""
        chart_type = kwargs.get("chart_type", "bar")
        data = kwargs.get("data", [])
        title = kwargs.get("title", "Chart")
        x_label = kwargs.get("x_label", "")
        y_label = kwargs.get("y_label", "")
        show_values = kwargs.get("show_values", True)
        color_scheme = kwargs.get("color_scheme", "default")

        try:
            if not data:
                return ToolResult(
                    success=False,
                    output=None,
                    error="No data provided for chart generation",
                )

            # Generate ASCII representation
            ascii_chart = self._generate_ascii_chart(
                chart_type=chart_type,
                data=data,
                title=title,
                show_values=show_values,
            )

            # Generate chart configuration for frontend
            chart_config = self._generate_chart_config(
                chart_type=chart_type,
                data=data,
                title=title,
                x_label=x_label,
                y_label=y_label,
                color_scheme=color_scheme,
            )

            # Generate data insights
            insights = self._generate_insights(data, chart_type)

            return ToolResult(
                success=True,
                output={
                    "ascii_chart": ascii_chart,
                    "chart_config": chart_config,
                    "insights": insights,
                    "data_summary": {
                        "total_points": len(data),
                        "max_value": max(d.get("value", 0) for d in data) if data else 0,
                        "min_value": min(d.get("value", 0) for d in data) if data else 0,
                        "sum": sum(d.get("value", 0) for d in data),
                    },
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Chart generation failed: {str(e)}",
            )

    def _generate_ascii_chart(
        self,
        chart_type: str,
        data: list,
        title: str,
        show_values: bool,
    ) -> str:
        """Generate ASCII representation of the chart."""
        if not data:
            return "No data to display"

        lines = []
        lines.append(f"\n{'=' * 60}")
        lines.append(f"  {title}")
        lines.append(f"{'=' * 60}\n")

        if chart_type in ["bar", "horizontal_bar"]:
            return self._ascii_bar_chart(data, lines, show_values)
        elif chart_type == "line":
            return self._ascii_line_chart(data, lines, show_values)
        elif chart_type == "pie":
            return self._ascii_pie_chart(data, lines, show_values)
        else:
            return self._ascii_bar_chart(data, lines, show_values)

    def _ascii_bar_chart(self, data: list, lines: list, show_values: bool) -> str:
        """Generate ASCII horizontal bar chart."""
        max_value = max(d.get("value", 0) for d in data) if data else 1
        max_label_len = max(len(str(d.get("label", ""))) for d in data) if data else 10
        bar_width = 40

        for item in data:
            label = str(item.get("label", ""))[:20].ljust(max_label_len)
            value = item.get("value", 0)
            bar_length = int((value / max_value) * bar_width) if max_value > 0 else 0
            bar = "█" * bar_length + "░" * (bar_width - bar_length)

            if show_values:
                # Format value nicely
                if value >= 1_000_000:
                    value_str = f"{value/1_000_000:.1f}M"
                elif value >= 1_000:
                    value_str = f"{value/1_000:.1f}K"
                else:
                    value_str = f"{value:.1f}" if isinstance(value, float) else str(value)
                lines.append(f"  {label} │{bar}│ {value_str}")
            else:
                lines.append(f"  {label} │{bar}│")

        lines.append("")
        return "\n".join(lines)

    def _ascii_line_chart(self, data: list, lines: list, show_values: bool) -> str:
        """Generate ASCII line chart representation."""
        if not data:
            return "\n".join(lines) + "\nNo data"

        max_value = max(d.get("value", 0) for d in data)
        min_value = min(d.get("value", 0) for d in data)
        height = 10
        width = min(len(data), 50)

        # Create grid
        grid = [[" " for _ in range(width)] for _ in range(height)]

        # Plot points
        for i, item in enumerate(data[:width]):
            value = item.get("value", 0)
            if max_value > min_value:
                y = int((value - min_value) / (max_value - min_value) * (height - 1))
            else:
                y = height // 2
            grid[height - 1 - y][i] = "●"

        # Connect with lines
        for row in range(height):
            lines.append(f"  {''.join(grid[row])}")

        # X-axis labels (first and last)
        if data:
            first_label = str(data[0].get("label", ""))[:10]
            last_label = str(data[-1].get("label", ""))[:10] if len(data) > 1 else ""
            lines.append(f"  {first_label}{' ' * (width - len(first_label) - len(last_label))}{last_label}")

        lines.append("")
        return "\n".join(lines)

    def _ascii_pie_chart(self, data: list, lines: list, show_values: bool) -> str:
        """Generate ASCII pie chart representation (as proportional bars)."""
        total = sum(d.get("value", 0) for d in data)
        if total == 0:
            return "\n".join(lines) + "\nNo data"

        max_label_len = max(len(str(d.get("label", ""))) for d in data) if data else 10

        for item in data:
            label = str(item.get("label", ""))[:20].ljust(max_label_len)
            value = item.get("value", 0)
            percentage = (value / total) * 100 if total > 0 else 0
            bar_length = int(percentage / 2)  # 50 chars = 100%
            bar = "█" * bar_length

            if show_values:
                lines.append(f"  {label} │{bar} {percentage:.1f}%")
            else:
                lines.append(f"  {label} │{bar}")

        lines.append(f"\n  Total: {total:,.0f}")
        lines.append("")
        return "\n".join(lines)

    def _generate_chart_config(
        self,
        chart_type: str,
        data: list,
        title: str,
        x_label: str,
        y_label: str,
        color_scheme: str,
    ) -> dict:
        """Generate configuration for frontend chart rendering."""
        color_schemes = {
            "default": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"],
            "blue": ["#1E40AF", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE", "#DBEAFE"],
            "green": ["#065F46", "#059669", "#10B981", "#34D399", "#6EE7B7", "#A7F3D0"],
            "gradient": ["#6366F1", "#8B5CF6", "#A855F7", "#C084FC", "#D8B4FE", "#E9D5FF"],
        }

        colors = color_schemes.get(color_scheme, color_schemes["default"])

        return {
            "type": chart_type,
            "data": {
                "labels": [d.get("label", "") for d in data],
                "datasets": [
                    {
                        "label": title,
                        "data": [d.get("value", 0) for d in data],
                        "backgroundColor": colors[: len(data)],
                        "borderColor": colors[: len(data)],
                    }
                ],
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": True, "text": title},
                },
                "scales": {
                    "x": {"title": {"display": bool(x_label), "text": x_label}},
                    "y": {"title": {"display": bool(y_label), "text": y_label}},
                },
            },
        }

    def _generate_insights(self, data: list, chart_type: str) -> list:
        """Generate automatic insights from the data."""
        if not data:
            return []

        insights = []
        values = [d.get("value", 0) for d in data]
        labels = [d.get("label", "") for d in data]

        # Find max and min
        max_idx = values.index(max(values))
        min_idx = values.index(min(values))
        avg = sum(values) / len(values) if values else 0

        insights.append(f"Highest: {labels[max_idx]} ({values[max_idx]:,.0f})")
        insights.append(f"Lowest: {labels[min_idx]} ({values[min_idx]:,.0f})")
        insights.append(f"Average: {avg:,.0f}")

        # Variance insight
        if max(values) > 0 and min(values) >= 0:
            spread = ((max(values) - min(values)) / max(values)) * 100
            if spread > 50:
                insights.append(f"High variance ({spread:.0f}%) between categories")
            elif spread < 20:
                insights.append(f"Categories are relatively balanced ({spread:.0f}% spread)")

        return insights
