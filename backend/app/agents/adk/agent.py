"""Google ADK root agent initialization."""
from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any

from app.agents.orchestrator import build_agent_orchestrator
from app.core.settings import AppSettings

try:
    from google.adk.agents import LlmAgent
except Exception:  # pragma: no cover - optional dependency at runtime
    LlmAgent = None  # type: ignore[assignment]


def build_root_agent() -> Any:
    """Create the backend's Google ADK root agent."""
    if LlmAgent is None:
        raise RuntimeError(
            "google-adk is not installed. Install dependencies first: `pip install -r requirements.txt`."
        )

    try:
        from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
        from google.adk.models.anthropic_llm import Claude
        from google.adk.models.registry import LLMRegistry
        from mcp import StdioServerParameters
    except ModuleNotFoundError as exc:
        raise RuntimeError("MCP or Vertex Anthropic dependencies are missing. Install backend requirements.") from exc

    settings = AppSettings.from_env()
    if not settings.vertex_project_id:
        raise RuntimeError("Missing VERTEX_PROJECT_ID (or GOOGLE_CLOUD_PROJECT) for Vertex provider.")

    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", settings.vertex_project_id)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", settings.vertex_location)

    try:
        LLMRegistry.register(Claude)
    except Exception:
        pass

    project_root = Path(__file__).resolve().parents[3]
    pythonpath = os.getenv("PYTHONPATH", "")
    pythonpath_parts = [item for item in pythonpath.split(os.pathsep) if item]
    project_root_str = str(project_root)
    if project_root_str not in pythonpath_parts:
        pythonpath_parts.insert(0, project_root_str)

    mcp_env = {
        "PATH": os.getenv("PATH", ""),
        "PYTHONPATH": os.pathsep.join(pythonpath_parts),
    }
    for key in ("DUCKDB_PATH", "DUCKDB_READ_ONLY", "DUCKDB_ALLOW_WRITE"):
        value = os.getenv(key)
        if value is not None:
            mcp_env[key] = value

    mcp_params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server.server", "--transport", "stdio"],
            env=mcp_env,
        ),
        timeout=30,
    )

    return build_agent_orchestrator(
        model=settings.llm_model,
        connection_params=mcp_params,
    )


# ADK tooling expects a module-level `root_agent`.
try:  # pragma: no cover - depends on local runtime dependencies
    root_agent = build_root_agent() if LlmAgent is not None else None
except Exception:
    root_agent = None
