import urllib.parse
from typing import Any, Callable

import pandas as pd

from app.core.columns import Col


def _normalize_str(value: Any) -> str:
    """Normalize a value to a trimmed string or empty string."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _format_postcode(value: Any) -> str:
    """Format a postcode value into a clean string."""
    if value is None or pd.isna(value):
        return ""
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return _normalize_str(value)


def _format_house_number(value: Any) -> str:
    """Format a house number value into a clean string."""
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return _normalize_str(value)


def _build_google_maps_link(parts: list[str]) -> str:
    """Build a Google Maps search URL from address parts."""
    if not parts:
        return ""
    query = " ".join(parts)
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"


def build_user_maps_link(row: pd.Series) -> str:
    """Build a Google Maps link from user-uploaded address fields.

    Args:
        row: Data row containing Street, Postcode, and City.

    Returns:
        Google Maps search URL string.
    """
    parts: list[str] = []

    street = _normalize_str(row.get(Col.STREET))
    if street:
        parts.append(street)

    postcode = _format_postcode(row.get(Col.POSTCODE))
    if postcode:
        parts.append(postcode)

    city = _normalize_str(row.get(Col.CITY))
    if city:
        parts.append(city)

    return _build_google_maps_link(parts)


def build_kartverket_maps_link(row: pd.Series) -> str:
    """Build a Google Maps link from Kartverket address fields.

    Args:
        row: Data row containing Adresse or Adressenavn/Nummer, Postnummer, Poststed.

    Returns:
        Google Maps search URL string.
    """
    parts: list[str] = []

    adresse = _normalize_str(row.get(Col.ADRESSE))
    if adresse:
        parts.append(adresse)
    else:
        adressenavn = _normalize_str(row.get(Col.ADRESSENAVN))
        nummer = _format_house_number(row.get(Col.NUMMER))
        if adressenavn or nummer:
            parts.append(f"{adressenavn} {nummer}".strip())

    postnummer = _format_postcode(row.get(Col.POSTNUMMER))
    if postnummer:
        parts.append(postnummer)

    poststed = _normalize_str(row.get(Col.POSTSTED))
    if poststed:
        parts.append(poststed)

    return _build_google_maps_link(parts)


def _add_google_maps_link(df: pd.DataFrame, builder: Callable[[pd.Series], str]) -> pd.DataFrame:
    """Return a copy of the dataframe with GoogleMapsLink column populated.

    Args:
        df: Source dataframe.
        builder: Function that builds a maps URL per row.

    Returns:
        Dataframe copy with Col.GOOGLE_MAPS_LINK set.
    """
    df = df.copy()
    df[Col.GOOGLE_MAPS_LINK] = df.apply(builder, axis=1)
    return df


def add_google_maps_link_for_user(df: pd.DataFrame) -> pd.DataFrame:
    """Add Google Maps links using user-uploaded address columns."""
    return _add_google_maps_link(df, build_user_maps_link)


def add_google_maps_link_for_kartverket(df: pd.DataFrame) -> pd.DataFrame:
    """Add Google Maps links using Kartverket address columns."""
    return _add_google_maps_link(df, build_kartverket_maps_link)
