"""Real Estate Query Tool for Arada AI Analytics Bot."""

from typing import Any

from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class RealEstateQueryTool(BaseTool):
    """Tool for querying real estate booking data with SQL-like capabilities."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="real_estate_query",
            description="""Query real estate booking data for analytics.

Available columns:
- unit_id: Unique unit identifier
- development: Development name (DAMAC Bay, DAMAC Hills, DAMAC Lagoons, Downtown Dubai, Dubai Hills Estate, Emaar Beachfront)
- cluster: Cluster within development (Waterfront, Golf Greens, Venice, Central Park, Marina Vista, etc.)
- unit_type: Type of unit (Studio, 1BR, 2BR, 3BR, Townhouse, Villa)
- area_sqft: Unit area in square feet
- selling_price: Original selling price (AED)
- discount_percent: Discount given (%)
- net_sale_value: Final sale value after discount (AED)
- dp_tier: Down payment tier (10%, 20%, 30%)
- lead_source: Source of lead (Broker Network, Digital, Event, Direct)
- deal_type: Type of deal (Direct, Broker)
- booking_date: Date of booking
- booking_status: Status (Booked, Cancelled, Handover, Registered)
- nationality: Buyer nationality
- amount_collected: Amount collected so far (AED)
- realization_percent: Percentage of total collected
- ageing_days: Days since booking

Supports aggregations: SUM, AVG, COUNT, MIN, MAX, GROUP BY
Supports filters: WHERE conditions
Supports ordering: ORDER BY""",
            parameters=[
                ToolParameter(
                    name="query_type",
                    type="string",
                    description="Type of query: 'aggregate', 'filter', 'trend', 'compare'",
                    required=True,
                    enum=["aggregate", "filter", "trend", "compare"],
                ),
                ToolParameter(
                    name="metrics",
                    type="array",
                    description="Metrics to calculate (e.g., ['total_bookings', 'portfolio_value', 'avg_price', 'cancellation_rate', 'avg_realization'])",
                    required=False,
                ),
                ToolParameter(
                    name="group_by",
                    type="array",
                    description="Fields to group by (e.g., ['development', 'unit_type', 'lead_source'])",
                    required=False,
                ),
                ToolParameter(
                    name="filters",
                    type="object",
                    description="Filter conditions as key-value pairs (e.g., {'development': 'DAMAC Bay', 'booking_status': 'Booked'})",
                    required=False,
                ),
                ToolParameter(
                    name="time_period",
                    type="object",
                    description="Time range filter (e.g., {'start': '2024-01-01', 'end': '2024-12-31'})",
                    required=False,
                ),
                ToolParameter(
                    name="order_by",
                    type="string",
                    description="Field to order results by",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum number of results to return",
                    required=False,
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute a real estate data query."""
        query_type = kwargs.get("query_type", "aggregate")
        metrics = kwargs.get("metrics", [])
        group_by = kwargs.get("group_by", [])
        filters = kwargs.get("filters", {})
        time_period = kwargs.get("time_period", {})
        order_by = kwargs.get("order_by")
        limit = kwargs.get("limit", 100)

        try:
            # Build and execute query against the data source
            # This would connect to your actual database
            result = await self._execute_query(
                query_type=query_type,
                metrics=metrics,
                group_by=group_by,
                filters=filters,
                time_period=time_period,
                order_by=order_by,
                limit=limit,
            )

            return ToolResult(
                success=True,
                output={
                    "data": result,
                    "query_type": query_type,
                    "filters_applied": filters,
                    "records_returned": len(result) if isinstance(result, list) else 1,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Query failed: {str(e)}",
            )

    async def _execute_query(
        self,
        query_type: str,
        metrics: list,
        group_by: list,
        filters: dict,
        time_period: dict,
        order_by: str | None,
        limit: int,
    ) -> dict | list:
        """Execute the actual database query.

        Uses the RealEstateDataService for data access.
        """
        from pathlib import Path

        from src.services.real_estate_data_service import get_real_estate_service, initialize_real_estate_service

        service = get_real_estate_service()

        # Auto-load CSV if not already loaded
        if service._df is None:
            csv_path = Path("/Users/mahak/arada-ai/records_real_estate.csv")
            if csv_path.exists():
                await service.load_csv(csv_path)

        # Portfolio summary query
        if query_type == "aggregate" and not group_by:
            return await service.get_portfolio_summary()

        # Grouped query
        if query_type == "aggregate" and group_by:
            return await service.get_metrics_by_entity(
                group_by=group_by[0] if group_by else "development",
                filters=filters,
            )

        # Trend query
        if query_type == "trend":
            metric = metrics[0] if metrics else "bookings"
            return await service.get_trend_data(
                metric=metric,
                time_granularity="month",
                filters=filters,
            )

        # Filter query
        if query_type == "filter":
            return await service.get_filtered_records(
                filters=filters,
                order_by=order_by,
                limit=limit,
            )

        # Compare query
        if query_type == "compare":
            entity_type = group_by[0] if group_by else "development"
            entities = filters.get(entity_type, []) if filters else []
            return await service.get_comparison_data(
                entity_type=entity_type,
                entities=entities if isinstance(entities, list) else [entities],
                metrics=metrics,
            )

        return {"message": "Query executed successfully"}
