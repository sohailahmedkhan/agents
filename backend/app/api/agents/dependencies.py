"""Dependency providers for the agents API layer.

This module owns API-facing dependency construction and caching so routers can
remain declarative and easy to test.
"""
from __future__ import annotations

from functools import lru_cache

from app.agents import AgentsService


@lru_cache(maxsize=1)
def get_agents_service() -> AgentsService:
    """Return singleton agents service instance."""
    return AgentsService()


def reset_agents_service_cache() -> None:
    """Clear cached service instance (useful in tests)."""
    get_agents_service.cache_clear()
