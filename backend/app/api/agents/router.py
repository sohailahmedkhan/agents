"""FastAPI router for `/agents` endpoints.

This module defines HTTP routes, wires dependencies via FastAPI `Depends`,
and maps service exceptions to HTTP responses. It intentionally delegates all
business behavior to `app.agents`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.agents.schemas import AgentChatRequest, AgentToolInvokeRequest, DuckDBQueryRequest
from app.api.agents.dependencies import get_agents_service
from app.agents import AgentsService, list_analysis_options

router = APIRouter(prefix="/agents", tags=["agents"])


def _as_http_error(exc: Exception) -> HTTPException:
    """Map service-layer exceptions to HTTP status codes."""
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, NotImplementedError):
        return HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/health")
async def get_agents_health(service: AgentsService = Depends(get_agents_service)):
    """Return agents capability status."""
    return {"status": "ok", "runtime": service.health_report()}


@router.get("/duckdb/health")
async def get_duckdb_health(service: AgentsService = Depends(get_agents_service)):
    """Return DuckDB connectivity and configuration status."""
    try:
        return {"status": "ok", "duckdb": service.duckdb_health()}
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.get("/duckdb/tables")
async def get_duckdb_tables(service: AgentsService = Depends(get_agents_service)):
    """List tables available in the configured DuckDB database."""
    try:
        return {"tables": service.duckdb_tables()}
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.post("/duckdb/query")
async def run_duckdb_query(
    request: DuckDBQueryRequest,
    service: AgentsService = Depends(get_agents_service),
):
    """Execute a DuckDB SQL query with bounded output."""
    try:
        return service.duckdb_query(
            sql=request.sql,
            params=request.params,
            limit=request.limit,
        )
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.get("/tools")
async def list_agent_tools(service: AgentsService = Depends(get_agents_service)):
    """List available tools."""
    try:
        return {"tools": await service.list_tools()}
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.post("/tools/invoke")
async def invoke_agent_tool(
    request: AgentToolInvokeRequest,
    service: AgentsService = Depends(get_agents_service),
):
    """Invoke a tool directly."""
    try:
        result = await service.invoke_tool(request.name, request.args)
    except Exception as exc:
        raise _as_http_error(exc) from exc
    return {"status": "success", "tool": request.name, "result": result}


@router.get("/mcp/resources")
async def list_mcp_resources(service: AgentsService = Depends(get_agents_service)):
    """List MCP resources."""
    try:
        return {"resources": await service.list_mcp_resources()}
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.get("/mcp/resource")
async def read_mcp_resource(
    uri: str = Query(..., description="Resource URI to fetch"),
    service: AgentsService = Depends(get_agents_service),
):
    """Read one MCP resource by URI."""
    try:
        return await service.read_mcp_resource(uri)
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.get("/mcp/tools")
async def list_mcp_tools(service: AgentsService = Depends(get_agents_service)):
    """List MCP-style tools."""
    try:
        return {"tools": await service.list_mcp_tools()}
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.get("/analysis-options")
async def get_analysis_options():
    """Return selectable analysis options for UI workflows."""
    return {"options": list_analysis_options()}


@router.get("/kommuner")
async def get_available_kommuner(service: AgentsService = Depends(get_agents_service)):
    """Return available kommune names discovered from local Kartverket files."""
    try:
        return {"kommuner": service.list_available_kommuner()}
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.get("/kommune-insights")
async def get_kommune_insights(
    kommune: str = Query(..., description="Kommune key or label"),
    service: AgentsService = Depends(get_agents_service),
):
    """Return main municipality insights loaded from DB via MCP tools."""
    try:
        return await service.get_kommune_insights(kommune)
    except Exception as exc:
        raise _as_http_error(exc) from exc


@router.post("/chat")
async def run_agent_chat(
    request: AgentChatRequest,
    service: AgentsService = Depends(get_agents_service),
):
    """Run chat workflow."""
    try:
        return await service.run_chat(request.model_dump())
    except Exception as exc:
        raise _as_http_error(exc) from exc
