#!/usr/bin/env python3
"""Load full Kartverket BuildingOwnership sheets into DuckDB `main.properties`.

This loader reads the `BuildingOwnership` sheet from each file matching:
`1234_Kommune_Name_Properties.xlsx` (or `_Imputed` variant), adds metadata,
and rebuilds `main.properties` from scratch.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.columns import Col
from app.modules.kartverket.service import build_kartverket_dataset  # type: ignore


def _project_roots() -> Path:
    """Return `agents_root` based on this script location."""
    backend_root = Path(__file__).resolve().parents[1]
    agents_root = backend_root.parent
    return agents_root


def _default_paths() -> tuple[Path, Path]:
    """Build default paths for source dir and db file."""
    agents_root = _project_roots()
    source_dir = agents_root / "data" / "excel" / "raw" / "kartverket"
    duckdb_path = agents_root / "data" / "db" / "agents.duckdb"
    return source_dir, duckdb_path


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    source_dir, duckdb_path = _default_paths()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=source_dir)
    parser.add_argument("--duckdb-path", type=Path, default=duckdb_path)
    return parser.parse_args()


def _extract_kommune_name(file_path: Path) -> str:
    """Extract kommune name from `1234_Kommune_Name_Properties*.xlsx`."""
    match = re.match(r"^\d{4}_(.+?)_Properties(?:_Imputed)?$", file_path.stem, flags=re.IGNORECASE)
    if not match:
        return file_path.stem.replace("_", " ").strip()
    kommune_raw = match.group(1).split("___", 1)[0]
    return kommune_raw.replace("_", " ").strip()


def _format_kommune_label(kommune_name: str) -> str:
    """Normalize kommune label and ensure it ends with `Kommune`."""
    name = " ".join(str(kommune_name).split()).strip()
    if not name:
        return "Ukjent Kommune"
    if name.lower().endswith(" kommune"):
        return name
    return f"{name} Kommune"


def _load_frames(
    source_dir: Path,
) -> tuple[pd.DataFrame, list[tuple[str, int, int, int]]]:
    """Read filtered/deduplicated Kartverket frames from copied Proactive pipeline."""
    excel_files = sorted(source_dir.glob("*_Properties*.xlsx"))
    frames: list[pd.DataFrame] = []
    processed_sources: list[tuple[str, int, int, int]] = []
    loaded_files: set[Path] = set()

    for file_path in excel_files:
        if file_path.name.startswith("~$"):
            continue

        kommune_name_raw = _extract_kommune_name(file_path)
        dataset = build_kartverket_dataset(kommune_name=kommune_name_raw, source_dir=source_dir)
        if dataset is None:
            continue

        resolved_file = dataset.file_path.resolve()
        if resolved_file in loaded_files:
            continue
        loaded_files.add(resolved_file)

        df = dataset.data_dedup_df.copy()
        kommune_name = _format_kommune_label(kommune_name_raw)
        source = f"kartverket:{dataset.file_path.name}"

        alt_flag_col = Col.ALT_ADRESSER_FRA_KNR_GNR_BNR
        alt_filled_count = int(df[alt_flag_col].fillna(False).astype(bool).sum()) if alt_flag_col in df.columns else 0
        removed_count = int(len(dataset.data_df) - len(dataset.data_dedup_df))

        df.insert(0, "source", source)
        df.insert(0, "kommune", kommune_name)
        frames.append(df)
        processed_sources.append((source, len(df), removed_count, alt_filled_count))

    if not frames:
        return pd.DataFrame(columns=["kommune", "source"]), processed_sources
    return pd.concat(frames, ignore_index=True), processed_sources


def _rebuild_properties_table(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    """Replace `main.properties` with fresh data and zero-based IDs."""
    conn.execute("DROP TABLE IF EXISTS main.properties")
    conn.execute("DROP SEQUENCE IF EXISTS properties_id_seq")
    conn.execute("CREATE SEQUENCE properties_id_seq MINVALUE 0 START 0")

    conn.register("staging_properties", df)
    try:
        conn.execute(
            """
            CREATE TABLE main.properties AS
            SELECT
              nextval('properties_id_seq')::BIGINT AS id,
              kommune,
              s.* EXCLUDE (kommune)
            FROM staging_properties s
            """
        )
    finally:
        conn.unregister("staging_properties")

    # Keep hard uniqueness on id even when CTAS is used.
    conn.execute("CREATE UNIQUE INDEX idx_properties_id_unique ON main.properties (id)")


def main() -> int:
    """Run filtered Kartverket pipeline -> DuckDB load for all files in source dir."""
    args = _parse_args()
    source_dir = args.source_dir.resolve()
    duckdb_path = args.duckdb_path.resolve()

    if not source_dir.exists():
        print(f"Source directory does not exist: {source_dir}")
        return 1

    df, processed_sources = _load_frames(source_dir=source_dir)
    if not processed_sources:
        print(f"No Kartverket files found in {source_dir}")
        return 0

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(duckdb_path))
    try:
        _rebuild_properties_table(conn=conn, df=df)
        total_rows = conn.execute("SELECT COUNT(*) FROM main.properties").fetchone()[0]
    finally:
        conn.close()

    inserted_total = len(df)
    for source, count, removed_count, alt_filled_count in processed_sources:
        print(
            f"Loaded {count} rows from {source} "
            f"(removed duplicates: {removed_count}, alt-address backfilled: {alt_filled_count})"
        )
    print(f"\nInserted rows this run: {inserted_total}")
    print(f"Total rows currently in properties: {total_rows}")
    print(f"DuckDB path: {duckdb_path}")
    print("Pipeline loaded: build_kartverket_dataset(data_dedup_df)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
