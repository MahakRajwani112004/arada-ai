"""API schemas for CSV-SQL operations."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== Column Schema ====================


class ColumnInfo(BaseModel):
    """Information about a table column."""

    name: str
    type: str
    original: Optional[str] = None


# ==================== Table Schemas ====================


class CSVTableResponse(BaseModel):
    """Response containing CSV table details."""

    table_name: str
    original_filename: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: Optional[List[ColumnInfo]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CSVTableListResponse(BaseModel):
    """Response containing list of CSV tables."""

    tables: List[CSVTableResponse]
    total: int


# ==================== Upload Schemas ====================


class UploadCSVRequest(BaseModel):
    """Request to upload a CSV file."""

    table_name: str = Field(..., min_length=1, max_length=100, description="Name for the table")
    if_exists: str = Field(
        "fail",
        pattern="^(fail|replace|append)$",
        description="What to do if table exists: fail, replace, or append",
    )


class UploadCSVResponse(BaseModel):
    """Response after uploading a CSV file."""

    success: bool
    table_name: Optional[str] = None
    schema: Optional[str] = None
    full_path: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: Optional[List[ColumnInfo]] = None
    message: Optional[str] = None
    error: Optional[str] = None


# ==================== Query Schemas ====================


class ExecuteSQLRequest(BaseModel):
    """Request to execute a SQL query."""

    query: str = Field(..., min_length=1, description="SQL query to execute")
    limit: int = Field(100, ge=1, le=10000, description="Maximum rows to return")


class ExecuteSQLResponse(BaseModel):
    """Response after executing a SQL query."""

    success: bool
    query_type: Optional[str] = None
    row_count: Optional[int] = None
    affected_rows: Optional[int] = None
    results: Optional[str] = None
    query: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


# ==================== Schema Response ====================


class TableSchemaResponse(BaseModel):
    """Response containing table schema."""

    success: bool
    table_name: Optional[str] = None
    schema: Optional[str] = None
    full_path: Optional[str] = None
    columns: Optional[List[ColumnInfo]] = None
    row_count: Optional[int] = None
    original_filename: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


# ==================== Sample Data Response ====================


class SampleDataResponse(BaseModel):
    """Response containing sample data from a table."""

    success: bool
    table_name: Optional[str] = None
    sample: Optional[str] = None
    row_count: Optional[int] = None
    error: Optional[str] = None


# ==================== Delete Response ====================


class DeleteTableResponse(BaseModel):
    """Response after deleting a table."""

    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
