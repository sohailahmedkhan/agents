"""Environment-backed settings model for backend configuration.

Defines a typed `AppSettings` object and parsing helpers that normalize
runtime options such as app metadata and CORS origins.
"""
from __future__ import annotations

from functools import lru_cache
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def _load_env_files() -> None:
    """Load .env files from project roots when available."""
    current = Path(__file__).resolve()
    candidates = (
        current.parents[4] / ".env",  # workspace root: .../Docker/.env
        current.parents[3] / ".env",  # agents root: .../Docker/agents/.env
        current.parents[2] / ".env",  # backend root: .../Docker/agents/backend/.env
        Path.cwd() / ".env",
    )
    for path in candidates:
        if path.exists():
            load_dotenv(path, override=False)


def _csv_env(name: str, default: str) -> list[str]:
    """Parse comma-separated env vars into a clean list."""
    raw = os.getenv(name, default)
    values = [item.strip() for item in raw.split(",")]
    return [item for item in values if item]


def _env_bool(name: str, default: bool) -> bool:
    """Parse a boolean environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _default_duckdb_path() -> str:
    """Return default DuckDB path inside the agents project."""
    project_root = Path(__file__).resolve().parents[3]
    return str(project_root / "data" / "db" / "agents.duckdb")


@dataclass(frozen=True)
class AppSettings:
    """Runtime configuration for the FastAPI application."""

    title: str = "Agents API"
    version: str = "0.1.0"
    description: str = "Standalone FastAPI backend for agents workspace."
    cors_origins: tuple[str, ...] = ("http://localhost:3100", "http://localhost:3000")
    duckdb_path: str = _default_duckdb_path()
    duckdb_read_only: bool = False
    duckdb_allow_write: bool = False
    llm_model: str = "claude-sonnet-4-5"
    llm_provider: str = "vertex_anthropic"
    vertex_project_id: str = ""
    vertex_location: str = "europe-west1"

    @classmethod
    def from_env(cls) -> "AppSettings":
        """Build settings from environment variables."""
        _load_env_files()

        title = os.getenv("APP_NAME", cls.title)
        version = os.getenv("APP_VERSION", cls.version)
        description = os.getenv("APP_DESCRIPTION", cls.description)
        origins = tuple(_csv_env("APP_CORS_ORIGINS", ",".join(cls.cors_origins)))
        duckdb_path = os.getenv("DUCKDB_PATH", cls.duckdb_path)
        duckdb_read_only = _env_bool("DUCKDB_READ_ONLY", cls.duckdb_read_only)
        duckdb_allow_write = _env_bool("DUCKDB_ALLOW_WRITE", cls.duckdb_allow_write)
        llm_model = os.getenv("LLM_MODEL", os.getenv("GOOGLE_ADK_MODEL", cls.llm_model))
        llm_provider = os.getenv("LLM_PROVIDER", cls.llm_provider)
        vertex_project_id = os.getenv("VERTEX_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", cls.vertex_project_id))
        vertex_location = os.getenv("VERTEX_LOCATION", os.getenv("GOOGLE_CLOUD_LOCATION", cls.vertex_location))
        return cls(
            title=title,
            version=version,
            description=description,
            cors_origins=origins,
            duckdb_path=duckdb_path,
            duckdb_read_only=duckdb_read_only,
            duckdb_allow_write=duckdb_allow_write,
            llm_model=llm_model,
            llm_provider=llm_provider,
            vertex_project_id=vertex_project_id,
            vertex_location=vertex_location,
        )
