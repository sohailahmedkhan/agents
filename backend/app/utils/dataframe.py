"""Shared DataFrame helpers used across services and routers."""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.columns import Col


def extract_kommune_name(filename: str) -> str:
    """Extract kommune name from filename.

    Expected format: KommuneName_* (kommune name as first underscore segment)

    Args:
        filename: The uploaded file name

    Returns:
        Kommune name or empty string if pattern doesn't match
    """
    if not filename:
        return ""

    name_without_ext = filename.rsplit(".", 1)[0] if "." in filename else filename
    parts = name_without_ext.split("_")
    if len(parts) >= 1:
        return parts[0]

    return ""


def extract_kartverket_kommune_name(file_path: str | Path) -> str:
    """Extract kommune name from a Kartverket filename/path.

    Expected formats:
    - {KNR}_{Kommune}_Properties.xlsx
    - {KNR}_{Kommune}_Properties_Imputed.xlsx
    """
    path = Path(file_path)
    parts = path.stem.split("_")
    if len(parts) >= 2:
        core_parts = parts
        if len(core_parts) >= 2 and core_parts[-1].lower() == "imputed" and core_parts[-2].lower() == "properties":
            core_parts = core_parts[:-2]
        elif core_parts[-1].lower() == "properties":
            core_parts = core_parts[:-1]

        kommune_parts = core_parts[1:] if len(core_parts) > 1 else []
        if kommune_parts:
            return "_".join(kommune_parts)
        return parts[1]
    return path.stem




def df_to_json_safe(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame to JSON-safe list of dicts.

    Handles NA values and float-to-int conversion.

    Args:
        df: DataFrame to convert

    Returns:
        List of dictionaries with proper JSON-safe values
    """
    df = df.fillna(value=pd.NA)
    result_dict = df.to_dict(orient="records")

    for row in result_dict:
        for key, value in row.items():
            if isinstance(value, (list, dict)):
                continue
            if isinstance(value, float) and not math.isfinite(value):
                row[key] = None
            elif pd.isna(value):
                row[key] = None
            elif isinstance(value, float) and value.is_integer():
                row[key] = int(value)

    return result_dict


def deduplicate_by_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where DuplikatFlagg contains 'Duplicate'.

    This filters out duplicate entries, keeping only:
    - Rows with 'Unique' flag
    - Rows with 'Primary' flag (Primary of a duplicate group)
    - Rows with 'Extension' flag

    Args:
        df: DataFrame with optional 'DuplikatFlagg' column

    Returns:
        DataFrame with duplicate rows removed
    """
    if Col.DUPLIKAT_FLAGG not in df.columns:
        return df
    mask = ~df[Col.DUPLIKAT_FLAGG].fillna("").astype(str).str.contains("Duplicate", case=False)
    return df[mask].copy()


def _parse_underenheter_entries(value: str, address: str | None) -> list[dict[str, Any]]:
    """Parse Underenheter string into structured entries.

    Args:
        value: Raw Underenheter string value.
        address: Optional address to attach to each entry.

    Returns:
        List of parsed entry dictionaries with name, industry, code, and address.
    """
    if value is None or pd.isna(value):
        return []
    value_str = str(value).strip()
    if value_str == "" or value_str == "-":
        return []
    if value_str.lower() in {"nan", "<na>"}:
        return []

    entries: list[dict[str, Any]] = []
    parts = [part.strip() for part in str(value).split(";") if part.strip()]
    pattern = re.compile(r"^(.+?)\s*\[(.+),\s*(\d+(?:\.\d+)?)\]$")

    for part in parts:
        match = pattern.match(part)
        if match:
            name, industry, code = match.groups()
            entries.append({
                "name": name.strip(),
                "industry": industry.strip(),
                "code": code.strip(),
                "address": address,
            })
        else:
            entries.append({
                "name": part,
                "industry": "",
                "code": "",
                "address": address,
            })

    return entries


def merge_underenheter_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """Merge Underenheter across duplicate groups and filter Duplicate rows."""
    if Col.DUPLIKAT_FLAGG not in df.columns or Col.DUPLIKAT_GRUPPE not in df.columns:
        return df

    grouped: dict[str, list[dict[str, Any]]] = {}
    for _, row in df.iterrows():
        group_value = row.get(Col.DUPLIKAT_GRUPPE)
        group_value_str = "" if group_value is None else str(group_value).strip()
        if group_value is None or pd.isna(group_value) or group_value_str == "" or group_value_str.lower() == "nan":
            continue
        key = group_value_str
        grouped.setdefault(key, []).append(row.to_dict())

    merged_by_group: dict[str, list[dict[str, Any]]] = {}
    for group_key, rows in grouped.items():
        all_entries: list[dict[str, Any]] = []
        for row in rows:
            addr_value = row.get(Col.ADRESSE)
            if addr_value is None or pd.isna(addr_value):
                row_address = None
            else:
                addr_str = str(addr_value).strip()
                row_address = None if addr_str.lower() in {"nan", "<na>"} or addr_str == "" else addr_str
            all_entries.extend(_parse_underenheter_entries(row.get(Col.UNDERENHETER, ""), row_address))

        seen_names = set()
        unique_entries: list[dict[str, Any]] = []
        for entry in all_entries:
            name = entry.get("name")
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            unique_entries.append(entry)

        merged_by_group[group_key] = unique_entries

    result_rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        duplicate_flag = row.get(Col.DUPLIKAT_FLAGG)
        if duplicate_flag is not None and not pd.isna(duplicate_flag):
            flag_str = str(duplicate_flag).strip()
            if flag_str and flag_str.lower() != "nan" and "duplicate" in flag_str.lower():
                continue

        group_value = row.get(Col.DUPLIKAT_GRUPPE)
        group_value_str = "" if group_value is None else str(group_value).strip()
        if group_value is None or pd.isna(group_value) or group_value_str == "" or group_value_str.lower() == "nan":
            result_rows.append(row.to_dict())
            continue

        group_key = group_value_str
        merged_entries = merged_by_group.get(group_key, [])
        if not merged_entries:
            result_rows.append(row.to_dict())
            continue

        underenheter_value = "; ".join([
            f"{entry['name']} [{entry['industry']}, {entry['code']}]"
            if entry.get("industry") and entry.get("code")
            else entry.get("name", "")
            for entry in merged_entries
        ])

        updated = row.to_dict()
        updated[Col.UNDERENHETER] = underenheter_value
        updated[Col.ANTALL_UNDERENHETER] = len(merged_entries)
        updated["_parsedUnderenheter"] = merged_entries
        result_rows.append(updated)

    return pd.DataFrame(result_rows)
