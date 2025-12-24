"""Arada Real Estate SQL MCP Server.

Provides MCP tools for querying real estate bookings data:
- get_schema: Get database schema and column descriptions
- execute_sql: Execute SQL queries on the bookings table
- get_portfolio_summary: Get high-level portfolio metrics

No credentials required - connects to local PostgreSQL.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Add parent directory for base import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseMCPServer, tool


# Database connection
DATABASE_URL = os.getenv(
    "ARADA_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql://magure:magure_dev_password@localhost:5432/magure_db")
)


class AradaSQLServer(BaseMCPServer):
    """MCP Server for Arada Real Estate SQL queries."""

    def __init__(self):
        super().__init__(
            name="arada-sql",
            version="1.0.0",
            description="Arada Real Estate Analytics SQL Server - Query booking data for insights",
        )

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    def _format_results(self, rows, max_rows: int = 100) -> str:
        """Format query results as readable text."""
        if not rows:
            return "No results found."

        # Limit rows
        truncated = len(rows) > max_rows
        rows = rows[:max_rows]

        # Convert to list of dicts
        results = [dict(row) for row in rows]

        output = json.dumps(results, indent=2, default=str)

        if truncated:
            output += f"\n\n... (showing first {max_rows} rows, more results exist)"

        return output

    @tool(
        name="get_schema",
        description="""Get the database schema with all columns, their types, and descriptions.

Use this FIRST to understand what data is available before writing queries.
Returns column names, types, and what each column means.""",
        input_schema={
            "type": "object",
            "properties": {},
        },
    )
    async def get_schema(self, credentials: Dict[str, str] = None) -> Dict[str, Any]:
        """Get database schema."""
        schema = """
DATABASE: Arada Real Estate Bookings
TABLE: bookings
RECORDS: 1,000 booking transactions (Aug 2021 - Dec 2025)
TOTAL PORTFOLIO VALUE: ~AED 5.37 Billion

COLUMNS:
========

LOCATION:
- development (VARCHAR): Master development name
  Values: DAMAC Bay, DAMAC Hills, DAMAC Lagoons, Downtown Dubai, Dubai Hills Estate, Emaar Beachfront
- cluster (VARCHAR): Cluster/sub-area within development
  Values: Waterfront, Golf Greens, Venice, Central Park, Marina Vista, Opera District, etc.
- building (VARCHAR): Building name

UNIT DETAILS:
- unit_id (VARCHAR): Unique unit identifier (e.g., U-754)
- unit_type (VARCHAR): Type of unit
  Values: Studio, 1BR, 2BR, 3BR, Townhouse, Villa
- area_sqft (DECIMAL): Unit size in square feet

PRICING:
- selling_price (DECIMAL): Original selling price in AED
- discount_amount (DECIMAL): Discount amount in AED
- discount_percent (DECIMAL): Discount percentage (0-10%)
- net_sale_value (DECIMAL): Final sale value after discount (AED)

PAYMENT TERMS:
- dp_percent (VARCHAR): Down payment tier
  Values: '10%', '20%', '30%'
- dp_balance (DECIMAL): Remaining down payment balance
- dp_received (DECIMAL): Down payment amount received

COLLECTIONS:
- total_received (DECIMAL): Total amount received (realized + PDCs)
- total_realized (DECIMAL): Actual cash collected
- realization_percent (DECIMAL): Percentage of value collected (0-100)
- pdcs_total (DECIMAL): Post-dated cheques total

DATES:
- booking_date (DATE): Date of booking (YYYY-MM-DD format)
- booking_month (VARCHAR): Month name of booking
- ageing_days (INTEGER): Days since booking
- handover_date (DATE): Expected handover date

STATUS:
- booking_status (VARCHAR): Current booking status
  Values: Booked, Cancelled
- unit_status (VARCHAR): Unit availability status
- stage (VARCHAR): Deal stage
  Values: Booked, Registered, Opportunity

SALES ATTRIBUTION:
- deal_type (VARCHAR): Type of deal
  Values: Direct, Broker
- lead_source (VARCHAR): How the lead came
  Values: Event, Digital, Broker Network, Direct
- lead_sub_source (VARCHAR): Detailed lead source
- sales_executive (VARCHAR): Sales person name
- sales_manager (VARCHAR): Manager name
- sales_vp (VARCHAR): VP name
- broker_name (VARCHAR): Broker company if applicable

CUSTOMER:
- nationality (VARCHAR): Primary buyer nationality (UK, India, China, UAE, Russia, etc.)
- nationality_2 (VARCHAR): Secondary buyer nationality
- customer_code (VARCHAR): Customer identifier

USEFUL QUERY PATTERNS:
=====================

1. Cancellation rate:
   AVG(CASE WHEN booking_status = 'Cancelled' THEN 1 ELSE 0 END) * 100

2. Group by development:
   GROUP BY development ORDER BY COUNT(*) DESC

3. Time trends:
   DATE_TRUNC('month', booking_date) as month

4. Filter by status:
   WHERE booking_status = 'Booked'  -- Active bookings
   WHERE booking_status = 'Cancelled'  -- Cancelled bookings
"""
        return {"schema": schema}

    @tool(
        name="execute_sql",
        description="""Execute a SQL query on the real estate bookings database.

IMPORTANT:
- Table name is 'bookings'
- Use get_schema first to see available columns
- Always include meaningful column aliases
- Limit results if expecting many rows

EXAMPLES:
- SELECT development, COUNT(*) as total_bookings FROM bookings GROUP BY development
- SELECT AVG(realization_percent) as avg_realization FROM bookings WHERE development = 'DAMAC Bay'
- SELECT lead_source, AVG(CASE WHEN booking_status='Cancelled' THEN 1 ELSE 0 END)*100 as cancel_rate FROM bookings GROUP BY lead_source""",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute (SELECT only)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum rows to return (default 100)",
                    "default": 100,
                },
            },
            "required": ["query"],
        },
    )
    async def execute_sql(
        self,
        query: str,
        limit: int = 100,
        credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Execute SQL query."""
        # Basic safety check - only allow SELECT
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            return {
                "error": "Only SELECT queries are allowed",
                "query": query,
            }

        # Prevent dangerous operations
        dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
        for word in dangerous:
            if word in query_upper:
                return {
                    "error": f"Query contains forbidden keyword: {word}",
                    "query": query,
                }

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Add LIMIT if not present
            if "LIMIT" not in query_upper:
                query = f"{query.rstrip(';')} LIMIT {limit}"

            cur.execute(query)
            rows = cur.fetchall()

            cur.close()
            conn.close()

            return {
                "success": True,
                "row_count": len(rows),
                "query": query,
                "results": self._format_results(rows, max_rows=limit),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
            }

    @tool(
        name="get_portfolio_summary",
        description="""Get a high-level summary of the entire real estate portfolio.

Returns:
- Total bookings and portfolio value
- Breakdown by development
- Key metrics (cancellation rate, realization, discounts)
- Top performing and underperforming segments

Use this for overview questions or to start analysis.""",
        input_schema={
            "type": "object",
            "properties": {},
        },
    )
    async def get_portfolio_summary(
        self,
        credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Get portfolio summary."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Overall metrics
            cur.execute("""
                SELECT
                    COUNT(*) as total_bookings,
                    ROUND(SUM(net_sale_value) / 1000000000, 2) as portfolio_value_billions,
                    ROUND(AVG(selling_price) / 1000000, 2) as avg_price_millions,
                    ROUND(AVG(CASE WHEN booking_status = 'Cancelled' THEN 1 ELSE 0 END) * 100, 1) as cancellation_rate,
                    ROUND(AVG(realization_percent), 1) as avg_realization,
                    ROUND(AVG(discount_percent), 1) as avg_discount
                FROM bookings
            """)
            overall = dict(cur.fetchone())

            # By development
            cur.execute("""
                SELECT
                    development,
                    COUNT(*) as bookings,
                    ROUND(SUM(net_sale_value) / 1000000, 0) as value_millions,
                    ROUND(AVG(selling_price) / 1000000, 2) as avg_price_millions,
                    ROUND(AVG(CASE WHEN booking_status = 'Cancelled' THEN 1 ELSE 0 END) * 100, 1) as cancel_rate,
                    ROUND(AVG(realization_percent), 1) as realization
                FROM bookings
                GROUP BY development
                ORDER BY bookings DESC
            """)
            by_development = [dict(row) for row in cur.fetchall()]

            # By unit type
            cur.execute("""
                SELECT
                    unit_type,
                    COUNT(*) as bookings,
                    ROUND(AVG(selling_price) / 1000000, 2) as avg_price_millions
                FROM bookings
                GROUP BY unit_type
                ORDER BY bookings DESC
            """)
            by_unit_type = [dict(row) for row in cur.fetchall()]

            # By lead source
            cur.execute("""
                SELECT
                    lead_source,
                    COUNT(*) as bookings,
                    ROUND(AVG(CASE WHEN booking_status = 'Cancelled' THEN 1 ELSE 0 END) * 100, 1) as cancel_rate
                FROM bookings
                GROUP BY lead_source
                ORDER BY bookings DESC
            """)
            by_lead_source = [dict(row) for row in cur.fetchall()]

            cur.close()
            conn.close()

            summary = {
                "portfolio_overview": overall,
                "by_development": by_development,
                "by_unit_type": by_unit_type,
                "by_lead_source": by_lead_source,
            }

            return {
                "success": True,
                "summary": json.dumps(summary, indent=2, default=str),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Create server instance
server = AradaSQLServer()
app = server.app

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8002)
