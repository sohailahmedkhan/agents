"""DuckDB service for local analytical storage and SQL query execution.

This module provides a small wrapper around DuckDB connections with
health-check, table listing, and bounded query execution helpers.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import re
from typing import Any, Iterator

from app.core.db_limits import DB_DEFAULT_RESULT_ROWS, validate_db_row_limit


class DuckDBService:
    """Service wrapper around a DuckDB database file."""

    READ_PREFIXES = {"select", "with", "show", "describe", "pragma", "explain"}

    def __init__(self, db_path: str, read_only: bool = False, allow_write: bool = False):
        """Initialize DuckDB service.

        Args:
            db_path: File path to the DuckDB database.
            read_only: Open DB in read-only mode when True.
            allow_write: Permit non-read SQL when True.
        """
        self.db_path = Path(db_path).expanduser()
        self.read_only = read_only
        self.allow_write = allow_write
        if not self.read_only:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load_driver():
        """Load DuckDB driver lazily with a clear error message."""
        try:
            import duckdb  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on local env
            raise RuntimeError("DuckDB driver is not installed. Install backend requirements.") from exc
        return duckdb

    @contextmanager
    def _connect(self) -> Iterator[Any]:
        """Yield a DuckDB connection and always close it."""
        duckdb = self._load_driver()
        conn = duckdb.connect(str(self.db_path), read_only=self.read_only)
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def _is_write_statement(cls, sql: str) -> bool:
        """Return True when SQL appears to be write/DDL."""
        match = re.match(r"^\s*([a-zA-Z_]+)", sql)
        if not match:
            return True
        return match.group(1).lower() not in cls.READ_PREFIXES

    def health(self) -> dict[str, Any]:
        """Return DuckDB connection and version information."""
        with self._connect() as conn:
            version_row = conn.execute("SELECT version()").fetchone()
        version = version_row[0] if version_row else "unknown"
        return {
            "connected": True,
            "db_path": str(self.db_path),
            "read_only": self.read_only,
            "allow_write": self.allow_write,
            "version": version,
        }

    def list_tables(self) -> list[dict[str, str]]:
        """List user-visible tables in the DuckDB database."""
        query = """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name
        """
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
        return [{"schema": str(schema), "name": str(name)} for schema, name in rows]

    def query(
        self,
        sql: str,
        params: list[Any] | None = None,
        limit: int = DB_DEFAULT_RESULT_ROWS,
    ) -> dict[str, Any]:
        """Execute SQL query and return structured result.

        Args:
            sql: SQL statement.
            params: Optional positional parameters.
            limit: Maximum result rows returned.
        """
        statement = str(sql or "").strip()
        if not statement:
            raise ValueError("sql is required.")
        validate_db_row_limit(limit)
        if not self.allow_write and self._is_write_statement(statement):
            raise PermissionError("Write SQL is disabled. Set DUCKDB_ALLOW_WRITE=true to enable.")

        with self._connect() as conn:
            cursor = conn.execute(statement, params or [])
            if cursor.description is None:
                return {
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "truncated": False,
                    "db_path": str(self.db_path),
                    "message": "Statement executed successfully.",
                }

            columns = [str(item[0]) for item in cursor.description]
            fetched = cursor.fetchmany(limit + 1)
            truncated = len(fetched) > limit
            rows = fetched[:limit]

        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
            "truncated": truncated,
            "db_path": str(self.db_path),
        }
