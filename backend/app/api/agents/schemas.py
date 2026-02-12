"""Pydantic schemas for agents HTTP requests.

These models validate incoming payloads for `/agents` routes and provide a
single place to evolve API contracts without touching router logic.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.db_limits import DB_DEFAULT_RESULT_ROWS, DB_MAX_RESULT_ROWS


class AgentChatRequest(BaseModel):
    """Request model for orchestrated agent chat workflows."""

    message: str = ""
    workflow: Literal["kommune_match_overview", "benchmark_health"] = "kommune_match_overview"
    kommune_name: str | None = None
    data_source: Literal["raw", "imputed"] = "raw"
    processed_rows: list[dict[str, Any]] | None = None
    match_hash: str | None = None
    requested_analyses: list[str] = Field(default_factory=list)
    use_llm: bool = True
    include_mcp_resources: bool = False


class AgentToolInvokeRequest(BaseModel):
    """Request model for direct tool invocation."""

    name: str = Field(..., description="Registered tool name")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class DuckDBQueryRequest(BaseModel):
    """Request model for executing DuckDB SQL queries."""

    sql: str = Field(..., description="SQL statement to execute")
    params: list[Any] | None = Field(default=None, description="Optional positional query parameters")
    limit: int = Field(default=DB_DEFAULT_RESULT_ROWS, ge=1, le=DB_MAX_RESULT_ROWS, description="Maximum rows to return")
