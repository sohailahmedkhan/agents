"""Centralized row limits for DuckDB result extraction."""
from __future__ import annotations

DB_MAX_RESULT_ROWS = 2000
DB_DEFAULT_RESULT_ROWS = DB_MAX_RESULT_ROWS


def validate_db_row_limit(limit: int) -> int:
    """Validate a requested DB row limit against global bounds."""
    if limit < 1 or limit > DB_MAX_RESULT_ROWS:
        raise ValueError(f"limit must be in range [1, {DB_MAX_RESULT_ROWS}].")
    return limit
