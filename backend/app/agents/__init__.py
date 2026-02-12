"""Agents package.

Exports the agents service facade plus auxiliary data providers consumed by
the API layer.
"""

from app.agents.catalog import list_analysis_options
from app.agents.orchestrator import build_agent_orchestrator
from app.agents.service import AgentsService

__all__ = ["AgentsService", "build_agent_orchestrator", "list_analysis_options"]
