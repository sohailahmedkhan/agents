"""MCP client wrapper for the local DuckDB MCP server."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys
from typing import Any

from app.mcp_server.contracts import MCP_RESOURCES, MCP_TOOLS

try:
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    Client = None  # type: ignore[assignment]
    StdioTransport = None  # type: ignore[assignment]


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict):
            return {str(k): v for k, v in dumped.items()}
    if hasattr(value, "dict"):
        dumped = value.dict()
        if isinstance(dumped, dict):
            return {str(k): v for k, v in dumped.items()}
    out: dict[str, Any] = {}
    for key in ("name", "description", "uri", "mimeType", "title"):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


class DuckDBMCPClient:
    """Thin async client around the backend DuckDB MCP server."""

    def __init__(self):
        project_root = Path(__file__).resolve().parents[2]
        self._cwd = str(project_root)
        self._client_cm: Any | None = None
        self._client: Any | None = None
        self._lifecycle_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()

    @staticmethod
    def _require_fastmcp() -> None:
        if Client is None or StdioTransport is None:
            raise RuntimeError("fastmcp is not installed. Install backend requirements first.")

    @staticmethod
    def _server_env() -> dict[str, str]:
        env = {
            "PATH": os.getenv("PATH", ""),
            "PYTHONPATH": os.getenv("PYTHONPATH", ""),
        }
        for key in ("DUCKDB_PATH", "DUCKDB_READ_ONLY", "DUCKDB_ALLOW_WRITE"):
            value = os.getenv(key)
            if value is not None:
                env[key] = value
        return env

    def _transport(self) -> Any:
        self._require_fastmcp()
        return StdioTransport(
            command=sys.executable,
            args=["-m", "app.mcp_server.server", "--transport", "stdio"],
            cwd=self._cwd,
            env=self._server_env(),
        )

    async def start(self) -> None:
        """Start and retain a single MCP client session."""
        if Client is None:
            return

        async with self._lifecycle_lock:
            if self._client is not None:
                return

            client_cm = Client(self._transport())
            self._client = await client_cm.__aenter__()
            self._client_cm = client_cm

    async def stop(self) -> None:
        """Close the retained MCP client session."""
        if Client is None:
            return

        async with self._lifecycle_lock:
            if self._client_cm is None:
                return
            try:
                await self._client_cm.__aexit__(None, None, None)
            finally:
                self._client_cm = None
                self._client = None

    async def _ensure_client(self) -> Any:
        self._require_fastmcp()
        if self._client is None:
            await self.start()
        if self._client is None:
            raise RuntimeError("Failed to start MCP client session.")
        return self._client

    async def list_tools(self) -> list[dict[str, Any]]:
        """List MCP tools from the server."""
        if Client is None:
            return [dict(item) for item in MCP_TOOLS]
        client = await self._ensure_client()
        async with self._request_lock:
            tools = await client.list_tools()
        return [_to_dict(tool) for tool in tools]

    async def list_resources(self) -> list[dict[str, Any]]:
        """List MCP resources from the server."""
        if Client is None:
            return [dict(item) for item in MCP_RESOURCES]
        client = await self._ensure_client()
        async with self._request_lock:
            resources = await client.list_resources()
        return [_to_dict(resource) for resource in resources]

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read an MCP resource by URI."""
        if not uri:
            raise ValueError("uri is required.")

        client = await self._ensure_client()
        async with self._request_lock:
            payload = await client.read_resource(uri)
        return {"uri": uri, "contents": payload}

    async def call_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call one MCP tool by name."""
        if not name:
            raise ValueError("name is required.")

        client = await self._ensure_client()
        async with self._request_lock:
            try:
                result = await client.call_tool(name, args or {}, raise_on_error=False)
            except TypeError as exc:
                if "raise_on_error" not in str(exc):
                    raise
                result = await client.call_tool(name, args or {})

        is_error = bool(getattr(result, "is_error", False))
        if is_error:
            raise ValueError(f"MCP tool failed: {name}")

        if isinstance(result, dict):
            return result
        if isinstance(result, (list, tuple, str, int, float, bool)):
            return {"result": result}

        if hasattr(result, "model_dump"):
            dumped = result.model_dump()
            if isinstance(dumped, dict):
                return dumped
            return {"result": dumped}
        if hasattr(result, "dict"):
            dumped = result.dict()
            if isinstance(dumped, dict):
                return dumped
            return {"result": dumped}

        if hasattr(result, "data") and result.data is not None:
            if isinstance(result.data, dict):
                return result.data
            return {"result": result.data}

        content = getattr(result, "content", None)
        if content is not None:
            return {"content": content}
        return {"result": result}
