"""
File caching service for address processing.

This module provides caching functionality for:
1. Saving and finding raw uploaded files (Excel, JSON)
2. Saving and retrieving processed results
3. Content-based deduplication using SHA256 hashes
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Get the project root directory
BACKEND_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Directory paths for data storage (absolute paths) - stored in project root
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "norway" / "user_data"
CACHE_ROOT = PROJECT_ROOT / "data" / "cache"
USER_CACHE_DIR = CACHE_ROOT / "user"
KARTVERKET_CACHE_DIR = CACHE_ROOT / "kartverket"
KARTVERKET_IMPUTED_CACHE_DIR = CACHE_ROOT / "kartverket_imputed"
MATCH_CACHE_DIR = CACHE_ROOT / "match"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
USER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
KARTVERKET_CACHE_DIR.mkdir(parents=True, exist_ok=True)
KARTVERKET_IMPUTED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MATCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA256 hash of file content for cache identification.

    Args:
        file_content: Raw file bytes

    Returns:
        Hex string of SHA256 hash
    """
    return hashlib.sha256(file_content).hexdigest()


def write_json_atomic(path: Path, payload: Any) -> None:
    """Write JSON atomically to avoid partial-file cache corruption."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def write_text_atomic(path: Path, content: str) -> None:
    """Write text atomically to avoid partial-file reads."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            f.write(content)
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def normalize_rows_for_hashing(rows: list) -> list:
    """
    Normalize rows for consistent hashing by removing volatile fields.

    Args:
        rows: List of row dictionaries

    Returns:
        List of normalized row dictionaries (without uniqueRowID and other volatile fields)
    """
    normalized = []
    for row in rows:
        # Remove uniqueRowID and any other fields that might vary between uploads
        normalized_row = {k: v for k, v in row.items() if k not in ['uniqueRowID', 'UniqueRowID', 'unique_row_id']}
        normalized.append(normalized_row)
    return normalized


def calculate_data_hash(rows: list) -> str:
    """
    Calculate SHA256 hash of normalized data rows for caching.

    Args:
        rows: List of row dictionaries

    Returns:
        Hex string of SHA256 hash
    """
    normalized_rows = normalize_rows_for_hashing(rows)
    sorted_rows = sorted(normalized_rows, key=lambda x: json.dumps(x, sort_keys=True))
    data_str = json.dumps(sorted_rows, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()


def _build_cache_filename(file_hash: str, kommune_name: str) -> str:
    """Build cache filename using kommune name + hash prefix."""
    hash_prefix = file_hash[:8]
    if kommune_name:
        return f"{kommune_name}_{hash_prefix}.json"
    return f"unknown_{hash_prefix}.json"


def _load_cached_result(
    cache_dir: Path,
    file_hash: str,
    kommune_name: str,
    *,
    require_data_key: bool = True,
) -> dict | None:
    """Load cached result from a specific cache directory."""
    if not cache_dir.exists():
        return None
    cache_path = cache_dir / _build_cache_filename(file_hash, kommune_name)
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)

        # Validate basic structure
        if not isinstance(cached_data, dict):
            logger.warning(f"Invalid cache format (not a dict): {cache_path.name}")
            return None

        # Validate required top-level fields (some caches store non-table payloads)
        if require_data_key and "data" not in cached_data:
            logger.warning(f"Invalid cache structure (missing data): {cache_path.name}")
            return None

        logger.info(f"Valid cache hit: {cache_path.name}")
        return cached_data

    except json.JSONDecodeError as e:
        logger.error(f"Corrupted cache file: {cache_path.name} - {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading cache: {cache_path.name} - {e}")
        return None


def _save_cached_result(cache_dir: Path, result_data: dict, file_hash: str, kommune_name: str) -> Path:
    """Save processed result to a specific cache directory."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_filename = _build_cache_filename(file_hash, kommune_name)
    cache_path = cache_dir / cache_filename

    write_json_atomic(cache_path, result_data)

    logger.info(f"Saved cache: {cache_filename}")
    return cache_path


def find_existing_raw_file(file_hash: str, source_type: str | None = None) -> Path | None:
    """
    Check if a raw file with the same content hash already exists.

    This function searches for files in RAW_DATA_DIR with matching hash prefix,
    optionally filtering by source type (excel, json, or bigquery).

    Args:
        file_hash: SHA256 hash of file content (full hash or prefix)
        source_type: Optional source type filter ("excel", "json", "bigquery")
                    If None, searches across all source types

    Returns:
        Path to existing file if found, None otherwise
    """
    hash_prefix = file_hash[:8]

    # If source_type is specified, search for that specific pattern
    if source_type:
        # Look for files with pattern: *_{source_type}_{hash}.*
        for file_path in RAW_DATA_DIR.glob(f"*_{source_type}_{hash_prefix}.*"):
            return file_path

        # Check old naming pattern for backwards compatibility (excel only)
        if source_type == "excel":
            for file_path in RAW_DATA_DIR.glob(f"*_{hash_prefix}.*"):
                # Skip bigquery and json files
                if "_bigquery_" not in file_path.name and "_json_" not in file_path.name:
                    return file_path
    else:
        # Search across all source types
        for source in ["bigquery", "excel", "json"]:
            for file_path in RAW_DATA_DIR.glob(f"*_{source}_{hash_prefix}.*"):
                return file_path

        # Check old naming pattern for backwards compatibility
        for file_path in RAW_DATA_DIR.glob(f"*_{hash_prefix}.*"):
            return file_path

    return None


def save_raw_file(file_content: bytes, kommune_name: str, original_filename: str, file_hash: str) -> tuple[Path, bool]:
    """
    Save uploaded Excel file to raw data directory, or return existing file if duplicate.

    Naming convention: {KommuneName}_excel_{hash_prefix}.xlsx

    Args:
        file_content: Raw file bytes to save
        kommune_name: Kommune name extracted from filename
        original_filename: Original filename for extension extraction
        file_hash: SHA256 hash of file content

    Returns:
        Tuple of (Path to file, whether file was newly created)
    """
    # Check if file with same content hash already exists
    existing_file = find_existing_raw_file(file_hash, source_type="excel")
    if existing_file:
        logger.info(f"Duplicate Excel file detected - reusing: {existing_file.name}")
        return existing_file, False

    # Extract file extension from original filename
    ext = Path(original_filename).suffix if original_filename else ".xlsx"

    # Create standardized filename
    hash_prefix = file_hash[:8]
    filename = f"{kommune_name}_excel_{hash_prefix}{ext}" if kommune_name else f"unknown_excel_{hash_prefix}{ext}"

    # Write file content to disk
    file_path = RAW_DATA_DIR / filename
    with open(file_path, "wb") as f:
        f.write(file_content)

    logger.info(f"Saved new Excel file: {filename}")
    return file_path, True


def get_cached_result(file_hash: str, kommune_name: str) -> dict | None:
    """
    Check if processed result exists in cache.

    Cache filename format: {KommuneName}_{hash_prefix}.json

    Args:
        file_hash: SHA256 hash of input file content (full hash)
        kommune_name: Kommune name for organization

    Returns:
        Cached result dictionary if valid cache exists, None otherwise
    """
    # Check new cache directory first
    cached = _load_cached_result(USER_CACHE_DIR, file_hash, kommune_name)
    if cached:
        # Ensure expected fields for user processing cache
        if "success" not in cached:
            logger.warning("User cache missing 'success' field. Ignoring.")
        else:
            return cached

    return None


def save_to_cache(result_data: dict, file_hash: str, kommune_name: str) -> Path:
    """
    Save processed result to cache for future requests.

    Cache filename format: {KommuneName}_{hash_prefix}.json

    Args:
        result_data: Processed result dictionary
        file_hash: SHA256 hash of input file content
        kommune_name: Kommune name for organization

    Returns:
        Path to the saved cache file
    """
    return _save_cached_result(USER_CACHE_DIR, result_data, file_hash, kommune_name)


def _resolve_kartverket_cache_dir(source: str) -> Path:
    """Resolve Kartverket cache directory for a given source."""
    if source == "imputed":
        return KARTVERKET_IMPUTED_CACHE_DIR
    return KARTVERKET_CACHE_DIR


def get_kartverket_cached_result(file_hash: str, kommune_name: str, source: str = "raw") -> dict | None:
    """Check if a Kartverket processed result exists in cache."""
    cache_dir = _resolve_kartverket_cache_dir(source)
    cached = _load_cached_result(cache_dir, file_hash, kommune_name)
    if cached:
        return cached
    return None

def save_kartverket_cache(result_data: dict, file_hash: str, kommune_name: str, source: str = "raw") -> Path:
    """Save Kartverket processed result to cache."""
    cache_dir = _resolve_kartverket_cache_dir(source)
    return _save_cached_result(cache_dir, result_data, file_hash, kommune_name)


def get_match_cached_result(file_hash: str, kommune_name: str) -> dict | None:
    """Check if a match-enrichment result exists in cache."""
    cached = _load_cached_result(MATCH_CACHE_DIR, file_hash, kommune_name, require_data_key=False)
    if cached:
        return cached
    return None


def save_match_cache(result_data: dict, file_hash: str, kommune_name: str) -> Path:
    """Save match-enrichment result to cache."""
    return _save_cached_result(MATCH_CACHE_DIR, result_data, file_hash, kommune_name)
