"""Real Estate Data Service for Arada AI Analytics.

This service provides data access layer for the real estate booking data.
It can connect to PostgreSQL, CSV files, or data warehouses.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


class RealEstateDataService:
    """Service for accessing and querying real estate booking data."""

    # Column mapping from CSV to normalized names
    COLUMN_MAPPING = {
        "Unit": "unit_id",
        "Master Development": "development",
        "Cluster Name": "cluster",
        "Unit Type": "unit_type",
        "Total Saleable Area (Sqft)": "area_sqft",
        "Selling Price": "selling_price",
        "Discount %": "discount_percent",
        "Net Sale Value (AED)": "net_sale_value",
        "DP (%)": "dp_tier",
        "Lead Source": "lead_source",
        "Deal Type": "deal_type",
        "Date of Sales Reporting": "booking_date",
        "Stage": "booking_status",
        "P1 Nationality": "nationality",
        "Total Amount Realized": "amount_collected",
        "Total Realized %": "realization_percent",
        "Ageing": "ageing_days",
        "Booking Status": "status",
    }

    def __init__(self, data_source: str = "database"):
        """Initialize the data service.

        Args:
            data_source: One of 'database', 'csv', or 'dataframe'
        """
        self.data_source = data_source
        self._df: pd.DataFrame | None = None

    async def load_csv(self, file_path: str | Path) -> None:
        """Load data from CSV file into memory."""
        df = pd.read_csv(file_path)
        # Rename columns to normalized names
        df = df.rename(columns=self.COLUMN_MAPPING)
        # Parse dates
        if "booking_date" in df.columns:
            df["booking_date"] = pd.to_datetime(df["booking_date"], format="%d/%m/%Y", errors="coerce")
        self._df = df

    async def get_portfolio_summary(self) -> dict:
        """Get high-level portfolio summary metrics."""
        if self._df is not None:
            df = self._df
            # Handle column name variations
            status_col = "status" if "status" in df.columns else "booking_status"
            realization_col = "realization_percent" if "realization_percent" in df.columns else "Total Realized %"
            discount_col = "discount_percent" if "discount_percent" in df.columns else "Discount %"
            net_sale_col = "net_sale_value" if "net_sale_value" in df.columns else "Net Sale Value (AED)"

            return {
                "total_bookings": len(df),
                "portfolio_value": float(df[net_sale_col].sum()) if net_sale_col in df.columns else 0,
                "avg_unit_price": float(df[net_sale_col].mean()) if net_sale_col in df.columns else 0,
                "cancellation_rate": float((df[status_col] == "Cancelled").mean() * 100) if status_col in df.columns else 0,
                "avg_realization": float(df[realization_col].mean()) if realization_col in df.columns else 0,
                "avg_discount": float(df[discount_col].mean()) if discount_col in df.columns else 0,
                "developments": df["development"].nunique() if "development" in df.columns else 0,
                "unit_types": df["unit_type"].nunique() if "unit_type" in df.columns else 0,
            }

        # No data loaded, return empty
        return {
            "total_bookings": 0,
            "portfolio_value": 0,
            "avg_unit_price": 0,
            "cancellation_rate": 0,
            "avg_realization": 0,
            "avg_discount": 0,
            "developments": 0,
            "unit_types": 0,
            "error": "No data loaded. Please load CSV data first.",
        }

    async def get_metrics_by_entity(
        self,
        group_by: str,
        filters: dict | None = None,
    ) -> list[dict]:
        """Get metrics grouped by a specific entity (development, cluster, etc.)."""
        if self._df is not None:
            df = self._df.copy()

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if key in df.columns:
                        df = df[df[key] == value]

            # Group and aggregate
            grouped = df.groupby(group_by).agg(
                total_bookings=("unit_id", "count"),
                portfolio_value=("net_sale_value", "sum"),
                avg_unit_price=("net_sale_value", "mean"),
                cancellation_rate=("booking_status", lambda x: (x == "Cancelled").mean() * 100),
                avg_realization=("realization_percent", "mean"),
                avg_discount=("discount_percent", "mean"),
            ).reset_index()

            return grouped.to_dict("records")

        # Database query fallback
        return []

    async def get_trend_data(
        self,
        metric: str,
        time_granularity: str = "month",
        filters: dict | None = None,
    ) -> list[dict]:
        """Get time-series trend data for a specific metric."""
        if self._df is not None:
            df = self._df.copy()

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if key in df.columns:
                        df = df[df[key] == value]

            # Create time period column
            if time_granularity == "month":
                df["period"] = df["booking_date"].dt.to_period("M")
            elif time_granularity == "quarter":
                df["period"] = df["booking_date"].dt.to_period("Q")
            elif time_granularity == "year":
                df["period"] = df["booking_date"].dt.to_period("Y")

            # Aggregate by period
            if metric == "bookings":
                result = df.groupby("period").size().reset_index(name="value")
            elif metric == "portfolio_value":
                result = df.groupby("period")["net_sale_value"].sum().reset_index(name="value")
            elif metric == "cancellation_rate":
                result = (
                    df.groupby("period")
                    .apply(lambda x: (x["booking_status"] == "Cancelled").mean() * 100)
                    .reset_index(name="value")
                )
            else:
                result = df.groupby("period")[metric].mean().reset_index(name="value")

            result["period"] = result["period"].astype(str)
            return result.to_dict("records")

        return []

    async def get_filtered_records(
        self,
        filters: dict | None = None,
        fields: list | None = None,
        order_by: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get filtered records with optional field selection."""
        if self._df is not None:
            df = self._df.copy()

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if key in df.columns:
                        if isinstance(value, list):
                            df = df[df[key].isin(value)]
                        else:
                            df = df[df[key] == value]

            # Select fields
            if fields:
                df = df[[f for f in fields if f in df.columns]]

            # Order by
            if order_by and order_by in df.columns:
                df = df.sort_values(order_by, ascending=False)

            # Limit
            df = df.head(limit)

            return df.to_dict("records")

        return []

    async def get_comparison_data(
        self,
        entity_type: str,
        entities: list[str],
        metrics: list[str],
    ) -> dict:
        """Get comparison data for multiple entities."""
        results = {}

        for entity in entities:
            filters = {entity_type: entity}
            entity_metrics = await self.get_metrics_by_entity(
                group_by=entity_type,
                filters=filters,
            )
            if entity_metrics:
                results[entity] = entity_metrics[0]

        # Calculate portfolio averages
        portfolio = await self.get_portfolio_summary()
        results["portfolio_average"] = portfolio

        return results

    async def detect_anomalies(
        self,
        metric: str,
        threshold_std: float = 2.0,
    ) -> list[dict]:
        """Detect anomalies in the data based on standard deviation."""
        if self._df is not None:
            df = self._df.copy()

            if metric not in df.columns:
                return []

            mean = df[metric].mean()
            std = df[metric].std()

            anomalies = df[
                (df[metric] > mean + threshold_std * std)
                | (df[metric] < mean - threshold_std * std)
            ]

            return anomalies.to_dict("records")

        return []

    async def get_risk_indicators(self) -> dict:
        """Get portfolio risk indicators."""
        if self._df is not None:
            df = self._df.copy()

            # Collection risk: aged bookings with low realization
            collection_risk = df[
                (df["ageing_days"] > 400)
                & (df["realization_percent"] < 40)
                & (~df["booking_status"].isin(["Handover", "Registered"]))
            ]

            # High discount risk
            discount_risk = df[df["discount_percent"] > 8]

            # Cancellation risk by segment
            cancel_by_source = (
                df.groupby("lead_source")
                .apply(lambda x: (x["booking_status"] == "Cancelled").mean() * 100)
                .to_dict()
            )

            return {
                "collection_risk": {
                    "units_at_risk": len(collection_risk),
                    "value_at_risk": float(collection_risk["net_sale_value"].sum()),
                    "by_development": collection_risk.groupby("development").size().to_dict(),
                },
                "discount_anomalies": {
                    "count": len(discount_risk),
                    "total_discount_given": float(
                        (discount_risk["selling_price"] - discount_risk["net_sale_value"]).sum()
                    ),
                },
                "cancellation_by_source": cancel_by_source,
            }

        return {}


# Global service instance
_service: RealEstateDataService | None = None


def get_real_estate_service() -> RealEstateDataService:
    """Get the global real estate data service instance."""
    global _service
    if _service is None:
        _service = RealEstateDataService()
    return _service


async def initialize_real_estate_service(csv_path: str | None = None) -> RealEstateDataService:
    """Initialize the real estate data service with data source."""
    global _service
    _service = RealEstateDataService()

    if csv_path:
        await _service.load_csv(csv_path)

    return _service
