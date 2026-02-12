"""Agents API package.

Exports the FastAPI router that serves `/agents` endpoints and keeps HTTP
concerns isolated from the underlying service implementation.
"""

from app.api.agents.router import router

__all__ = ["router"]
