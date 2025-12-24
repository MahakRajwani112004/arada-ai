"""Import real estate CSV data into PostgreSQL.

This script:
1. Reads the CSV file
2. Maps columns to database schema
3. Cleans and transforms data
4. Inserts into PostgreSQL

Usage:
    python import_data.py --csv /path/to/records_real_estate.csv --db postgresql://user:pass@localhost:5432/arada
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Optional

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


# Column mapping: CSV column name -> Database column name
COLUMN_MAPPING = {
    "Master Development": "development",
    "Cluster Name": "cluster",
    "Building Name": "building",
    "Unit": "unit_id",
    "Unit Type": "unit_type",
    "Total Saleable Area (Sqft)": "area_sqft",
    "Selling Price": "selling_price",
    "Discount Amount": "discount_amount",
    "Discount %": "discount_percent",
    "Net Sale Value (AED)": "net_sale_value",
    "DP (%)": "dp_percent",
    "DP Balance": "dp_balance",
    "DP Received": "dp_received",
    "Total Received (Realized + PDC)": "total_received",
    "Total Amount Realized": "total_realized",
    "Total Realized %": "realization_percent",
    "PDCs Total Amount": "pdcs_total",
    "Booking Date": "booking_date",
    "Booking Month": "booking_month",
    "Ageing": "ageing_days",
    "Handover Date": "handover_date",
    "Booking Status": "booking_status",
    "Unit Status": "unit_status",
    "Stage": "stage",
    "Deal Type": "deal_type",
    "Lead Source": "lead_source",
    "Lead Sub Source": "lead_sub_source",
    "Sales Executive": "sales_executive",
    "Sales Manager": "sales_manager",
    "Sales VP": "sales_vp",
    "Broker 1: Purchaser Name": "broker_name",
    "Customer Code": "customer_code",
    "P1 Nationality": "nationality",
    "P2 Nationality": "nationality_2",
}


def parse_date(date_str: str) -> Optional[str]:
    """Parse date from DD/MM/YYYY format to YYYY-MM-DD."""
    if pd.isna(date_str) or not date_str:
        return None
    try:
        # Try DD/MM/YYYY format
        dt = datetime.strptime(str(date_str), "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Try other formats
            dt = datetime.strptime(str(date_str), "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None


def clean_numeric(value) -> Optional[float]:
    """Clean numeric value (remove commas, handle nulls)."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        # Remove commas and convert
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def clean_percentage(value) -> Optional[float]:
    """Clean percentage value."""
    if pd.isna(value):
        return None
    try:
        val = float(str(value).replace("%", "").replace(",", ""))
        return val
    except (ValueError, TypeError):
        return None


def import_csv_to_postgres(csv_path: str, database_url: str):
    """Import CSV data into PostgreSQL."""

    print(f"Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records")

    # Show available columns
    print(f"\nCSV columns found: {len(df.columns)}")

    # Prepare data for insertion
    records = []

    for idx, row in df.iterrows():
        record = {
            "development": row.get("Master Development"),
            "cluster": row.get("Cluster Name"),
            "building": row.get("Building Name"),
            "unit_id": row.get("Unit"),
            "unit_type": row.get("Unit Type"),
            "area_sqft": clean_numeric(row.get("Total Saleable Area (Sqft)")),
            "selling_price": clean_numeric(row.get("Selling Price")),
            "discount_amount": clean_numeric(row.get("Discount Amount")),
            "discount_percent": clean_percentage(row.get("Discount %")),
            "net_sale_value": clean_numeric(row.get("Net Sale Value (AED)")),
            "dp_percent": str(row.get("DP (%)", "")).replace(".0", "") + "%" if pd.notna(row.get("DP (%)")) else None,
            "dp_balance": clean_numeric(row.get("DP Balance")),
            "dp_received": clean_numeric(row.get("DP Received")),
            "total_received": clean_numeric(row.get("Total Received (Realized + PDC)")),
            "total_realized": clean_numeric(row.get("Total Amount Realized")),
            "realization_percent": clean_percentage(row.get("Total Realized %")),
            "pdcs_total": clean_numeric(row.get("PDCs Total Amount")),
            "booking_date": parse_date(row.get("Booking Date")),
            "booking_month": row.get("Booking Month"),
            "ageing_days": int(row.get("Ageing")) if pd.notna(row.get("Ageing")) else None,
            "handover_date": parse_date(row.get("Handover Date")),
            "booking_status": row.get("Booking Status"),
            "unit_status": row.get("Unit Status"),
            "stage": row.get("Stage"),
            "deal_type": row.get("Deal Type"),
            "lead_source": row.get("Lead Source"),
            "lead_sub_source": row.get("Lead Sub Source"),
            "sales_executive": row.get("Sales Executive"),
            "sales_manager": row.get("Sales Manager"),
            "sales_vp": row.get("Sales VP"),
            "broker_name": row.get("Broker 1: Purchaser Name"),
            "customer_code": row.get("Customer Code"),
            "nationality": row.get("P1 Nationality"),
            "nationality_2": row.get("P2 Nationality"),
        }
        records.append(record)

    print(f"\nPrepared {len(records)} records for insertion")

    # Connect to PostgreSQL
    print(f"\nConnecting to database...")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    # Run schema
    print("Creating table...")
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        cur.execute(f.read())
    conn.commit()

    # Insert data
    print("Inserting data...")

    columns = list(records[0].keys())
    insert_sql = f"""
        INSERT INTO bookings ({", ".join(columns)})
        VALUES %s
    """

    values = [tuple(r[col] for col in columns) for r in records]

    execute_values(cur, insert_sql, values)
    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM bookings")
    count = cur.fetchone()[0]
    print(f"\nInserted {count} records successfully!")

    # Show sample
    print("\nSample data:")
    cur.execute("""
        SELECT development, COUNT(*) as bookings,
               ROUND(AVG(selling_price)::numeric, 0) as avg_price,
               ROUND(AVG(CASE WHEN booking_status = 'Cancelled' THEN 1 ELSE 0 END) * 100, 1) as cancel_rate
        FROM bookings
        GROUP BY development
        ORDER BY bookings DESC
    """)

    print(f"\n{'Development':<25} {'Bookings':>10} {'Avg Price':>15} {'Cancel %':>10}")
    print("-" * 65)
    for row in cur.fetchall():
        print(f"{row[0]:<25} {row[1]:>10} {row[2]:>15,.0f} {row[3]:>10}%")

    cur.close()
    conn.close()

    print("\nImport complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import real estate CSV to PostgreSQL")
    parser.add_argument(
        "--csv",
        default="/Users/mahak/arada-ai/records_real_estate.csv",
        help="Path to CSV file",
    )
    parser.add_argument(
        "--db",
        default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/arada"),
        help="PostgreSQL connection URL",
    )

    args = parser.parse_args()

    import_csv_to_postgres(args.csv, args.db)
