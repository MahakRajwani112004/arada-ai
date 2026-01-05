"""CSV-to-SQL MCP Server.

A generic MCP server that allows users to:
- Upload CSV files and create PostgreSQL tables
- Query tables with full SQL access (SELECT, INSERT, UPDATE, DELETE)
- List and manage uploaded tables

Each user's tables are isolated by user_id prefix.
"""

import base64
import io
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Add parent directory for base import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseMCPServer, tool


# Database connection
DATABASE_URL = os.getenv(
    "CSV_SQL_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql://magure:magure_dev_password@localhost:5432/magure_db")
)

# Schema for CSV tables
CSV_SCHEMA = "csv_data"

# Limits
MAX_CSV_SIZE_MB = 50
MAX_ROWS = 1_000_000
MAX_COLUMNS = 500


def sanitize_table_name(name: str) -> str:
    """Sanitize table name to prevent SQL injection."""
    # Remove file extension
    name = os.path.splitext(name)[0]
    # Replace non-alphanumeric with underscore
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Lowercase
    name = name.lower()
    # Truncate to reasonable length
    name = name[:50]
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = 'csv_' + name
    return name or 'unnamed'


def infer_sql_type(series: pd.Series) -> str:
    """Infer PostgreSQL type from pandas Series."""
    # Drop nulls for inference
    non_null = series.dropna()
    if len(non_null) == 0:
        return "TEXT"

    # Check pandas dtype first
    dtype = series.dtype

    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    elif pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"

    # Try to infer from string values
    sample = non_null.head(100).astype(str)

    # Check for integers
    try:
        sample.astype(int)
        return "BIGINT"
    except (ValueError, TypeError):
        pass

    # Check for floats
    try:
        sample.astype(float)
        return "DOUBLE PRECISION"
    except (ValueError, TypeError):
        pass

    # Check for dates (YYYY-MM-DD)
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if sample.str.match(date_pattern).all():
        return "DATE"

    # Check for datetimes
    datetime_pattern = r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'
    if sample.str.match(datetime_pattern).all():
        return "TIMESTAMP"

    # Check for booleans
    bool_values = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f'}
    if sample.str.lower().isin(bool_values).all():
        return "BOOLEAN"

    # Default to TEXT
    return "TEXT"


def sanitize_column_name(name: str) -> str:
    """Sanitize column name."""
    # Replace non-alphanumeric with underscore
    name = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Lowercase
    name = name.lower()
    # Truncate
    name = name[:63]
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = 'col_' + name
    return name or 'column'


class CSVSQLServer(BaseMCPServer):
    """MCP Server for CSV to SQL operations."""

    def __init__(self):
        super().__init__(
            name="csv-sql",
            version="1.0.0",
            description="CSV to SQL Server - Upload CSV files and query them with SQL",
        )
        self._ensure_schema()

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    def _ensure_schema(self):
        """Ensure the csv_data schema exists."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {CSV_SCHEMA}")

            # Create metadata table
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {CSV_SCHEMA}._metadata (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) NOT NULL,
                    table_name VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255),
                    row_count INTEGER,
                    column_count INTEGER,
                    columns JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, table_name)
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not ensure schema: {e}")

    def _get_full_table_name(self, user_id: str, table_name: str) -> str:
        """Get full table name with user prefix."""
        user_prefix = user_id[:8] if user_id else "default"
        return f"csv_{user_prefix}_{sanitize_table_name(table_name)}"

    def _format_results(self, rows: List[Dict], max_rows: int = 100) -> str:
        """Format query results as JSON."""
        if not rows:
            return "No results found."

        truncated = len(rows) > max_rows
        rows = rows[:max_rows]
        results = [dict(row) for row in rows]
        output = json.dumps(results, indent=2, default=str)

        if truncated:
            output += f"\n\n... (showing first {max_rows} rows, more results exist)"

        return output

    @tool(
        name="upload_csv",
        description="""Upload a CSV file and create a PostgreSQL table from it.

The CSV data should be provided as a base64-encoded string.
A table will be created with automatically inferred column types.

Returns the created table name and schema.

IMPORTANT: Table names are automatically sanitized and prefixed with user ID.""",
        input_schema={
            "type": "object",
            "properties": {
                "csv_data": {
                    "type": "string",
                    "description": "Base64-encoded CSV file content",
                },
                "table_name": {
                    "type": "string",
                    "description": "Name for the table (will be sanitized)",
                },
                "if_exists": {
                    "type": "string",
                    "enum": ["fail", "replace", "append"],
                    "description": "What to do if table exists: fail, replace, or append",
                    "default": "fail",
                },
            },
            "required": ["csv_data", "table_name"],
        },
        credential_headers=["X-User-Id"],
    )
    async def upload_csv(
        self,
        csv_data: str,
        table_name: str,
        if_exists: str = "fail",
        credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Upload CSV and create table."""
        user_id = credentials.get("user_id", "default") if credentials else "default"

        try:
            # Decode base64 CSV data
            try:
                csv_bytes = base64.b64decode(csv_data)
            except Exception:
                return {"success": False, "error": "Invalid base64 encoding"}

            # Check size
            size_mb = len(csv_bytes) / (1024 * 1024)
            if size_mb > MAX_CSV_SIZE_MB:
                return {
                    "success": False,
                    "error": f"CSV file too large ({size_mb:.1f}MB). Max size is {MAX_CSV_SIZE_MB}MB",
                }

            # Read CSV with pandas
            try:
                df = pd.read_csv(io.BytesIO(csv_bytes))
            except Exception as e:
                return {"success": False, "error": f"Failed to parse CSV: {str(e)}"}

            # Check limits
            if len(df) > MAX_ROWS:
                return {
                    "success": False,
                    "error": f"CSV has {len(df)} rows. Max is {MAX_ROWS}",
                }
            if len(df.columns) > MAX_COLUMNS:
                return {
                    "success": False,
                    "error": f"CSV has {len(df.columns)} columns. Max is {MAX_COLUMNS}",
                }

            # Sanitize column names
            original_columns = list(df.columns)
            df.columns = [sanitize_column_name(col) for col in df.columns]

            # Handle duplicate column names
            seen = {}
            new_columns = []
            for col in df.columns:
                if col in seen:
                    seen[col] += 1
                    new_columns.append(f"{col}_{seen[col]}")
                else:
                    seen[col] = 0
                    new_columns.append(col)
            df.columns = new_columns

            # Infer types
            column_types = {}
            for col in df.columns:
                column_types[col] = infer_sql_type(df[col])

            # Get full table name
            full_table_name = self._get_full_table_name(user_id, table_name)

            conn = self._get_connection()
            cur = conn.cursor()

            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                )
            """, (CSV_SCHEMA, full_table_name))
            table_exists = cur.fetchone()['exists']

            if table_exists:
                if if_exists == "fail":
                    cur.close()
                    conn.close()
                    return {
                        "success": False,
                        "error": f"Table '{full_table_name}' already exists. Use if_exists='replace' or 'append'",
                    }
                elif if_exists == "replace":
                    cur.execute(
                        sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                            sql.Identifier(CSV_SCHEMA),
                            sql.Identifier(full_table_name)
                        )
                    )

            # Create table if needed
            if not table_exists or if_exists == "replace":
                columns_sql = ", ".join([
                    f'"{col}" {dtype}' for col, dtype in column_types.items()
                ])
                cur.execute(
                    sql.SQL("CREATE TABLE {}.{} ({})").format(
                        sql.Identifier(CSV_SCHEMA),
                        sql.Identifier(full_table_name),
                        sql.SQL(columns_sql)
                    )
                )

            # Insert data
            if len(df) > 0:
                cols = ", ".join([f'"{col}"' for col in df.columns])
                placeholders = ", ".join(["%s"] * len(df.columns))
                insert_sql = f'INSERT INTO {CSV_SCHEMA}."{full_table_name}" ({cols}) VALUES ({placeholders})'

                # Convert DataFrame to list of tuples
                values = [tuple(None if pd.isna(v) else v for v in row) for row in df.values]

                # Batch insert
                from psycopg2.extras import execute_batch
                execute_batch(cur, insert_sql, values, page_size=1000)

            # Update metadata
            columns_info = [
                {"name": col, "type": column_types[col], "original": orig}
                for col, orig in zip(df.columns, original_columns)
            ]

            cur.execute(f"""
                INSERT INTO {CSV_SCHEMA}._metadata
                (user_id, table_name, original_filename, row_count, column_count, columns)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, table_name)
                DO UPDATE SET
                    row_count = EXCLUDED.row_count,
                    column_count = EXCLUDED.column_count,
                    columns = EXCLUDED.columns,
                    updated_at = NOW()
            """, (user_id, full_table_name, table_name, len(df), len(df.columns), json.dumps(columns_info)))

            conn.commit()
            cur.close()
            conn.close()

            return {
                "success": True,
                "table_name": full_table_name,
                "schema": CSV_SCHEMA,
                "full_path": f"{CSV_SCHEMA}.{full_table_name}",
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": columns_info,
                "message": f"Successfully created table '{full_table_name}' with {len(df)} rows",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(
        name="list_tables",
        description="""List all CSV tables for the current user.

Returns table names, row counts, and creation dates.""",
        input_schema={
            "type": "object",
            "properties": {},
        },
        credential_headers=["X-User-Id"],
    )
    async def list_tables(
        self,
        credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """List user's CSV tables."""
        user_id = credentials.get("user_id", "default") if credentials else "default"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute(f"""
                SELECT
                    table_name,
                    original_filename,
                    row_count,
                    column_count,
                    columns,
                    created_at,
                    updated_at
                FROM {CSV_SCHEMA}._metadata
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))

            tables = [dict(row) for row in cur.fetchall()]

            cur.close()
            conn.close()

            return {
                "success": True,
                "tables": tables,
                "count": len(tables),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(
        name="get_table_schema",
        description="""Get the schema (columns and types) for a specific table.

Use this to understand the table structure before writing queries.""",
        input_schema={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table",
                },
            },
            "required": ["table_name"],
        },
        credential_headers=["X-User-Id"],
    )
    async def get_table_schema(
        self,
        table_name: str,
        credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Get table schema."""
        user_id = credentials.get("user_id", "default") if credentials else "default"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Get from metadata
            cur.execute(f"""
                SELECT columns, row_count, original_filename, created_at
                FROM {CSV_SCHEMA}._metadata
                WHERE user_id = %s AND table_name = %s
            """, (user_id, table_name))

            result = cur.fetchone()

            if not result:
                # Try direct table lookup
                cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (CSV_SCHEMA, table_name))

                columns = [{"name": row["column_name"], "type": row["data_type"]} for row in cur.fetchall()]

                if not columns:
                    cur.close()
                    conn.close()
                    return {"success": False, "error": f"Table '{table_name}' not found"}

                cur.close()
                conn.close()

                return {
                    "success": True,
                    "table_name": table_name,
                    "schema": CSV_SCHEMA,
                    "columns": columns,
                }

            cur.close()
            conn.close()

            return {
                "success": True,
                "table_name": table_name,
                "schema": CSV_SCHEMA,
                "full_path": f"{CSV_SCHEMA}.{table_name}",
                "columns": result["columns"],
                "row_count": result["row_count"],
                "original_filename": result["original_filename"],
                "created_at": str(result["created_at"]),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(
        name="execute_sql",
        description="""Execute a SQL query on the CSV tables.

FULL SQL ACCESS: SELECT, INSERT, UPDATE, DELETE are all allowed.

IMPORTANT:
- Tables are in the 'csv_data' schema
- Use list_tables to see available tables
- Use get_table_schema to see column names and types
- Always use the full table path: csv_data.table_name

EXAMPLES:
- SELECT * FROM csv_data.csv_abc123_sales LIMIT 10
- SELECT category, SUM(amount) FROM csv_data.csv_abc123_sales GROUP BY category
- UPDATE csv_data.csv_abc123_sales SET status = 'processed' WHERE id = 1
- DELETE FROM csv_data.csv_abc123_sales WHERE status = 'invalid'""",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum rows to return for SELECT queries (default 100)",
                    "default": 100,
                },
            },
            "required": ["query"],
        },
        credential_headers=["X-User-Id"],
    )
    async def execute_sql(
        self,
        query: str,
        limit: int = 100,
        credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Execute SQL query."""
        user_id = credentials.get("user_id", "default") if credentials else "default"

        # Basic validation - ensure they're accessing csv_data schema
        query_upper = query.strip().upper()

        # Prevent schema operations
        dangerous_ops = ["CREATE SCHEMA", "DROP SCHEMA", "ALTER SCHEMA"]
        for op in dangerous_ops:
            if op in query_upper:
                return {"success": False, "error": f"Operation not allowed: {op}"}

        # Prevent access to metadata table directly (allow read)
        if "_METADATA" in query_upper and not query_upper.startswith("SELECT"):
            return {"success": False, "error": "Cannot modify _metadata table"}

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Add search path for convenience
            cur.execute(f"SET search_path TO {CSV_SCHEMA}, public")

            # Determine query type
            is_select = query_upper.startswith("SELECT") or query_upper.startswith("WITH")

            if is_select:
                # Add LIMIT if not present
                if "LIMIT" not in query_upper:
                    query = f"{query.rstrip(';')} LIMIT {limit}"

                cur.execute(query)
                rows = cur.fetchall()

                conn.close()

                return {
                    "success": True,
                    "query_type": "SELECT",
                    "row_count": len(rows),
                    "query": query,
                    "results": self._format_results(rows, max_rows=limit),
                }
            else:
                # INSERT, UPDATE, DELETE
                cur.execute(query)
                affected_rows = cur.rowcount
                conn.commit()

                cur.close()
                conn.close()

                return {
                    "success": True,
                    "query_type": query_upper.split()[0],
                    "affected_rows": affected_rows,
                    "query": query,
                    "message": f"Query executed successfully. {affected_rows} rows affected.",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
            }

    @tool(
        name="delete_table",
        description="""Delete a CSV table.

WARNING: This permanently deletes the table and all its data.""",
        input_schema={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to delete",
                },
            },
            "required": ["table_name"],
        },
        credential_headers=["X-User-Id"],
    )
    async def delete_table(
        self,
        table_name: str,
        credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Delete a table."""
        user_id = credentials.get("user_id", "default") if credentials else "default"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Verify ownership
            cur.execute(f"""
                SELECT 1 FROM {CSV_SCHEMA}._metadata
                WHERE user_id = %s AND table_name = %s
            """, (user_id, table_name))

            if not cur.fetchone():
                cur.close()
                conn.close()
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found or not owned by you",
                }

            # Drop table
            cur.execute(
                sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                    sql.Identifier(CSV_SCHEMA),
                    sql.Identifier(table_name)
                )
            )

            # Remove metadata
            cur.execute(f"""
                DELETE FROM {CSV_SCHEMA}._metadata
                WHERE user_id = %s AND table_name = %s
            """, (user_id, table_name))

            conn.commit()
            cur.close()
            conn.close()

            return {
                "success": True,
                "message": f"Table '{table_name}' deleted successfully",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(
        name="get_sample_data",
        description="""Get sample rows from a table.

Useful for previewing table contents before writing queries.""",
        input_schema={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table",
                },
                "rows": {
                    "type": "integer",
                    "description": "Number of sample rows to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["table_name"],
        },
        credential_headers=["X-User-Id"],
    )
    async def get_sample_data(
        self,
        table_name: str,
        rows: int = 5,
        credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Get sample data from table."""
        user_id = credentials.get("user_id", "default") if credentials else "default"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Set search path
            cur.execute(f"SET search_path TO {CSV_SCHEMA}, public")

            # Get sample
            cur.execute(
                sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
                    sql.Identifier(CSV_SCHEMA),
                    sql.Identifier(table_name)
                ),
                (rows,)
            )

            sample = [dict(row) for row in cur.fetchall()]

            cur.close()
            conn.close()

            return {
                "success": True,
                "table_name": table_name,
                "sample": json.dumps(sample, indent=2, default=str),
                "row_count": len(sample),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


# Create server instance
server = CSVSQLServer()
app = server.app

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8003)
