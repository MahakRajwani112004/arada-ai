"""KPI Calculator Tool for Arada AI Real Estate Analytics."""

from typing import Any

from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class KPICalculatorTool(BaseTool):
    """Tool for calculating dynamic KPIs based on context and question type."""

    # Available KPI definitions
    KPI_DEFINITIONS = {
        "total_bookings": {
            "name": "Total Bookings",
            "description": "Count of all booking transactions",
            "formula": "COUNT(unit_id)",
            "unit": "units",
        },
        "portfolio_value": {
            "name": "Portfolio Value",
            "description": "Sum of all net sale values",
            "formula": "SUM(net_sale_value)",
            "unit": "AED",
        },
        "avg_unit_price": {
            "name": "Average Unit Price",
            "description": "Average net sale value per unit",
            "formula": "AVG(net_sale_value)",
            "unit": "AED",
        },
        "cancellation_rate": {
            "name": "Cancellation Rate",
            "description": "Percentage of cancelled bookings",
            "formula": "COUNT(cancelled) / COUNT(total) * 100",
            "unit": "%",
            "benchmark": 35.0,
            "threshold_warning": 45.0,
            "threshold_critical": 55.0,
        },
        "avg_realization": {
            "name": "Average Realization",
            "description": "Average percentage of amount collected vs net sale value",
            "formula": "AVG(amount_collected / net_sale_value * 100)",
            "unit": "%",
        },
        "avg_discount": {
            "name": "Average Discount",
            "description": "Average discount percentage given",
            "formula": "AVG(discount_percent)",
            "unit": "%",
        },
        "collection_efficiency": {
            "name": "Collection Efficiency",
            "description": "Total collected vs total portfolio value",
            "formula": "SUM(amount_collected) / SUM(net_sale_value) * 100",
            "unit": "%",
        },
        "avg_deal_size": {
            "name": "Average Deal Size",
            "description": "Average transaction value",
            "formula": "AVG(net_sale_value)",
            "unit": "AED",
        },
        "conversion_rate": {
            "name": "Conversion Rate",
            "description": "Percentage of non-cancelled bookings",
            "formula": "COUNT(non_cancelled) / COUNT(total) * 100",
            "unit": "%",
        },
        "price_per_sqft": {
            "name": "Price per Sqft",
            "description": "Average price per square foot",
            "formula": "AVG(net_sale_value / area_sqft)",
            "unit": "AED/sqft",
        },
    }

    # Question type to KPI mapping for auto-selection
    QUESTION_KPI_MAP = {
        "performance": ["total_bookings", "portfolio_value", "cancellation_rate", "avg_realization", "avg_discount"],
        "sales": ["total_bookings", "portfolio_value", "avg_unit_price", "conversion_rate"],
        "collection": ["avg_realization", "collection_efficiency", "portfolio_value"],
        "pricing": ["avg_unit_price", "avg_discount", "price_per_sqft"],
        "risk": ["cancellation_rate", "avg_realization", "avg_discount"],
        "comparison": ["total_bookings", "portfolio_value", "cancellation_rate", "avg_realization"],
    }

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="kpi_calculator",
            description="""Calculate relevant KPIs dynamically based on the question context.

Features:
- Auto-selects relevant KPIs based on question type (performance, sales, collection, pricing, risk)
- Calculates benchmarks and thresholds
- Compares against portfolio averages
- Generates performance indices

Available KPIs:
- total_bookings: Count of bookings
- portfolio_value: Total value in AED
- avg_unit_price: Average price per unit
- cancellation_rate: % of cancelled bookings
- avg_realization: % of amount collected
- avg_discount: Average discount given
- collection_efficiency: Collection vs total value
- conversion_rate: Non-cancelled bookings %
- price_per_sqft: Price per square foot""",
            parameters=[
                ToolParameter(
                    name="question_type",
                    type="string",
                    description="Type of analysis question to auto-select KPIs",
                    required=False,
                    enum=["performance", "sales", "collection", "pricing", "risk", "comparison"],
                ),
                ToolParameter(
                    name="kpis",
                    type="array",
                    description="Specific KPIs to calculate (overrides auto-selection)",
                    required=False,
                ),
                ToolParameter(
                    name="entity",
                    type="object",
                    description="Entity to calculate KPIs for (e.g., {'development': 'DAMAC Bay'})",
                    required=False,
                ),
                ToolParameter(
                    name="compare_to_portfolio",
                    type="boolean",
                    description="Whether to include portfolio benchmark comparison",
                    required=False,
                ),
                ToolParameter(
                    name="include_thresholds",
                    type="boolean",
                    description="Whether to include warning/critical thresholds",
                    required=False,
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Calculate KPIs based on the request."""
        question_type = kwargs.get("question_type")
        kpis = kwargs.get("kpis", [])
        entity = kwargs.get("entity", {})
        compare_to_portfolio = kwargs.get("compare_to_portfolio", True)
        include_thresholds = kwargs.get("include_thresholds", True)

        try:
            # Auto-select KPIs if not specified
            if not kpis and question_type:
                kpis = self.QUESTION_KPI_MAP.get(question_type, list(self.KPI_DEFINITIONS.keys())[:5])

            # Calculate each KPI
            results = []
            for kpi_id in kpis:
                if kpi_id in self.KPI_DEFINITIONS:
                    kpi_result = await self._calculate_kpi(
                        kpi_id=kpi_id,
                        entity=entity,
                        compare_to_portfolio=compare_to_portfolio,
                        include_thresholds=include_thresholds,
                    )
                    results.append(kpi_result)

            return ToolResult(
                success=True,
                output={
                    "entity": entity or "Portfolio",
                    "question_type": question_type,
                    "kpis": results,
                    "auto_generated": not kwargs.get("kpis"),
                    "kpi_count": len(results),
                    "entity_filter": entity,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"KPI calculation failed: {str(e)}",
            )

    async def _calculate_kpi(
        self,
        kpi_id: str,
        entity: dict,
        compare_to_portfolio: bool,
        include_thresholds: bool,
    ) -> dict:
        """Calculate a single KPI with optional comparisons."""
        kpi_def = self.KPI_DEFINITIONS[kpi_id]

        # TODO: Replace with actual database calculation
        # Placeholder values for demonstration
        sample_values = {
            "total_bookings": {"entity": 172, "portfolio": 1000},
            "portfolio_value": {"entity": 831600000, "portfolio": 5370000000},
            "avg_unit_price": {"entity": 4830000, "portfolio": 5670000},
            "cancellation_rate": {"entity": 57.0, "portfolio": 50.9},
            "avg_realization": {"entity": 37.1, "portfolio": 36.8},
            "avg_discount": {"entity": 5.2, "portfolio": 5.1},
            "collection_efficiency": {"entity": 37.1, "portfolio": 36.8},
            "conversion_rate": {"entity": 43.0, "portfolio": 49.1},
            "price_per_sqft": {"entity": 2850, "portfolio": 3200},
        }

        values = sample_values.get(kpi_id, {"entity": 0, "portfolio": 0})

        result = {
            "kpi_id": kpi_id,
            "name": kpi_def["name"],
            "description": kpi_def["description"],
            "value": values["entity"] if entity else values["portfolio"],
            "unit": kpi_def["unit"],
            "formula": kpi_def["formula"],
        }

        if compare_to_portfolio and entity:
            portfolio_value = values["portfolio"]
            entity_value = values["entity"]
            delta = entity_value - portfolio_value
            delta_percent = (delta / portfolio_value * 100) if portfolio_value else 0

            result["portfolio_benchmark"] = portfolio_value
            result["delta"] = delta
            result["delta_percent"] = round(delta_percent, 1)
            result["vs_portfolio"] = "above" if delta > 0 else "below" if delta < 0 else "equal"

        if include_thresholds and "threshold_warning" in kpi_def:
            result["benchmark"] = kpi_def.get("benchmark")
            result["threshold_warning"] = kpi_def.get("threshold_warning")
            result["threshold_critical"] = kpi_def.get("threshold_critical")

            current_value = result["value"]
            if current_value >= kpi_def.get("threshold_critical", float("inf")):
                result["status"] = "critical"
                result["status_icon"] = "🔴"
            elif current_value >= kpi_def.get("threshold_warning", float("inf")):
                result["status"] = "warning"
                result["status_icon"] = "⚠️"
            else:
                result["status"] = "normal"
                result["status_icon"] = "✅"

        return result
