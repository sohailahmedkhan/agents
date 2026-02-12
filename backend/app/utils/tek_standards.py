"""
TEK Standard (Norwegian Building Regulation) Mapping
=====================================================

This module provides mapping from building construction years to the corresponding
Norwegian TEK (Teknisk forskrift) building regulation standard.

TEK standards define minimum requirements for building construction in Norway.
The standard that applies depends on when the building permit was granted.

Reference:
    https://dibk.no/regelverk/byggteknisk-forskrift-tek17/
    https://dibk.no/regelverk/liste-over-tidligere-regelverk/
"""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from app.core.columns import Col


# =============================================================================
# TEK Standards Data
# =============================================================================


@dataclass(frozen=True)
class TEKStandard:
    """Represents a Norwegian building regulation standard."""

    name: str
    in_force_date: date
    in_force_str: str  # Norwegian formatted date
    period_str: str  # Period range string


# Ordered from newest to oldest for efficient lookup
TEK_STANDARDS: list[TEKStandard] = [
    TEKStandard("TEK17", date(2017, 7, 1), "1. jul 2017", "2017–i dag"),
    TEKStandard("TEK10", date(2010, 7, 1), "1. jul 2010", "2010–2017"),
    TEKStandard("TEK07", date(2007, 2, 1), "1. feb 2007", "2007–2010"),
    TEKStandard("TEK97", date(1997, 7, 1), "1. jul 1997", "1997–2007"),
    TEKStandard("BF87", date(1987, 7, 1), "1. jul 1987", "1987–1997"),
    TEKStandard("BF85", date(1985, 1, 1), "1. jan 1985", "1985–1987"),
    TEKStandard("BF69", date(1969, 8, 1), "1. aug 1969", "1969–1985"),
    TEKStandard("BF49", date(1949, 12, 15), "15. des 1949", "1949–1969"),
]

# Fallback for buildings before first standard
PRE_1949 = TEKStandard("Pre-1949", date(1, 1, 1), "Før 1949", "Før 1949")

# Empty result for missing/invalid dates
EMPTY_TEK_INFO: dict[str, str] = {"standard": "", "in_force": "", "period": ""}


# =============================================================================
# Lookup Functions
# =============================================================================


def get_tek_info(status_date: str | date | None) -> dict[str, str]:
    """
    Get the TEK standard info for a building based on its earliest status date.

    The TEK standard is determined by the date the building was registered/permitted.
    Buildings are subject to the regulations in force at the time of construction.

    Args:
        status_date: The building's earliest status date.
                     Can be ISO date string (YYYY-MM-DD), date object, or None.

    Returns:
        Dict with keys: "standard", "in_force", "period".
        Returns empty strings for all keys if date is None or invalid.

    Example:
        >>> get_tek_info("2015-03-12")
        {'standard': 'TEK10', 'in_force': '1. jul 2010', 'period': '2010–2017'}
        >>> get_tek_info("1975-06-15")
        {'standard': 'BF69', 'in_force': '1. aug 1969', 'period': '1969–1985'}
        >>> get_tek_info(None)
        {'standard': '', 'in_force': '', 'period': ''}
    """
    if status_date is None:
        return EMPTY_TEK_INFO.copy()

    # Parse date if string
    if isinstance(status_date, str):
        if not status_date.strip():
            return EMPTY_TEK_INFO.copy()
        try:
            # Handle ISO format YYYY-MM-DD
            parsed_date = date.fromisoformat(status_date[:10])
        except (ValueError, TypeError):
            return EMPTY_TEK_INFO.copy()
    elif isinstance(status_date, date):
        parsed_date = status_date
    else:
        return EMPTY_TEK_INFO.copy()

    # Find the applicable standard (first standard with in_force_date <= parsed_date)
    for tek in TEK_STANDARDS:
        if parsed_date >= tek.in_force_date:
            return {
                "standard": tek.name,
                "in_force": tek.in_force_str,
                "period": tek.period_str,
            }

    # Building predates first standard (BF49)
    return {
        "standard": PRE_1949.name,
        "in_force": PRE_1949.in_force_str,
        "period": PRE_1949.period_str,
    }


def get_tek_standard(status_date: str | date | None) -> str:
    """
    Get just the TEK standard name for a building.

    Convenience function when only the standard name is needed.

    Args:
        status_date: The building's earliest status date.

    Returns:
        TEK standard name (e.g., "TEK17", "BF87", "Pre-1949").
        Returns empty string if date is None or invalid.
    """
    return get_tek_info(status_date)["standard"]


# =============================================================================
# DataFrame Column Utilities
# =============================================================================


def add_tek_standard_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add TEK standard columns to a DataFrame.

    Computes the TEK standard, in-force date, and period based on the
    TidligsteStatusDato column and adds them as new columns.

    Args:
        df: DataFrame with TidligsteStatusDato column.

    Returns:
        DataFrame with added TEK standard columns:
        - TEK-standard
        - TEK Ikrafttredelse
        - TEK Periode
    """
    if Col.TIDLIGSTE_STATUS_DATO not in df.columns:
        return df

    df = df.copy()

    # Apply get_tek_info to each row and expand to columns
    tek_info = df[Col.TIDLIGSTE_STATUS_DATO].apply(get_tek_info)
    df[Col.TEK_STANDARD] = tek_info.apply(lambda x: x["standard"])
    df[Col.TEK_IKRAFTTREDELSE] = tek_info.apply(lambda x: x["in_force"])
    df[Col.TEK_PERIODE] = tek_info.apply(lambda x: x["period"])

    return df
