"""
Kartverket data service for property enrichment.

This module provides functionality for:
1. Finding and loading Kartverket Excel files
2. Loading pre-filtered BuildingOwnership data
3. Building a processed dataset (Knr-Gnr-Bnr, Adresse, TEK, simplified category)
"""
import io
import logging
import re
from pathlib import Path
from typing import Literal, NamedTuple

import pandas as pd

from app.core.columns import Col
from app.utils.dataframe import df_to_json_safe, merge_underenheter_by_group
from app.utils.cache import calculate_file_hash, get_kartverket_cached_result, save_kartverket_cache
from app.utils.google_maps import add_google_maps_link_for_kartverket
from app.utils.tek_standards import add_tek_standard_columns
from app.modules.matrikkel.codes import (
    EXCLUDED_BUILDING_STATUS_CODE_IDS,
    INCLUDED_BUILDING_STATUS_CODE_IDS,
    INTERNAL_ID_TO_NS3457,
    get_building_type_hierarchy,
    get_simplified_building_category,
    normalize_simplified_building_category,
)

logger = logging.getLogger(__name__)

# Cache schema version to invalidate stale Kartverket caches when processing changes.
KARTVERKET_CACHE_VERSION = "2026-02-10-category-fallback-annet-v4"

# Get the project root directory
BACKEND_DIR = Path(__file__).resolve().parents[3]
PROJECT_ROOT = BACKEND_DIR.parent
KARTVERKET_DIR = PROJECT_ROOT / "data" / "raw" / "norway" / "kartverket_data"
KARTVERKET_IMPUTED_DIR = (
    PROJECT_ROOT / "data" / "imputed" / "norway" / "kartverket_data"
)
KARTVERKET_DATA_SOURCES: tuple[str, str] = ("raw", "imputed")
KartverketDataSource = Literal["raw", "imputed"]


def resolve_kartverket_source_dir(data_source: KartverketDataSource) -> Path:
    """Resolve source directory for a Kartverket dataset mode."""
    return KARTVERKET_DIR if data_source == "raw" else KARTVERKET_IMPUTED_DIR


class KartverketDataset(NamedTuple):
    """Container for processed Kartverket data."""
    data_df: pd.DataFrame
    data_dedup_df: pd.DataFrame
    unfiltered_df: pd.DataFrame
    unfiltered_dedup_df: pd.DataFrame
    excluded_status_df: pd.DataFrame
    excluded_status_dedup_df: pd.DataFrame
    statistics: dict
    file_path: Path


def _normalize_kommune_name(value: str) -> str:
    """Normalize kommune names for matching against filenames."""
    return " ".join(str(value).replace("_", " ").split()).strip().lower()


def _extract_kommune_candidates(stem: str) -> list[str]:
    """Extract normalized kommune name candidates from a filename stem.

    Args:
        stem: Filename stem without extension.

    Returns:
        List of normalized kommune name candidates.
    """
    parts = stem.split("_")
    if len(parts) < 2:
        return [_normalize_kommune_name(stem)]

    core_parts = parts
    if len(core_parts) >= 2 and core_parts[-1].lower() == "imputed" and core_parts[-2].lower() == "properties":
        core_parts = core_parts[:-2]
    elif core_parts[-1].lower() == "properties":
        core_parts = core_parts[:-1]

    name_part = "_".join(core_parts[1:]) if len(core_parts) > 1 else ""

    candidates: list[str] = []
    for raw in [p for p in name_part.split("___") if p]:
        normalized = _normalize_kommune_name(raw)
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    full_candidate = _normalize_kommune_name(name_part)
    if full_candidate and full_candidate not in candidates:
        candidates.append(full_candidate)

    # Add first segment to handle filenames that append fylke names (e.g., "Herøy_Møre_og_Romsdal")
    first_segment = _normalize_kommune_name(name_part.split("_", 1)[0])
    if first_segment and first_segment not in candidates:
        candidates.append(first_segment)

    return candidates


def find_kartverket_file(kommune_name: str, source_dir: Path | None = None) -> Path | None:
    """
    Find the Kartverket file for a given kommune.

    Supported filenames:
    - {KNR}_{Kommune}_Properties.xlsx
    - {KNR}_{Kommune}_Properties_Imputed.xlsx

    Args:
        kommune_name: Name of the kommune (e.g., "Austevoll")
        source_dir: Optional directory override for lookup.

    Returns:
        Path to the Kartverket file if found, None otherwise
    """
    source_root = source_dir or KARTVERKET_DIR
    if not source_root.exists():
        return None

    target = _normalize_kommune_name(kommune_name)
    if not target:
        return None

    matches: list[Path] = []

    matched_paths: list[Path] = []
    for pattern in ("*_Properties.xlsx", "*_Properties_Imputed.xlsx"):
        matched_paths.extend(source_root.glob(pattern))

    for file_path in sorted(set(matched_paths)):
        # Skip temporary Excel lock files
        if file_path.name.startswith("~$"):
            continue

        candidates = _extract_kommune_candidates(file_path.stem)
        if target in candidates:
            matches.append(file_path)

    if not matches:
        return None
    if len(matches) > 1:
        logger.warning(
            "Multiple Kartverket files matched kommune '%s': %s. Using first match.",
            kommune_name,
            ", ".join([m.name for m in matches]),
        )
    return matches[0]


def _read_kartverket_bytes(file_path: Path) -> tuple[bytes, str]:
    """Read Kartverket Excel bytes and compute a content hash."""
    file_bytes = file_path.read_bytes()
    file_hash = calculate_file_hash(file_bytes)
    return file_bytes, file_hash


def _load_kartverket_dataframe(file_bytes: bytes) -> pd.DataFrame:
    """Load BuildingOwnership sheet from raw Excel bytes."""
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name="BuildingOwnership")


def _apply_minimal_processing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply minimal processing to unfiltered data (no ownership filtering).

    Adds computed columns needed for display but preserves all rows.
    """
    df = _fill_alt_addresses_from_cadastre(df)
    df = add_knr_gnr_bnr_column(df)
    df = add_address_column(df)
    df = add_google_maps_link_for_kartverket(df)
    df = add_tek_standard_columns(df)
    df = add_simplified_category_column(df)
    return df


def _process_kartverket_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply the Kartverket enrichment pipeline to a dataframe."""
    df = filter_kommune_hjemmelshaver_rows(df)
    df = _fill_alt_addresses_from_cadastre(df)
    df = add_knr_gnr_bnr_column(df)
    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows from BuildingOwnership sheet")

    df = add_address_column(df)
    df = add_google_maps_link_for_kartverket(df)
    df = add_tek_standard_columns(df)
    df = add_simplified_category_column(df)

    statistics = {
        "total_rows": total_rows
    }

    return df, statistics


def _dataframe_from_cache(cache_payload: dict) -> pd.DataFrame:
    """Rebuild dataframe from cached Kartverket payload."""
    rows = cache_payload.get("data", [])
    columns = cache_payload.get("columns")
    df = pd.DataFrame(rows)
    if columns:
        df = df.reindex(columns=columns)
    return df


def _cache_has_required_columns(cache_payload: dict) -> bool:
    """Return True when cached payload contains required scoring columns."""
    columns = cache_payload.get("columns")
    if not isinstance(columns, list):
        return False
    return Col.FORENKLET_BYGNINGS_KATEGORI in columns


def _build_deduplicated_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Build deduplicated Kartverket view by duplicate group and duplicate flag."""
    return merge_underenheter_by_group(df)


def split_excluded_status_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split dataframe into included rows (allowed status codes) and excluded-status rows."""
    if Col.BYGNINGSSTATUS_KODE_ID not in df.columns:
        return df, df.iloc[0:0].copy()

    status_series = pd.to_numeric(df[Col.BYGNINGSSTATUS_KODE_ID], errors="coerce")
    included_mask = status_series.isin(INCLUDED_BUILDING_STATUS_CODE_IDS)
    included_df = df[included_mask].copy()
    excluded_df = df[~included_mask].copy()
    return included_df, excluded_df


def _normalize_owner_name(value: str) -> str:
    """Normalize owner names for case-insensitive matching."""
    return " ".join(str(value).replace("_", " ").split()).strip().lower()


def _split_ownership_values(value: object) -> list[str]:
    """Split semicolon/comma-separated ownership values."""
    if value is None or pd.isna(value):
        return []
    value_str = str(value).strip()
    if value_str == "" or value_str == "-" or value_str.lower() in {"nan", "<na>"}:
        return []
    return [part.strip() for part in re.split(r"[;,]", value_str) if part.strip()]


def _extract_code_ids(value: str) -> list[int]:
    """Extract integer code IDs from a raw code string."""
    if not value:
        return []
    codes: list[int] = []
    for token in re.findall(r"\d+", str(value)):
        try:
            codes.append(int(token))
        except ValueError:
            continue
    return codes


def _parse_ownership_percent(value: object) -> float | None:
    """Parse an ownership percentage value (e.g. '100.0%') into a float.

    Returns None when the value is missing or cannot be parsed.
    """
    if value is None or pd.isna(value):
        return None
    value_str = str(value).strip()
    if value_str == "" or value_str == "-" or value_str.lower() in {"nan", "<na>"}:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", value_str)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _is_value_present(value: object) -> bool:
    """Return True when a value is non-empty and not a placeholder."""
    if value is None or pd.isna(value):
        return False
    value_str = str(value).strip()
    return value_str not in {"", "-", "nan", "<na>"}


def filter_kommune_hjemmelshaver_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep rows only when the kommune is an owner with ownership code 0.

    Rules:
    - If the kommune appears in the owners list but does not have code 0 (even if it has 1/11),
      the row is removed.
    - If the kommune does not appear in the owners list (or owners/codes are empty),
      the row is removed.
    - If the kommune has code 0 but owns less than 100%, the row is removed.
    - If the kommune has code 0 and at least 100% ownership, but there are non-kommune owners and
      the total ownership exceeds 100%, the row is removed.
      (If all owners are the kommune itself, keep even if the total exceeds 100%.)
    """
    required_cols = {Col.ALLE_EIERE, Col.ALLE_EIERFORHOLD_KODE_IDS, Col.ALLE_EIERANDELER}
    missing_cols = required_cols.difference(set(df.columns))
    if missing_cols:
        logger.warning(
            "Kartverket ownership filter skipped: missing required columns (%s). Returning empty dataframe.",
            ", ".join(sorted(missing_cols)),
        )
        return df.iloc[0:0].copy()

    kommune_name = df.attrs.get("kommune_name")
    if not kommune_name:
        logger.warning("Kartverket ownership filter skipped: missing df.attrs['kommune_name']. Returning empty dataframe.")
        return df.iloc[0:0].copy()

    if df.empty:
        return df.copy()

    # Ensure kommune name includes "KOMMUNE" suffix for exact matching
    kommune_base = _normalize_owner_name(kommune_name)
    if not kommune_base.endswith(" kommune"):
        kommune_norm = f"{kommune_base} kommune"
    else:
        kommune_norm = kommune_base

    def should_keep(row: pd.Series) -> bool:
        owners = _split_ownership_values(row.get(Col.ALLE_EIERE))
        codes_raw = _split_ownership_values(row.get(Col.ALLE_EIERFORHOLD_KODE_IDS))
        shares_raw = _split_ownership_values(row.get(Col.ALLE_EIERANDELER))

        if not owners or not codes_raw or not shares_raw:
            return False

        # The owners/codes/shares lists are supposed to be aligned by index.
        # If the lengths don't match, treat the row as malformed and drop it.
        if len(owners) != len(codes_raw) or len(owners) != len(shares_raw):
            return False

        kommune_owner_indices = [
            idx
            for idx, owner in enumerate(owners)
            if _normalize_owner_name(owner) == kommune_norm
        ]
        if not kommune_owner_indices:
            return False

        kommune_codes: list[int] = []
        kommune_shares: list[float] = []
        for owner_idx in kommune_owner_indices:
            if owner_idx < len(codes_raw):
                kommune_codes.extend(_extract_code_ids(codes_raw[owner_idx]))
            if owner_idx < len(shares_raw):
                share = _parse_ownership_percent(shares_raw[owner_idx])
                if share is not None:
                    kommune_shares.append(share)

        if 0 not in kommune_codes:
            return False

        # Kommune must own at least 100% in total (duplicates allowed, but < 100% is removed).
        kommune_total_share = sum(kommune_shares)
        if kommune_total_share < 100.0 - 1e-6:
            return False

        # Parse total ownership across all owners; if shares can't be parsed, remove row (strict).
        all_shares: list[float] = []
        for raw in shares_raw:
            parsed = _parse_ownership_percent(raw)
            if parsed is None:
                return False
            all_shares.append(parsed)

        total_share = sum(all_shares)
        has_non_kommune_owner = any(_normalize_owner_name(owner) != kommune_norm for owner in owners)

        if has_non_kommune_owner and total_share > 100.0 + 1e-6:
            return False

        return True

    filtered = df[df.apply(should_keep, axis=1)].copy()
    removed = len(df) - len(filtered)
    if removed > 0:
        logger.info(f"Filtered out {removed} rows where kommune ownership criteria not met.")
    return filtered


def _format_postnummer(value: object) -> str:
    """Format Postnummer value, converting floats to integers."""
    if not _is_value_present(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _build_alt_address(row: pd.Series) -> str:
    """Build a single formatted address for Alt. Adresser."""
    if not _is_value_present(row.get(Col.ADRESSENAVN)):
        return ""

    address_name = str(row.get(Col.ADRESSENAVN)).strip()
    number_value = row.get(Col.NUMMER)
    if _is_value_present(number_value):
        address = f"{address_name} {format_nummer(number_value)}".strip()
    else:
        address = address_name

    postnummer_value = row.get(Col.POSTNUMMER)
    postnummer = _format_postnummer(postnummer_value)
    if postnummer:
        address = f"{address}, {postnummer}"

    poststed_value = row.get(Col.POSTSTED)
    if _is_value_present(poststed_value):
        poststed = str(poststed_value).strip()
        address = f"{address} {poststed}"

    return address


def _fill_alt_addresses_from_cadastre(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill Alt. Adresser for rows missing addresses using other rows with the same Knr-Gnr-Bnr.

    Adds a boolean column to flag rows where alternate addresses were populated.
    """
    df = df.copy()
    flag_col = Col.ALT_ADRESSER_FRA_KNR_GNR_BNR
    df[flag_col] = False

    if Col.ADRESSENAVN not in df.columns or Col.NUMMER not in df.columns:
        return df

    if Col.KNR_GNR_BNR in df.columns:
        key_series = df[Col.KNR_GNR_BNR]
    elif {Col.KOMMUNE_NR, Col.GARDS_NR, Col.BRUKS_NR}.issubset(df.columns):
        key_series = df.apply(create_knr_gnr_bnr, axis=1)
    else:
        return df

    key_series = key_series.fillna("").astype(str).str.strip()
    key_valid_mask = key_series.apply(_is_value_present)

    address_series = df.apply(_build_alt_address, axis=1).fillna("").astype(str)
    has_address_mask = address_series.str.strip() != ""

    if not key_valid_mask.any() or not has_address_mask.any():
        return df

    address_lookup = (
        pd.DataFrame({"key": key_series, "address": address_series})
        .loc[key_valid_mask & has_address_mask]
        .groupby("key")["address"]
        .apply(lambda s: list(dict.fromkeys([a.strip() for a in s if str(a).strip()])))
    )

    missing_mask = key_valid_mask & (~has_address_mask)
    if not missing_mask.any():
        return df

    if Col.ADRESSER not in df.columns:
        df[Col.ADRESSER] = ""

    for idx in df.index[missing_mask]:
        key = key_series.at[idx]
        addresses = address_lookup.get(key, [])
        if not addresses:
            continue

        existing_value = df.at[idx, Col.ADRESSER]
        existing = (
            [addr.strip() for addr in str(existing_value).split(";") if addr.strip()]
            if _is_value_present(existing_value)
            else []
        )
        combined = list(dict.fromkeys(existing + addresses))
        df.at[idx, Col.ADRESSER] = ";".join(combined)
        df.at[idx, flag_col] = True

    return df


def build_kartverket_dataset(kommune_name: str, source_dir: Path | None = None) -> KartverketDataset | None:
    """
    Build fully processed Kartverket dataset for a kommune.

    This is the centralized pipeline for BuildingOwnership data:
    - Add Knr-Gnr-Bnr
    - Add Adresse
    - Add Google Maps link
    - Add TEK standards
    - Add simplified building category

    Args:
        kommune_name: Name of the kommune
        source_dir: Optional source directory override for kommune files.

    Returns:
        KartverketDataset with processed dataframe, statistics, and file path,
        or None if file not found.
    """
    file_path = find_kartverket_file(kommune_name, source_dir=source_dir)
    if not file_path:
        return None

    file_bytes, file_hash = _read_kartverket_bytes(file_path)
    cache_source = "imputed" if file_path.stem.lower().endswith("_properties_imputed") else "raw"

    cached = get_kartverket_cached_result(file_hash, kommune_name, source=cache_source)
    if (
        cached
        and cached.get("cache_version") == KARTVERKET_CACHE_VERSION
        and _cache_has_required_columns(cached)
    ):
        df = _dataframe_from_cache(cached)
        df_unfiltered = _dataframe_from_cache(cached.get("unfiltered", cached))
        cached_dedup = cached.get("deduplicated")
        if isinstance(cached_dedup, dict) and "data" in cached_dedup:
            df_dedup = _dataframe_from_cache(cached_dedup)
        else:
            df_dedup = _build_deduplicated_dataframe(df)

        cached_unfiltered_dedup = cached.get("unfiltered_deduplicated")
        if isinstance(cached_unfiltered_dedup, dict) and "data" in cached_unfiltered_dedup:
            df_unfiltered_dedup = _dataframe_from_cache(cached_unfiltered_dedup)
        else:
            df_unfiltered_dedup = _build_deduplicated_dataframe(df_unfiltered)

        cached_excluded_status = cached.get("excluded_status")
        if isinstance(cached_excluded_status, dict) and "data" in cached_excluded_status:
            df_excluded_status = _dataframe_from_cache(cached_excluded_status)
        else:
            df_excluded_status = df.iloc[0:0].copy()

        cached_excluded_status_dedup = cached.get("excluded_status_deduplicated")
        if isinstance(cached_excluded_status_dedup, dict) and "data" in cached_excluded_status_dedup:
            df_excluded_status_dedup = _dataframe_from_cache(cached_excluded_status_dedup)
        else:
            df_excluded_status_dedup = _build_deduplicated_dataframe(df_excluded_status)

        statistics = cached.get("statistics", {"total_rows": len(df)})
        if "file_hash" not in statistics:
            statistics["file_hash"] = file_hash[:8]
        statistics.setdefault("deduplicated_rows", len(df_dedup))
        statistics.setdefault("unfiltered_rows", len(df_unfiltered))
        statistics.setdefault("unfiltered_deduplicated_rows", len(df_unfiltered_dedup))
        statistics.setdefault("filtered_out_rows", len(df_unfiltered) - len(df))
        statistics.setdefault("filtered_out_status_rows", len(df_excluded_status))
        statistics.setdefault("excluded_status_rows", len(df_excluded_status))
        statistics.setdefault("excluded_status_deduplicated_rows", len(df_excluded_status_dedup))
        return KartverketDataset(
            data_df=df,
            data_dedup_df=df_dedup,
            unfiltered_df=df_unfiltered,
            unfiltered_dedup_df=df_unfiltered_dedup,
            excluded_status_df=df_excluded_status,
            excluded_status_dedup_df=df_excluded_status_dedup,
            statistics=statistics,
            file_path=file_path
        )
    elif cached and cached.get("cache_version") == KARTVERKET_CACHE_VERSION:
        logger.warning(
            "Ignoring stale Kartverket cache lacking required columns for %s (%s). Rebuilding from source.",
            kommune_name,
            file_path.name,
        )

    logger.info(f"Loading Kartverket file: {file_path.name}")
    data_df = _load_kartverket_dataframe(file_bytes)
    data_df.attrs["kommune_name"] = kommune_name

    # Process unfiltered data (minimal processing, no ownership filter)
    df_unfiltered_copy = data_df.copy()
    df_unfiltered_copy.attrs["kommune_name"] = kommune_name
    df_unfiltered = _apply_minimal_processing(df_unfiltered_copy)

    # Process filtered data (with ownership filter)
    df, statistics = _process_kartverket_dataframe(data_df)
    df, df_excluded_status = split_excluded_status_rows(df)
    df_dedup = _build_deduplicated_dataframe(df)
    df_unfiltered_dedup = _build_deduplicated_dataframe(df_unfiltered)
    df_excluded_status_dedup = _build_deduplicated_dataframe(df_excluded_status)

    # Update statistics with unfiltered counts
    statistics["file_hash"] = file_hash[:8]
    statistics["deduplicated_rows"] = len(df_dedup)
    statistics["unfiltered_rows"] = len(df_unfiltered)
    statistics["unfiltered_deduplicated_rows"] = len(df_unfiltered_dedup)
    statistics["filtered_out_rows"] = len(df_unfiltered) - len(df)
    statistics["filtered_out_status_rows"] = len(df_excluded_status)
    statistics["excluded_status_rows"] = len(df_excluded_status)
    statistics["excluded_status_deduplicated_rows"] = len(df_excluded_status_dedup)

    cache_payload = {
        "data": df_to_json_safe(df),
        "columns": df.columns.tolist(),
        "deduplicated": {
            "data": df_to_json_safe(df_dedup),
            "columns": df_dedup.columns.tolist(),
        },
        "unfiltered": {
            "data": df_to_json_safe(df_unfiltered),
            "columns": df_unfiltered.columns.tolist(),
        },
        "unfiltered_deduplicated": {
            "data": df_to_json_safe(df_unfiltered_dedup),
            "columns": df_unfiltered_dedup.columns.tolist(),
        },
        "excluded_status": {
            "data": df_to_json_safe(df_excluded_status),
            "columns": df_excluded_status.columns.tolist(),
        },
        "excluded_status_deduplicated": {
            "data": df_to_json_safe(df_excluded_status_dedup),
            "columns": df_excluded_status_dedup.columns.tolist(),
        },
        "statistics": statistics,
        "cache_version": KARTVERKET_CACHE_VERSION,
    }
    save_kartverket_cache(cache_payload, file_hash, kommune_name, source=cache_source)

    return KartverketDataset(
        data_df=df,
        data_dedup_df=df_dedup,
        unfiltered_df=df_unfiltered,
        unfiltered_dedup_df=df_unfiltered_dedup,
        excluded_status_df=df_excluded_status,
        excluded_status_dedup_df=df_excluded_status_dedup,
        statistics=statistics,
        file_path=file_path
    )


def create_knr_gnr_bnr(row: pd.Series) -> str:
    """Create Knr-Gnr-Bnr string from Kommunenummer, Gardsnummer, Bruksnummer columns."""
    if pd.notna(row.get(Col.KOMMUNE_NR)) and pd.notna(row.get(Col.GARDS_NR)) and pd.notna(row.get(Col.BRUKS_NR)):
        return f"{int(row[Col.KOMMUNE_NR])}-{int(row[Col.GARDS_NR])}-{int(row[Col.BRUKS_NR])}"
    return ""


def add_knr_gnr_bnr_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add Knr-Gnr-Bnr column to dataframe."""
    df = df.copy()
    df[Col.KNR_GNR_BNR] = df.apply(create_knr_gnr_bnr, axis=1)
    return df


def normalize_eiendom(eiendom_value: str) -> str:
    """
    Normalize Eiendom column value from knr-gnr-bnr-fnr-snr to knr-gnr-bnr.

    Args:
        eiendom_value: String in format "knr-gnr-bnr-fnr-snr"

    Returns:
        String in format "knr-gnr-bnr"
    """
    if pd.isna(eiendom_value) or not eiendom_value:
        return ""

    parts = str(eiendom_value).split("-")
    if len(parts) >= 3:
        return f"{parts[0]}-{parts[1]}-{parts[2]}"
    return str(eiendom_value)


def is_valid_knr_gnr_bnr(value) -> bool:
    """Check if Knr-Gnr-Bnr value is valid (not empty, null, or just a dash)."""
    if pd.isna(value):
        return False
    str_value = str(value).strip()
    return str_value != "" and str_value != "-"


def format_nummer(value) -> str:
    """Format Nummer (house number) value, converting floats to integers."""
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def add_address_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add combined Adresse column from Adressenavn and Nummer."""
    if Col.ADRESSENAVN not in df.columns or Col.NUMMER not in df.columns:
        return df

    df = df.copy()
    df[Col.ADRESSE] = df.apply(
        lambda row: f"{row[Col.ADRESSENAVN]} {format_nummer(row[Col.NUMMER])}" if pd.notna(row[Col.ADRESSENAVN]) and pd.notna(row[Col.NUMMER])
        else (row[Col.ADRESSENAVN] if pd.notna(row[Col.ADRESSENAVN]) else ""),
        axis=1
    )
    return df

def get_enriched_kartverket_data(
    kommune_name: str,
    data_source: KartverketDataSource = "raw",
) -> tuple[pd.DataFrame, dict] | tuple[None, None]:
    """
    Get fully processed and enriched Kartverket data for a kommune.

    This is the main entry point for getting Kartverket data.
    The BuildingOwnership sheet is pre-filtered and pre-merged.

    Note: Column names from KartverketAPI are already in Norwegian API format.

    Args:
        kommune_name: Name of the kommune

    Returns:
        Tuple of (processed dataframe, statistics dict) or (None, None) if not found
    """
    dataset = build_kartverket_dataset(
        kommune_name,
        source_dir=resolve_kartverket_source_dir(data_source),
    )
    if not dataset:
        return None, None
    return dataset.data_df, dataset.statistics


def add_simplified_category_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add building category names (Hovedgruppe/Bygningsgruppe/Bygningstype) and
    simplified category based on available building type codes.

    Args:
        df: DataFrame with BygningstypeKodeSSB and/or BygningstypeKodeId columns

    Returns:
        DataFrame with populated category name columns
    """
    if (
        Col.BYGNINGSTYPE_KODE_SSB not in df.columns
        and Col.BYGNINGSTYPE_KODE_ID not in df.columns
    ):
        return df

    df = df.copy()

    def _safe_int(value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            value = stripped
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _resolve_ssb_code(row: pd.Series) -> int | None:
        ssb_code = _safe_int(row.get(Col.BYGNINGSTYPE_KODE_SSB))
        if ssb_code is not None:
            return ssb_code
        internal_id = _safe_int(row.get(Col.BYGNINGSTYPE_KODE_ID))
        if internal_id is None:
            return None
        return INTERNAL_ID_TO_NS3457.get(internal_id)

    ssb_resolved = df.apply(_resolve_ssb_code, axis=1)

    if Col.BYGNINGSTYPE_KODE_SSB not in df.columns:
        df[Col.BYGNINGSTYPE_KODE_SSB] = ssb_resolved
    else:
        existing_ssb = df[Col.BYGNINGSTYPE_KODE_SSB].apply(_safe_int)
        missing_ssb = existing_ssb.isna()
        df.loc[missing_ssb, Col.BYGNINGSTYPE_KODE_SSB] = ssb_resolved[missing_ssb]

    def _resolve_hierarchy(row: pd.Series) -> tuple[str, str, str]:
        internal_id = _safe_int(row.get(Col.BYGNINGSTYPE_KODE_ID))
        result = get_building_type_hierarchy(internal_id) if internal_id is not None else ("", "", "")
        if not isinstance(result, (tuple, list)) or len(result) != 3:
            return ("", "", "")
        return (result[0] or "", result[1] or "", result[2] or "")

    hierarchy_values = df.apply(_resolve_hierarchy, axis=1)
    hierarchy = pd.DataFrame(
        hierarchy_values.tolist(),
        index=df.index,
        columns=[Col.HOVEDGRUPPE, Col.BYGNINGSGRUPPE, Col.BYGNINGSTYPE],
    )

    def _is_missing(value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, float) and pd.isna(value):
            return True
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"", "-", "nan", "<na>", "none", "null"}:
                return True
        return False

    for col in (Col.HOVEDGRUPPE, Col.BYGNINGSGRUPPE, Col.BYGNINGSTYPE):
        if col not in df.columns:
            df[col] = ""
        elif df[col].dtype != object:
            df[col] = df[col].astype("object")
        missing_mask = df[col].apply(_is_missing)
        df.loc[missing_mask, col] = hierarchy.loc[missing_mask, col]

    simplified = ssb_resolved.apply(lambda value: get_simplified_building_category(_safe_int(value)))
    if Col.FORENKLET_BYGNINGS_KATEGORI not in df.columns:
        df[Col.FORENKLET_BYGNINGS_KATEGORI] = simplified
    else:
        if df[Col.FORENKLET_BYGNINGS_KATEGORI].dtype != object:
            df[Col.FORENKLET_BYGNINGS_KATEGORI] = df[Col.FORENKLET_BYGNINGS_KATEGORI].astype("object")
        missing_mask = df[Col.FORENKLET_BYGNINGS_KATEGORI].apply(_is_missing)
        df.loc[missing_mask, Col.FORENKLET_BYGNINGS_KATEGORI] = simplified[missing_mask]
    df[Col.FORENKLET_BYGNINGS_KATEGORI] = df[Col.FORENKLET_BYGNINGS_KATEGORI].apply(
        normalize_simplified_building_category
    )

    return df
