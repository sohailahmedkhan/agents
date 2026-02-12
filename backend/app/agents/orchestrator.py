"""Agent orchestrator builder for ADK chat workflow."""
from __future__ import annotations

from typing import Any

try:
    from google.adk.agents import LlmAgent
    from google.adk.tools.mcp_tool import McpToolset
except ModuleNotFoundError:  # pragma: no cover - depends on runtime env
    LlmAgent = None  # type: ignore[assignment]
    McpToolset = None  # type: ignore[assignment]


def build_agent_orchestrator(model: str, connection_params: Any, workflow: str = "") -> Any:
    """Create the top-level orchestrator agent.

    The agent decides when to discover MCP tools and when to call them.
    """
    if LlmAgent is None or McpToolset is None:
        raise RuntimeError("google-adk is not installed. Install backend requirements first.")

    instruction = (
        "You are `agent_orchestrator`, a municipality data assistant. "
        "For all database actions use `mcp_call_tool` only. "
        "Discover first with `mcp_list_tools` when needed, then call "
        "`duckdb_list_tables`, `duckdb_describe_table`, and `duckdb_query` via `mcp_call_tool`. "
        "Prefer specialized call targets `duckdb_kommune_occupancy_distribution` and "
        "`duckdb_kommune_largest_occupancy_area` for municipality occupancy insights. "
        "For underwriting-style insights, prefer `duckdb_kommune_underwriting_analytics` "
        "or sectional targets such as `duckdb_kommune_exposure_dashboard` and "
        "`duckdb_kommune_data_quality_score`. "
        "Generate SQL based on the user's request, execute it, and answer only from returned data. "
        "If needed information is missing, clearly ask a follow-up question."
    )
    if workflow:
        instruction = f"{instruction}\nWorkflow hint: {workflow}"

    return LlmAgent(
        name="agent_orchestrator",
        model=model,
        instruction=instruction,
        description="MCP-driven orchestrator that plans tool calls and answers from DuckDB results.",
        tools=[McpToolset(connection_params=connection_params)],
    )
