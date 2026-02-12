"""Static catalog for selectable analysis options.

Provides a stable list of UI options for agents workflows and keeps this data
out of router code so it can evolve independently.
"""
from __future__ import annotations

from typing import Any

ANALYSIS_OPTIONS: tuple[dict[str, str], ...] = (
    {
        "key": "portfolio_overview",
        "label": "Portfolio Overview",
        "description": "High-level overview of municipality portfolio composition.",
    },
    {
        "key": "risk_score",
        "label": "Risk Score",
        "description": "Occupancy risk score and key contributors.",
    },
    {
        "key": "largest_properties",
        "label": "Largest Properties",
        "description": "Largest buildings by floor area.",
    },
    {
        "key": "data_quality",
        "label": "Data Quality",
        "description": "Completeness and quality checks for key columns.",
    },
)


def list_analysis_options() -> list[dict[str, Any]]:
    """Return selectable analysis options for clients."""
    return [dict(item) for item in ANALYSIS_OPTIONS]
