"""MCP server package for DuckDB-backed agent tools."""

from app.mcp_server.client import DuckDBMCPClient


def create_duckdb_mcp_server(*args, **kwargs):
    """Lazily import MCP server factory to avoid module preloading side effects."""
    from app.mcp_server.server import create_duckdb_mcp_server as _create

    return _create(*args, **kwargs)


__all__ = ["DuckDBMCPClient", "create_duckdb_mcp_server"]
