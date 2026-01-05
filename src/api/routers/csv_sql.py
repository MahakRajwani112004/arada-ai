"""API router for CSV-to-SQL operations.

This router provides endpoints to upload CSV files and convert them to PostgreSQL tables
that can be queried via the CSV-SQL MCP server.
"""
import base64
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from src.api.schemas.csv_sql import (
    ColumnInfo,
    CSVTableListResponse,
    CSVTableResponse,
    DeleteTableResponse,
    ExecuteSQLRequest,
    ExecuteSQLResponse,
    SampleDataResponse,
    TableSchemaResponse,
    UploadCSVResponse,
)
from src.auth.dependencies import CurrentUser
from src.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/csv-sql", tags=["csv-sql"])

# CSV-SQL MCP Server URL
CSV_SQL_SERVER_URL = os.getenv("CSV_SQL_SERVER_URL", "http://localhost:8003")

# Limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


async def _call_mcp_tool(
    tool_name: str,
    arguments: dict,
    user_id: str,
) -> dict:
    """Call a tool on the CSV-SQL MCP server.

    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments
        user_id: User ID for isolation

    Returns:
        Tool result from MCP server
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{CSV_SQL_SERVER_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
            },
            headers={
                "Content-Type": "application/json",
                "X-User-Id": user_id,
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"CSV-SQL server error: {response.text}",
            )

        result = response.json()

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"].get("message", "Unknown error"),
            )

        # Extract result from MCP response
        content = result.get("result", {}).get("content", [])
        if content and len(content) > 0:
            import json
            text = content[0].get("text", "{}")
            return json.loads(text)

        return {}


# ==================== Upload Endpoint ====================


@router.post("/upload", response_model=UploadCSVResponse)
async def upload_csv(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    table_name: str = Form(...),
    if_exists: str = Form("fail"),
) -> UploadCSVResponse:
    """Upload a CSV file and create a PostgreSQL table.

    Args:
        file: CSV file to upload
        table_name: Name for the table (will be sanitized)
        if_exists: What to do if table exists (fail, replace, append)

    Returns:
        Upload result with table info
    """
    logger.info(
        "csv_upload_started",
        filename=file.filename,
        table_name=table_name,
        user_id=current_user.id,
    )

    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported",
        )

    # Validate if_exists parameter
    if if_exists not in ("fail", "replace", "append"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="if_exists must be one of: fail, replace, append",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    # Encode as base64
    csv_data = base64.b64encode(content).decode("utf-8")

    # Call MCP server
    try:
        result = await _call_mcp_tool(
            tool_name="upload_csv",
            arguments={
                "csv_data": csv_data,
                "table_name": table_name,
                "if_exists": if_exists,
            },
            user_id=current_user.id,
        )

        logger.info(
            "csv_upload_completed",
            filename=file.filename,
            table_name=result.get("table_name"),
            row_count=result.get("row_count"),
            user_id=current_user.id,
        )

        # Convert columns to ColumnInfo objects
        columns = None
        if result.get("columns"):
            columns = [
                ColumnInfo(
                    name=col.get("name"),
                    type=col.get("type"),
                    original=col.get("original"),
                )
                for col in result.get("columns", [])
            ]

        return UploadCSVResponse(
            success=result.get("success", False),
            table_name=result.get("table_name"),
            schema=result.get("schema"),
            full_path=result.get("full_path"),
            row_count=result.get("row_count"),
            column_count=result.get("column_count"),
            columns=columns,
            message=result.get("message"),
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "csv_upload_failed",
            filename=file.filename,
            error=str(e),
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload CSV: {str(e)}",
        )


# ==================== List Tables Endpoint ====================


@router.get("/tables", response_model=CSVTableListResponse)
async def list_tables(
    current_user: CurrentUser,
) -> CSVTableListResponse:
    """List all CSV tables for the current user."""
    try:
        result = await _call_mcp_tool(
            tool_name="list_tables",
            arguments={},
            user_id=current_user.id,
        )

        tables = []
        for table in result.get("tables", []):
            columns = None
            if table.get("columns"):
                columns = [
                    ColumnInfo(
                        name=col.get("name"),
                        type=col.get("type"),
                        original=col.get("original"),
                    )
                    for col in table.get("columns", [])
                ]

            tables.append(
                CSVTableResponse(
                    table_name=table.get("table_name"),
                    original_filename=table.get("original_filename"),
                    row_count=table.get("row_count"),
                    column_count=table.get("column_count"),
                    columns=columns,
                    created_at=table.get("created_at"),
                    updated_at=table.get("updated_at"),
                )
            )

        return CSVTableListResponse(
            tables=tables,
            total=len(tables),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_tables_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tables: {str(e)}",
        )


# ==================== Get Table Schema Endpoint ====================


@router.get("/tables/{table_name}/schema", response_model=TableSchemaResponse)
async def get_table_schema(
    table_name: str,
    current_user: CurrentUser,
) -> TableSchemaResponse:
    """Get the schema for a specific table."""
    try:
        result = await _call_mcp_tool(
            tool_name="get_table_schema",
            arguments={"table_name": table_name},
            user_id=current_user.id,
        )

        columns = None
        if result.get("columns"):
            columns = [
                ColumnInfo(
                    name=col.get("name"),
                    type=col.get("type"),
                    original=col.get("original"),
                )
                for col in result.get("columns", [])
            ]

        return TableSchemaResponse(
            success=result.get("success", False),
            table_name=result.get("table_name"),
            schema=result.get("schema"),
            full_path=result.get("full_path"),
            columns=columns,
            row_count=result.get("row_count"),
            original_filename=result.get("original_filename"),
            created_at=result.get("created_at"),
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_table_schema_failed",
            table_name=table_name,
            error=str(e),
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get table schema: {str(e)}",
        )


# ==================== Get Sample Data Endpoint ====================


@router.get("/tables/{table_name}/sample", response_model=SampleDataResponse)
async def get_sample_data(
    table_name: str,
    current_user: CurrentUser,
    rows: int = 5,
) -> SampleDataResponse:
    """Get sample rows from a table."""
    try:
        result = await _call_mcp_tool(
            tool_name="get_sample_data",
            arguments={"table_name": table_name, "rows": rows},
            user_id=current_user.id,
        )

        return SampleDataResponse(
            success=result.get("success", False),
            table_name=result.get("table_name"),
            sample=result.get("sample"),
            row_count=result.get("row_count"),
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_sample_data_failed",
            table_name=table_name,
            error=str(e),
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sample data: {str(e)}",
        )


# ==================== Execute SQL Endpoint ====================


@router.post("/query", response_model=ExecuteSQLResponse)
async def execute_sql(
    request: ExecuteSQLRequest,
    current_user: CurrentUser,
) -> ExecuteSQLResponse:
    """Execute a SQL query on the CSV tables."""
    logger.info(
        "sql_query_started",
        query_preview=request.query[:100] if request.query else "",
        user_id=current_user.id,
    )

    try:
        result = await _call_mcp_tool(
            tool_name="execute_sql",
            arguments={"query": request.query, "limit": request.limit},
            user_id=current_user.id,
        )

        return ExecuteSQLResponse(
            success=result.get("success", False),
            query_type=result.get("query_type"),
            row_count=result.get("row_count"),
            affected_rows=result.get("affected_rows"),
            results=result.get("results"),
            query=result.get("query"),
            message=result.get("message"),
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "sql_query_failed",
            error=str(e),
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute query: {str(e)}",
        )


# ==================== Delete Table Endpoint ====================


@router.delete("/tables/{table_name}", response_model=DeleteTableResponse)
async def delete_table(
    table_name: str,
    current_user: CurrentUser,
) -> DeleteTableResponse:
    """Delete a CSV table."""
    logger.info(
        "delete_table_started",
        table_name=table_name,
        user_id=current_user.id,
    )

    try:
        result = await _call_mcp_tool(
            tool_name="delete_table",
            arguments={"table_name": table_name},
            user_id=current_user.id,
        )

        if result.get("success"):
            logger.info(
                "delete_table_completed",
                table_name=table_name,
                user_id=current_user.id,
            )

        return DeleteTableResponse(
            success=result.get("success", False),
            message=result.get("message"),
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_table_failed",
            table_name=table_name,
            error=str(e),
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete table: {str(e)}",
        )
