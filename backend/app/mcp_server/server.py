"""DuckDB MCP server implementation.

This server exposes:
1) direct DuckDB tools (`duckdb_*`) for practical query execution
2) DuckDB-MCP-extension-style compatibility tools (`mcp_*`)
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Callable

from app.core.db_limits import DB_DEFAULT_RESULT_ROWS
from app.core.settings import AppSettings
from app.db.duckdb_service import DuckDBService
from app.mcp_server.contracts import DUCKDB_CALL_TARGETS, MCP_RESOURCES, MCP_TOOLS

try:
    from fastmcp import FastMCP
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    FastMCP = None  # type: ignore[assignment]


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _normalize_args(args: Any) -> dict[str, Any]:
    if args is None:
        return {}
    if isinstance(args, dict):
        return dict(args)
    if isinstance(args, str):
        payload = args.strip()
        if not payload:
            return {}
        try:
            loaded = json.loads(payload)
        except json.JSONDecodeError:
            return {"value": args}
        return loaded if isinstance(loaded, dict) else {"value": loaded}
    return {"value": args}


def _split_table_name(name: str) -> tuple[str, str]:
    value = str(name or "").strip()
    if not value:
        raise ValueError("table is required.")
    if "." in value:
        schema, table = value.split(".", 1)
    else:
        schema, table = "main", value
    return schema.strip(), table.strip()


def create_duckdb_mcp_server(
    settings: AppSettings | None = None,
    duckdb: DuckDBService | None = None,
) -> Any:
    """Build an MCP server exposing DuckDB tools/resources."""
    if FastMCP is None:
        raise RuntimeError("fastmcp is not installed. Install backend requirements first.")

    resolved = settings or AppSettings.from_env()
    duckdb_service = duckdb or DuckDBService(
        db_path=resolved.duckdb_path,
        read_only=resolved.duckdb_read_only,
        allow_write=resolved.duckdb_allow_write,
    )
    mcp = FastMCP(name="duckdb-mcp-server")

    runtime_state: dict[str, Any] = {
        "running": True,
        "transport": "stdio",
        "host": "127.0.0.1",
        "port": 8200,
    }
    published_resources: dict[str, dict[str, Any]] = {}
    published_queries: dict[str, dict[str, Any]] = {}
    published_tools: dict[str, dict[str, Any]] = {}
    prompt_templates: dict[str, dict[str, str]] = {
        "sql_analysis": {
            "template": "Analyze this SQL result for municipality insights:\n{result}",
            "description": "Summarize and interpret SQL query results.",
        }
    }

    tool_dispatch: dict[str, Callable[..., Any]] = {}

    def _tool_catalog() -> list[dict[str, Any]]:
        catalog = [dict(item) for item in MCP_TOOLS]
        for target in DUCKDB_CALL_TARGETS:
            if not any(entry["name"] == target["name"] for entry in catalog):
                catalog.append(dict(target))
        for name, data in published_tools.items():
            if not any(entry["name"] == name for entry in catalog):
                catalog.append({"name": name, "description": str(data.get("description", ""))})
        return catalog

    def _call_target_catalog() -> list[dict[str, Any]]:
        catalog = [dict(item) for item in DUCKDB_CALL_TARGETS]
        for name, data in published_tools.items():
            if data.get("target_tool") and not any(entry["name"] == name for entry in catalog):
                catalog.append({"name": name, "description": str(data.get("description", ""))})
        return catalog

    def _resource_catalog() -> list[dict[str, Any]]:
        catalog = [dict(item) for item in MCP_RESOURCES]
        for uri, data in published_resources.items():
            catalog.append(
                {
                    "uri": uri,
                    "name": str(data.get("name", uri)),
                    "description": str(data.get("description", "Published MCP resource.")),
                }
            )
        for uri, data in published_queries.items():
            catalog.append(
                {
                    "uri": uri,
                    "name": str(data.get("name", uri)),
                    "description": str(data.get("description", "Published SQL-backed MCP resource.")),
                }
            )
        return catalog

    def _resolve_resource(uri: str) -> Any:
        if uri == "duckdb://health":
            return duckdb_service.health()
        if uri == "duckdb://tables":
            return duckdb_service.list_tables()
        if uri == "duckdb://tools":
            return _tool_catalog()
        if uri == "duckdb://tool-targets":
            return _call_target_catalog()

        if uri.startswith("duckdb://table/"):
            path = uri[len("duckdb://table/") :].strip("/")
            if not path:
                raise ValueError("duckdb://table resource requires table path.")
            if "/" in path:
                schema, table = path.split("/", 1)
                relation = f'"{schema}"."{table}"'
            else:
                relation = f'"{path}"'
            sql = f"SELECT * FROM {relation} LIMIT {DB_DEFAULT_RESULT_ROWS}"
            return duckdb_service.query(sql=sql, params=None, limit=DB_DEFAULT_RESULT_ROWS)

        if uri in published_queries:
            entry = published_queries[uri]
            return duckdb_service.query(
                sql=str(entry.get("sql", "")),
                params=entry.get("params"),
                limit=int(entry.get("limit", DB_DEFAULT_RESULT_ROWS)),
            )

        if uri in published_resources:
            return published_resources[uri].get("content")

        raise FileNotFoundError(f"Unknown resource URI: {uri}")

    def duckdb_health() -> dict[str, Any]:
        """Return DuckDB connection health metadata."""
        return duckdb_service.health()

    def duckdb_list_tables() -> list[dict[str, str]]:
        """Return a list of user-visible DuckDB tables."""
        return duckdb_service.list_tables()

    def duckdb_describe_table(schema: str, table: str) -> dict[str, Any]:
        """Describe one table's columns from information_schema."""
        sql = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = ?
        ORDER BY ordinal_position
        """
        result = duckdb_service.query(sql=sql, params=[schema, table], limit=500)
        return {
            "schema": schema,
            "table": table,
            "columns": [
                {"name": str(row[0]), "type": str(row[1]), "nullable": str(row[2])}
                for row in result["rows"]
            ],
        }

    def duckdb_query(sql: str, params: list[Any] | None = None, limit: int = DB_DEFAULT_RESULT_ROWS) -> dict[str, Any]:
        """Execute a bounded SQL query against DuckDB."""
        return duckdb_service.query(sql=sql, params=params, limit=limit)

    def _normalized_kommune_expr(column_ref: str) -> str:
        return (
            f"lower(trim(replace(replace({column_ref}, ' Kommune', ''), ' kommune', '')))"
        )

    def duckdb_kommune_occupancy_distribution(kommune_name: str, limit: int = 30) -> dict[str, Any]:
        """Return occupancy distribution for one kommune using area share by category."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        if limit < 1 or limit > 500:
            raise ValueError("limit must be in range [1, 500].")

        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")
        sql = f"""
        WITH grouped AS (
          SELECT
            "Forenklet Bygningskategori" AS occupancy_category,
            COUNT(*) AS building_count,
            SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
          FROM main.properties
          WHERE {kommune_expr} = {param_expr}
            AND "Forenklet Bygningskategori" IS NOT NULL
            AND trim("Forenklet Bygningskategori") <> ''
          GROUP BY 1
        )
        SELECT
          occupancy_category,
          building_count,
          total_bruksareal,
          ROUND(
            100.0 * total_bruksareal / NULLIF(SUM(total_bruksareal) OVER (), 0),
            2
          ) AS share_percent
        FROM grouped
        ORDER BY total_bruksareal DESC, occupancy_category
        LIMIT ?
        """
        result = duckdb_service.query(sql=sql, params=[normalized, int(limit)], limit=limit)
        return {
            "kommune_name": normalized,
            "metric": "occupancy_distribution",
            "result": result,
        }

    def duckdb_kommune_largest_occupancy_area(kommune_name: str) -> dict[str, Any]:
        """Return the largest occupancy category by summed `BruksarealTotalt`."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")

        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")
        sql = f"""
        SELECT
          "Forenklet Bygningskategori" AS occupancy_category,
          SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal,
          COUNT(*) AS building_count
        FROM main.properties
        WHERE {kommune_expr} = {param_expr}
          AND "Forenklet Bygningskategori" IS NOT NULL
          AND trim("Forenklet Bygningskategori") <> ''
        GROUP BY 1
        ORDER BY total_bruksareal DESC, building_count DESC, occupancy_category
        LIMIT 1
        """
        result = duckdb_service.query(sql=sql, params=[normalized], limit=1)
        return {
            "kommune_name": normalized,
            "metric": "largest_occupancy_by_area",
            "result": result,
        }

    def _rows_to_objects(result: dict[str, Any]) -> list[dict[str, Any]]:
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        if not isinstance(columns, list) or not isinstance(rows, list):
            return []

        out: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, list):
                continue
            item: dict[str, Any] = {}
            for idx in range(min(len(columns), len(row))):
                item[str(columns[idx])] = row[idx]
            out.append(item)
        return out

    def _query_objects(
        sql: str,
        params: list[Any] | None = None,
        limit: int = DB_DEFAULT_RESULT_ROWS,
    ) -> list[dict[str, Any]]:
        result = duckdb_service.query(sql=sql, params=params, limit=limit)
        return _rows_to_objects(result)

    def _to_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _as_int(value: Any) -> int:
        return int(round(_to_float(value)))

    def _as_round(value: Any, digits: int = 2) -> float:
        return round(_to_float(value), digits)

    def _normalize_kommune_value(value: str) -> str:
        normalized = " ".join(str(value or "").split()).strip().lower()
        if normalized.endswith(" kommune"):
            normalized = normalized[: -len(" kommune")]
        return normalized

    def _validate_limit(limit: int) -> int:
        value = int(limit)
        if value < 1 or value > DB_DEFAULT_RESULT_ROWS:
            raise ValueError(f"limit must be in range [1, {DB_DEFAULT_RESULT_ROWS}].")
        return value

    def _build_exposure_dashboard(kommune_name: str, top_n: int = 10) -> dict[str, Any]:
        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")
        params = [kommune_name]
        resolved_top_n = _validate_limit(top_n)

        portfolio_total_row = _query_objects(
            sql="""
            SELECT
              COUNT(*) AS total_properties,
              SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
            FROM main.properties
            """,
            params=None,
            limit=1,
        )[0]
        selected_total_row = _query_objects(
            sql=f"""
            SELECT
              COUNT(*) AS total_properties,
              SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
            """,
            params=params,
            limit=1,
        )[0]
        by_kommune_rows = _query_objects(
            sql=f"""
            WITH grouped AS (
              SELECT
                kommune,
                COUNT(*) AS property_count,
                SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
              FROM main.properties
              WHERE {kommune_expr} = {param_expr}
              GROUP BY 1
            ),
            totals AS (
              SELECT
                COUNT(*) AS portfolio_property_count,
                SUM(COALESCE("BruksarealTotalt", 0)) AS portfolio_total_bruksareal
              FROM main.properties
            )
            SELECT
              kommune,
              property_count,
              total_bruksareal,
              ROUND(100.0 * property_count / NULLIF(portfolio_property_count, 0), 2) AS property_share_percent,
              ROUND(100.0 * total_bruksareal / NULLIF(portfolio_total_bruksareal, 0), 2) AS area_share_percent
            FROM grouped, totals
            ORDER BY total_bruksareal DESC, property_count DESC, kommune
            """,
            params=params,
            limit=200,
        )
        normalized_selected = _normalize_kommune_value(kommune_name)
        for row in by_kommune_rows:
            row["is_selected"] = _normalize_kommune_value(str(row.get("kommune", ""))) == normalized_selected

        concentration_row = _query_objects(
            sql=f"""
            WITH ranked AS (
              SELECT
                COALESCE("BruksarealTotalt", 0) AS area,
                ROW_NUMBER() OVER (ORDER BY COALESCE("BruksarealTotalt", 0) DESC) AS rn
              FROM main.properties
              WHERE {kommune_expr} = {param_expr}
            ),
            totals AS (SELECT SUM(area) AS total_area FROM ranked)
            SELECT
              SUM(CASE WHEN rn <= 5 THEN area ELSE 0 END) AS top5_area,
              ROUND(100.0 * SUM(CASE WHEN rn <= 5 THEN area ELSE 0 END) / NULLIF(MAX(total_area), 0), 2) AS top5_share_percent,
              SUM(CASE WHEN rn <= 10 THEN area ELSE 0 END) AS top10_area,
              ROUND(100.0 * SUM(CASE WHEN rn <= 10 THEN area ELSE 0 END) / NULLIF(MAX(total_area), 0), 2) AS top10_share_percent
            FROM ranked, totals
            """,
            params=params,
            limit=1,
        )[0]

        top_properties_rows = _query_objects(
            sql=f"""
            WITH ranked AS (
              SELECT
                kommune,
                COALESCE("Adresse", "Adressenavn", '-') AS address_label,
                "Forenklet Bygningskategori" AS occupancy_category,
                COALESCE("Bygningsstatus", 'MISSING') AS bygningsstatus,
                COALESCE("TEK-standard", 'MISSING') AS tek_standard,
                COALESCE("BruksarealTotalt", 0) AS total_bruksareal,
                ROW_NUMBER() OVER (ORDER BY COALESCE("BruksarealTotalt", 0) DESC, COALESCE("Adresse", "Adressenavn", '-')) AS rn,
                SUM(COALESCE("BruksarealTotalt", 0)) OVER () AS portfolio_area
              FROM main.properties
              WHERE {kommune_expr} = {param_expr}
            )
            SELECT
              rn AS rank,
              kommune,
              address_label,
              occupancy_category,
              bygningsstatus,
              tek_standard,
              total_bruksareal,
              ROUND(100.0 * total_bruksareal / NULLIF(portfolio_area, 0), 2) AS area_share_percent
            FROM ranked
            WHERE rn <= ?
            ORDER BY rn
            """,
            params=[kommune_name, resolved_top_n],
            limit=resolved_top_n,
        )

        selected_total_area = _to_float(selected_total_row.get("total_bruksareal"))
        portfolio_total_area = _to_float(portfolio_total_row.get("total_bruksareal"))
        selected_total_properties = _as_int(selected_total_row.get("total_properties"))
        portfolio_total_properties = _as_int(portfolio_total_row.get("total_properties"))

        return {
            "portfolio_total_properties": portfolio_total_properties,
            "portfolio_total_bruksareal": _as_round(portfolio_total_area, 1),
            "selected_kommune_properties": selected_total_properties,
            "selected_kommune_bruksareal": _as_round(selected_total_area, 1),
            "selected_property_share_percent": round(
                100.0 * selected_total_properties / max(portfolio_total_properties, 1), 2
            ),
            "selected_area_share_percent": round(
                100.0 * selected_total_area / max(portfolio_total_area, 1.0), 2
            ),
            "by_kommune": by_kommune_rows,
            "concentration": {
                "top5_area": _as_round(concentration_row.get("top5_area"), 1),
                "top5_share_percent": _as_round(concentration_row.get("top5_share_percent"), 2),
                "top10_area": _as_round(concentration_row.get("top10_area"), 1),
                "top10_share_percent": _as_round(concentration_row.get("top10_share_percent"), 2),
            },
            "top_properties_by_area": top_properties_rows,
        }

    def _build_occupancy_risk_mix(kommune_name: str, limit: int = 30) -> dict[str, Any]:
        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")
        resolved_limit = _validate_limit(limit)

        by_category_rows = _query_objects(
            sql=f"""
            WITH grouped AS (
              SELECT
                "Forenklet Bygningskategori" AS occupancy_category,
                COUNT(*) AS building_count,
                SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
              FROM main.properties
              WHERE {kommune_expr} = {param_expr}
                AND "Forenklet Bygningskategori" IS NOT NULL
                AND TRIM("Forenklet Bygningskategori") <> ''
              GROUP BY 1
            )
            SELECT
              occupancy_category,
              building_count,
              total_bruksareal,
              ROUND(100.0 * building_count / NULLIF(SUM(building_count) OVER (), 0), 2) AS count_share_percent,
              ROUND(100.0 * total_bruksareal / NULLIF(SUM(total_bruksareal) OVER (), 0), 2) AS area_share_percent
            FROM grouped
            ORDER BY total_bruksareal DESC, occupancy_category
            LIMIT ?
            """,
            params=[kommune_name, resolved_limit],
            limit=resolved_limit,
        )
        top_by_count = sorted(
            [dict(row) for row in by_category_rows],
            key=lambda row: (-_to_float(row.get("building_count")), -_to_float(row.get("total_bruksareal"))),
        )[:10]
        return {
            "by_category": by_category_rows,
            "top_categories_by_area": by_category_rows[:10],
            "top_categories_by_count": top_by_count,
        }

    def _build_age_standard_proxy(kommune_name: str) -> dict[str, Any]:
        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")

        tek_distribution_rows = _query_objects(
            sql=f"""
            WITH grouped AS (
              SELECT
                COALESCE("TEK-standard", 'MISSING') AS tek_standard,
                COUNT(*) AS property_count,
                SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
              FROM main.properties
              WHERE {kommune_expr} = {param_expr}
              GROUP BY 1
            )
            SELECT
              tek_standard,
              property_count,
              total_bruksareal,
              ROUND(100.0 * property_count / NULLIF(SUM(property_count) OVER (), 0), 2) AS property_share_percent,
              ROUND(100.0 * total_bruksareal / NULLIF(SUM(total_bruksareal) OVER (), 0), 2) AS area_share_percent
            FROM grouped
            ORDER BY total_bruksareal DESC, tek_standard
            """,
            params=[kommune_name],
            limit=200,
        )
        age_band_rows = _query_objects(
            sql=f"""
            WITH grouped AS (
              SELECT
                CASE
                  WHEN "TEK-standard" IN ('TEK17', 'TEK10') THEN '2010+'
                  WHEN "TEK-standard" IN ('TEK07', 'TEK97') THEN '1997-2009'
                  WHEN "TEK-standard" LIKE 'BF%' THEN 'Pre-1997'
                  ELSE 'Unknown'
                END AS age_band,
                COUNT(*) AS property_count,
                SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
              FROM main.properties
              WHERE {kommune_expr} = {param_expr}
              GROUP BY 1
            )
            SELECT
              age_band,
              property_count,
              total_bruksareal,
              ROUND(100.0 * total_bruksareal / NULLIF(SUM(total_bruksareal) OVER (), 0), 2) AS area_share_percent
            FROM grouped
            ORDER BY
              CASE age_band
                WHEN 'Pre-1997' THEN 1
                WHEN '1997-2009' THEN 2
                WHEN '2010+' THEN 3
                ELSE 4
              END
            """,
            params=[kommune_name],
            limit=50,
        )
        return {
            "tek_distribution": tek_distribution_rows,
            "age_band_distribution": age_band_rows,
        }

    def _build_status_underwriting(kommune_name: str, limit: int = 50) -> dict[str, Any]:
        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")
        resolved_limit = _validate_limit(limit)

        distribution_rows = _query_objects(
            sql=f"""
            WITH grouped AS (
              SELECT
                COALESCE("Bygningsstatus", 'MISSING') AS bygningsstatus,
                COUNT(*) AS property_count,
                SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
              FROM main.properties
              WHERE {kommune_expr} = {param_expr}
              GROUP BY 1
            )
            SELECT
              bygningsstatus,
              property_count,
              total_bruksareal,
              ROUND(100.0 * property_count / NULLIF(SUM(property_count) OVER (), 0), 2) AS property_share_percent,
              ROUND(100.0 * total_bruksareal / NULLIF(SUM(total_bruksareal) OVER (), 0), 2) AS area_share_percent
            FROM grouped
            ORDER BY total_bruksareal DESC, bygningsstatus
            """,
            params=[kommune_name],
            limit=100,
        )
        problematic_rows = _query_objects(
            sql=f"""
            SELECT
              kommune,
              COALESCE("Adresse", "Adressenavn", '-') AS address_label,
              "Forenklet Bygningskategori" AS occupancy_category,
              "Bygningsstatus" AS bygningsstatus,
              "TEK-standard" AS tek_standard,
              COALESCE("BruksarealTotalt", 0) AS total_bruksareal
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
              AND (
                LOWER(COALESCE("Bygningsstatus", '')) LIKE '%riving%'
                OR LOWER(COALESCE("Bygningsstatus", '')) LIKE '%brenning%'
                OR LOWER(COALESCE("Bygningsstatus", '')) LIKE '%kondemn%'
                OR LOWER(COALESCE("Bygningsstatus", '')) LIKE '%ikke godkjent%'
              )
            ORDER BY total_bruksareal DESC, address_label
            LIMIT ?
            """,
            params=[kommune_name, resolved_limit],
            limit=resolved_limit,
        )
        problematic_statuses = sorted(
            {
                str(row.get("bygningsstatus", "")).strip()
                for row in distribution_rows
                if any(
                    token in str(row.get("bygningsstatus", "")).lower()
                    for token in ("riving", "brenning", "kondemn", "ikke godkjent")
                )
            }
        )
        return {
            "distribution": distribution_rows,
            "problematic_statuses": problematic_statuses,
            "problematic_properties": problematic_rows,
        }

    def _build_large_risk_schedule(kommune_name: str, limit: int = 20) -> dict[str, Any]:
        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")
        resolved_limit = _validate_limit(limit)

        rows = _query_objects(
            sql=f"""
            SELECT
              kommune,
              COALESCE("Adresse", "Adressenavn", '-') AS address_label,
              "Forenklet Bygningskategori" AS occupancy_category,
              "Bygningsstatus" AS bygningsstatus,
              "TEK-standard" AS tek_standard,
              COALESCE("BruksarealTotalt", 0) AS total_bruksareal
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
            ORDER BY total_bruksareal DESC, occupancy_category, address_label
            LIMIT ?
            """,
            params=[kommune_name, resolved_limit],
            limit=resolved_limit,
        )
        for idx, row in enumerate(rows, start=1):
            row["rank"] = idx
        return {"rows": rows}

    def _build_heritage_flags(kommune_name: str, limit: int = 50) -> dict[str, Any]:
        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")
        resolved_limit = _validate_limit(limit)

        rows = _query_objects(
            sql=f"""
            SELECT
              kommune,
              COALESCE("Adresse", "Adressenavn", '-') AS address_label,
              "Forenklet Bygningskategori" AS occupancy_category,
              COALESCE("BruksarealTotalt", 0) AS total_bruksareal,
              COALESCE("HarSefrakminne", 0) AS har_sefrakminne,
              COALESCE("HarKulturminne", 0) AS har_kulturminne,
              COALESCE("Skjermingsverdig", 0) AS skjermingsverdig
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
              AND (
                COALESCE("HarSefrakminne", 0) = 1
                OR COALESCE("HarKulturminne", 0) = 1
                OR COALESCE("Skjermingsverdig", 0) = 1
              )
            ORDER BY total_bruksareal DESC, address_label
            LIMIT ?
            """,
            params=[kommune_name, resolved_limit],
            limit=resolved_limit,
        )
        summary_row = _query_objects(
            sql=f"""
            SELECT
              SUM(CASE WHEN COALESCE("HarSefrakminne", 0) = 1 THEN 1 ELSE 0 END) AS sefrak_count,
              SUM(CASE WHEN COALESCE("HarKulturminne", 0) = 1 THEN 1 ELSE 0 END) AS kulturminne_count,
              SUM(CASE WHEN COALESCE("Skjermingsverdig", 0) = 1 THEN 1 ELSE 0 END) AS skjermingsverdig_count
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
            """,
            params=[kommune_name],
            limit=1,
        )[0]
        return {
            "summary": {
                "sefrak_count": _as_int(summary_row.get("sefrak_count")),
                "kulturminne_count": _as_int(summary_row.get("kulturminne_count")),
                "skjermingsverdig_count": _as_int(summary_row.get("skjermingsverdig_count")),
                "any_flag_count": len(rows),
            },
            "rows": rows,
        }

    def _build_tenant_activity_proxy(kommune_name: str, limit: int = 20) -> dict[str, Any]:
        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")
        resolved_limit = _validate_limit(limit)

        summary_row = _query_objects(
            sql=f"""
            SELECT
              COUNT(*) AS total_properties,
              SUM(CASE WHEN COALESCE("Antall Underenheter", 0) > 0 THEN 1 ELSE 0 END) AS with_tenants_count,
              SUM(CASE WHEN COALESCE("Antall Underenheter", 0) > 0 THEN COALESCE("BruksarealTotalt", 0) ELSE 0 END) AS with_tenants_area,
              MAX(COALESCE("Antall Underenheter", 0)) AS max_underenheter,
              SUM(CASE WHEN COALESCE("AntallEiere", 0) > 1 THEN 1 ELSE 0 END) AS multi_owner_count
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
            """,
            params=[kommune_name],
            limit=1,
        )[0]
        top_rows = _query_objects(
            sql=f"""
            SELECT
              kommune,
              COALESCE("Adresse", "Adressenavn", '-') AS address_label,
              "Forenklet Bygningskategori" AS occupancy_category,
              COALESCE("Antall Underenheter", 0) AS antall_underenheter,
              COALESCE("BruksarealTotalt", 0) AS total_bruksareal,
              COALESCE("AntallEiere", 0) AS antall_eiere,
              COALESCE("Underenheter", '') AS underenheter
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
              AND COALESCE("Antall Underenheter", 0) > 0
            ORDER BY antall_underenheter DESC, total_bruksareal DESC, address_label
            LIMIT ?
            """,
            params=[kommune_name, resolved_limit],
            limit=resolved_limit,
        )
        total_properties = max(_as_int(summary_row.get("total_properties")), 1)
        with_tenants_count = _as_int(summary_row.get("with_tenants_count"))
        return {
            "summary": {
                "total_properties": _as_int(summary_row.get("total_properties")),
                "with_tenants_count": with_tenants_count,
                "with_tenants_share_percent": round(100.0 * with_tenants_count / total_properties, 2),
                "with_tenants_area": _as_round(summary_row.get("with_tenants_area"), 1),
                "max_underenheter": _as_int(summary_row.get("max_underenheter")),
                "multi_owner_count": _as_int(summary_row.get("multi_owner_count")),
            },
            "top_rows": top_rows,
        }

    def _build_data_quality_score(kommune_name: str) -> dict[str, Any]:
        kommune_expr = _normalized_kommune_expr("kommune")
        param_expr = _normalized_kommune_expr("?")

        quality_row = _query_objects(
            sql=f"""
            SELECT
              COUNT(*) AS total_properties,
              SUM(CASE WHEN COALESCE("BruksarealTotalt", 0) > 0 THEN 1 ELSE 0 END) AS area_valid_count,
              SUM(CASE WHEN "Adresse" IS NOT NULL AND TRIM("Adresse") <> '' THEN 1 ELSE 0 END) AS address_present_count,
              SUM(CASE WHEN "Lat" IS NOT NULL AND "Lon" IS NOT NULL THEN 1 ELSE 0 END) AS geo_present_count,
              SUM(CASE WHEN "VannforsyningsKodeId" IS NOT NULL AND "AvlopsKodeId" IS NOT NULL THEN 1 ELSE 0 END) AS utilities_present_count,
              SUM(CASE WHEN "OppvarmingsKodeIds" IS NOT NULL OR "EnergikildeKodeIds" IS NOT NULL THEN 1 ELSE 0 END) AS heating_energy_present_count,
              SUM(CASE WHEN "Bygningsstatus" IS NOT NULL AND TRIM("Bygningsstatus") <> '' THEN 1 ELSE 0 END) AS status_present_count,
              SUM(CASE WHEN "TEK-standard" IS NOT NULL AND TRIM("TEK-standard") <> '' THEN 1 ELSE 0 END) AS tek_present_count
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
            """,
            params=[kommune_name],
            limit=1,
        )[0]

        total_properties = max(_as_int(quality_row.get("total_properties")), 1)
        fields: list[dict[str, Any]] = [
            {"field": "area_valid", "label": "Valid Area (>0)", "present_count": _as_int(quality_row.get("area_valid_count"))},
            {"field": "address_present", "label": "Address", "present_count": _as_int(quality_row.get("address_present_count"))},
            {"field": "geo_present", "label": "Lat/Lon", "present_count": _as_int(quality_row.get("geo_present_count"))},
            {"field": "utilities_present", "label": "Water + Sewage", "present_count": _as_int(quality_row.get("utilities_present_count"))},
            {
                "field": "heating_energy_present",
                "label": "Heating/Energy",
                "present_count": _as_int(quality_row.get("heating_energy_present_count")),
            },
            {"field": "status_present", "label": "Building Status", "present_count": _as_int(quality_row.get("status_present_count"))},
            {"field": "tek_present", "label": "TEK Standard", "present_count": _as_int(quality_row.get("tek_present_count"))},
        ]
        for entry in fields:
            entry["completeness_percent"] = round(100.0 * entry["present_count"] / total_properties, 2)
            entry["missing_count"] = total_properties - entry["present_count"]

        score_fields = [
            item
            for item in fields
            if item["field"] in {"area_valid", "address_present", "geo_present", "utilities_present", "heating_energy_present"}
        ]
        score_percent = round(
            sum(float(item["completeness_percent"]) for item in score_fields) / max(len(score_fields), 1),
            2,
        )
        return {
            "score_percent": score_percent,
            "total_properties": _as_int(quality_row.get("total_properties")),
            "fields": fields,
            "gaps": [item for item in fields if float(item["completeness_percent"]) < 90.0],
        }

    def _build_underwriting_analytics(kommune_name: str) -> dict[str, Any]:
        return {
            "exposure_dashboard": _build_exposure_dashboard(kommune_name=kommune_name, top_n=10),
            "occupancy_risk_mix": _build_occupancy_risk_mix(kommune_name=kommune_name, limit=30),
            "age_standard_proxy": _build_age_standard_proxy(kommune_name=kommune_name),
            "status_underwriting": _build_status_underwriting(kommune_name=kommune_name, limit=50),
            "large_risk_schedule": _build_large_risk_schedule(kommune_name=kommune_name, limit=20),
            "heritage_flags": _build_heritage_flags(kommune_name=kommune_name, limit=50),
            "tenant_activity_proxy": _build_tenant_activity_proxy(kommune_name=kommune_name, limit=20),
            "data_quality": _build_data_quality_score(kommune_name=kommune_name),
        }

    def duckdb_kommune_exposure_dashboard(kommune_name: str, top_n: int = 10) -> dict[str, Any]:
        """Return core exposure KPIs and concentration metrics."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        section = _build_exposure_dashboard(kommune_name=normalized, top_n=top_n)
        return {"kommune_name": normalized, "metric": "exposure_dashboard", "result": section}

    def duckdb_kommune_occupancy_risk_mix(kommune_name: str, limit: int = 30) -> dict[str, Any]:
        """Return occupancy category mix by both count share and area share."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        section = _build_occupancy_risk_mix(kommune_name=normalized, limit=limit)
        return {"kommune_name": normalized, "metric": "occupancy_risk_mix", "result": section}

    def duckdb_kommune_age_standard_proxy(kommune_name: str) -> dict[str, Any]:
        """Return TEK and grouped age-band distributions."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        section = _build_age_standard_proxy(kommune_name=normalized)
        return {"kommune_name": normalized, "metric": "age_standard_proxy", "result": section}

    def duckdb_kommune_status_underwriting(kommune_name: str, limit: int = 50) -> dict[str, Any]:
        """Return status mix and problematic-status property list."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        section = _build_status_underwriting(kommune_name=normalized, limit=limit)
        return {"kommune_name": normalized, "metric": "status_underwriting", "result": section}

    def duckdb_kommune_large_risk_schedule(kommune_name: str, limit: int = 20) -> dict[str, Any]:
        """Return top-N largest properties for underwriting queueing."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        section = _build_large_risk_schedule(kommune_name=normalized, limit=limit)
        return {"kommune_name": normalized, "metric": "large_risk_schedule", "result": section}

    def duckdb_kommune_heritage_flags(kommune_name: str, limit: int = 50) -> dict[str, Any]:
        """Return heritage/special-handling flag counts and affected properties."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        section = _build_heritage_flags(kommune_name=normalized, limit=limit)
        return {"kommune_name": normalized, "metric": "heritage_flags", "result": section}

    def duckdb_kommune_tenant_activity_proxy(kommune_name: str, limit: int = 20) -> dict[str, Any]:
        """Return tenant and underenheter activity proxy metrics."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        section = _build_tenant_activity_proxy(kommune_name=normalized, limit=limit)
        return {"kommune_name": normalized, "metric": "tenant_activity_proxy", "result": section}

    def duckdb_kommune_data_quality_score(kommune_name: str) -> dict[str, Any]:
        """Return data quality score and field-level completeness."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        section = _build_data_quality_score(kommune_name=normalized)
        return {"kommune_name": normalized, "metric": "data_quality", "result": section}

    def duckdb_kommune_underwriting_analytics(kommune_name: str) -> dict[str, Any]:
        """Return complete underwriting analytics package for one kommune."""
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        return {
            "kommune_name": normalized,
            "metric": "underwriting_analytics",
            "result": _build_underwriting_analytics(kommune_name=normalized),
        }

    @mcp.tool()
    def mcp_server_start(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8200) -> dict[str, Any]:
        """Update runtime metadata to started state (server is already running in-process)."""
        runtime_state.update({"running": True, "transport": transport, "host": host, "port": int(port)})
        return {"status": "ok", "runtime": dict(runtime_state), "note": "In-process MCP server is already active."}

    @mcp.tool()
    def mcp_server_stop() -> dict[str, Any]:
        """Update runtime metadata to stopped state (non-destructive/no process kill)."""
        runtime_state["running"] = False
        return {"status": "ok", "runtime": dict(runtime_state), "note": "State updated only; process not terminated."}

    @mcp.tool()
    def mcp_server_status() -> dict[str, Any]:
        """Return MCP runtime metadata."""
        return {
            "runtime": dict(runtime_state),
            "tool_count": len(_tool_catalog()),
            "resource_count": len(_resource_catalog()),
            "published_tool_count": len(published_tools),
            "published_resource_count": len(published_resources) + len(published_queries),
        }

    @mcp.tool()
    def mcp_server_health() -> dict[str, Any]:
        """Return MCP + DuckDB health status."""
        return {
            "runtime": dict(runtime_state),
            "duckdb": duckdb_service.health(),
            "status": "ok",
        }

    @mcp.tool()
    def mcp_server_test() -> dict[str, Any]:
        """Run a lightweight connectivity test against DuckDB."""
        result = duckdb_service.query(sql="SELECT 1 AS ok", params=None, limit=1)
        return {"status": "ok", "result": result}

    @mcp.tool()
    def mcp_get_diagnostics() -> dict[str, Any]:
        """Return server diagnostics and selected configuration values."""
        return {
            "runtime": dict(runtime_state),
            "duckdb": duckdb_service.health(),
            "catalog": {"tools": len(_tool_catalog()), "resources": len(_resource_catalog())},
            "settings": {
                "read_only": resolved.duckdb_read_only,
                "allow_write": resolved.duckdb_allow_write,
                "db_path": resolved.duckdb_path,
            },
        }

    @mcp.tool()
    def mcp_list_tools(server: str | None = None) -> list[dict[str, Any]]:
        """List tools available through this MCP runtime."""
        _ = server
        return _tool_catalog()

    @mcp.tool()
    def mcp_list_resources(server: str | None = None) -> list[dict[str, Any]]:
        """List resources available through this MCP runtime."""
        _ = server
        return _resource_catalog()

    @mcp.tool()
    def mcp_get_resource(server: str | None = None, uri: str = "") -> dict[str, Any]:
        """Read one MCP resource by URI."""
        _ = server
        if not uri:
            raise ValueError("uri is required.")
        return {"uri": uri, "contents": _resolve_resource(uri)}

    @mcp.tool()
    def mcp_publish_query(
        sql: str,
        uri: str,
        params: list[Any] | None = None,
        limit: int = DB_DEFAULT_RESULT_ROWS,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Publish a SQL query as a runtime resource."""
        if not sql.strip():
            raise ValueError("sql is required.")
        if not uri:
            raise ValueError("uri is required.")
        published_queries[uri] = {
            "sql": sql,
            "params": params or [],
            "limit": int(limit),
            "name": name or uri,
            "description": description or "Published SQL-backed resource.",
        }
        return {"status": "ok", "uri": uri}

    @mcp.tool()
    def mcp_publish_table(
        table: str,
        uri: str | None = None,
        limit: int = DB_DEFAULT_RESULT_ROWS,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Publish a DuckDB table as a resource."""
        schema, relation = _split_table_name(table)
        quoted = f'"{schema}"."{relation}"'
        target_uri = uri or f"duckdb://table/{schema}/{relation}"
        published_queries[target_uri] = {
            "sql": f"SELECT * FROM {quoted} LIMIT {int(limit)}",
            "params": [],
            "limit": int(limit),
            "name": name or target_uri,
            "description": description or f"Published table resource for {schema}.{relation}.",
        }
        return {"status": "ok", "uri": target_uri}

    @mcp.tool()
    def mcp_publish_tool(name: str, description: str, target_tool: str | None = None) -> dict[str, Any]:
        """Publish/register a custom tool descriptor."""
        if not name.strip():
            raise ValueError("name is required.")
        published_tools[name] = {"description": description, "target_tool": target_tool}
        return {"status": "ok", "name": name}

    @mcp.tool()
    def mcp_register_prompt_template(name: str, template: str, description: str = "") -> dict[str, Any]:
        """Register a prompt template for runtime use."""
        if not name.strip():
            raise ValueError("name is required.")
        if not template.strip():
            raise ValueError("template is required.")
        prompt_templates[name] = {"template": template, "description": description}
        return {"status": "ok", "name": name}

    @mcp.tool()
    def mcp_list_prompt_templates() -> list[dict[str, str]]:
        """List registered prompt templates."""
        return [
            {"name": name, "description": value.get("description", ""), "template": value.get("template", "")}
            for name, value in sorted(prompt_templates.items())
        ]

    @mcp.tool()
    def mcp_render_prompt_template(name: str, args: dict[str, Any] | None = None) -> dict[str, str]:
        """Render one prompt template with args."""
        if name not in prompt_templates:
            raise FileNotFoundError(f"Unknown prompt template: {name}")
        template = prompt_templates[name]["template"]
        rendered = template.format(**(args or {}))
        return {"name": name, "rendered": rendered}

    @mcp.tool()
    def mcp_list_prompts() -> list[dict[str, str]]:
        """List available prompt names."""
        prompts = [{"name": "db_schema_overview", "description": "Prompt for schema reconnaissance and safe querying."}]
        prompts.extend(
            {"name": name, "description": value.get("description", "")}
            for name, value in sorted(prompt_templates.items())
        )
        return prompts

    @mcp.tool()
    def mcp_get_prompt(name: str, args: dict[str, Any] | None = None) -> dict[str, str]:
        """Get one prompt by name."""
        if name == "db_schema_overview":
            return {
                "name": name,
                "prompt": (
                    "Use mcp_call_tool with duckdb_list_tables, duckdb_describe_table, and duckdb_query. "
                    "For municipality occupancy summaries, prefer duckdb_kommune_occupancy_distribution "
                    "and duckdb_kommune_largest_occupancy_area. For underwriting insights, prefer "
                    "duckdb_kommune_underwriting_analytics or its sectional tools "
                    "(duckdb_kommune_exposure_dashboard, duckdb_kommune_occupancy_risk_mix, "
                    "duckdb_kommune_age_standard_proxy, duckdb_kommune_status_underwriting, "
                    "duckdb_kommune_large_risk_schedule, duckdb_kommune_heritage_flags, "
                    "duckdb_kommune_tenant_activity_proxy, duckdb_kommune_data_quality_score). "
                    "List available tables, inspect schema for relevant tables, then run bounded SQL queries. "
                    "Only make claims grounded in query output."
                ),
            }
        return mcp_render_prompt_template(name=name, args=args)

    @mcp.tool()
    def mcp_reconnect_server(server: str | None = None) -> dict[str, Any]:
        """Reconnect/refresh server state (no-op for local in-process runtime)."""
        _ = server
        runtime_state["running"] = True
        return {"status": "ok", "runtime": dict(runtime_state)}

    @mcp.tool()
    def mcp_call_tool(server: str | None = None, tool: str = "", args: Any = None) -> dict[str, Any]:
        """Call one tool by name."""
        _ = server
        name = tool.strip()
        if not name:
            raise ValueError("tool is required.")
        if name == "mcp_call_tool":
            raise ValueError("Recursive mcp_call_tool invocation is not allowed.")

        published = published_tools.get(name)
        if published and published.get("target_tool"):
            name = str(published["target_tool"])

        if name not in tool_dispatch:
            raise FileNotFoundError(f"Unknown tool: {name}")

        payload = _normalize_args(args)
        try:
            result = tool_dispatch[name](**payload)
        except TypeError as exc:
            raise ValueError(f"Invalid args for tool `{name}`: {exc}") from exc
        return {"tool": name, "result": result}

    @mcp.tool()
    def mcp_server_send_request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Route a low-level request to server helper methods."""
        payload = params or {}
        routes: dict[str, Callable[..., Any]] = {
            "mcp_list_tools": mcp_list_tools,
            "mcp_list_resources": mcp_list_resources,
            "mcp_get_resource": mcp_get_resource,
            "mcp_call_tool": mcp_call_tool,
            "mcp_server_status": mcp_server_status,
            "mcp_server_health": mcp_server_health,
            "mcp_server_test": mcp_server_test,
            "mcp_get_diagnostics": mcp_get_diagnostics,
        }
        if method not in routes:
            raise ValueError(f"Unsupported method: {method}")
        return {"method": method, "result": routes[method](**payload)}

    tool_dispatch.update(
        {
            "duckdb_health": duckdb_health,
            "duckdb_list_tables": duckdb_list_tables,
            "duckdb_describe_table": duckdb_describe_table,
            "duckdb_query": duckdb_query,
            "duckdb_kommune_occupancy_distribution": duckdb_kommune_occupancy_distribution,
            "duckdb_kommune_largest_occupancy_area": duckdb_kommune_largest_occupancy_area,
            "duckdb_kommune_exposure_dashboard": duckdb_kommune_exposure_dashboard,
            "duckdb_kommune_occupancy_risk_mix": duckdb_kommune_occupancy_risk_mix,
            "duckdb_kommune_age_standard_proxy": duckdb_kommune_age_standard_proxy,
            "duckdb_kommune_status_underwriting": duckdb_kommune_status_underwriting,
            "duckdb_kommune_large_risk_schedule": duckdb_kommune_large_risk_schedule,
            "duckdb_kommune_heritage_flags": duckdb_kommune_heritage_flags,
            "duckdb_kommune_tenant_activity_proxy": duckdb_kommune_tenant_activity_proxy,
            "duckdb_kommune_data_quality_score": duckdb_kommune_data_quality_score,
            "duckdb_kommune_underwriting_analytics": duckdb_kommune_underwriting_analytics,
            "mcp_call_tool": mcp_call_tool,
            "mcp_get_diagnostics": mcp_get_diagnostics,
            "mcp_get_prompt": mcp_get_prompt,
            "mcp_get_resource": mcp_get_resource,
            "mcp_list_prompt_templates": mcp_list_prompt_templates,
            "mcp_list_prompts": mcp_list_prompts,
            "mcp_list_resources": mcp_list_resources,
            "mcp_list_tools": mcp_list_tools,
            "mcp_publish_query": mcp_publish_query,
            "mcp_publish_table": mcp_publish_table,
            "mcp_publish_tool": mcp_publish_tool,
            "mcp_reconnect_server": mcp_reconnect_server,
            "mcp_register_prompt_template": mcp_register_prompt_template,
            "mcp_render_prompt_template": mcp_render_prompt_template,
            "mcp_server_health": mcp_server_health,
            "mcp_server_send_request": mcp_server_send_request,
            "mcp_server_start": mcp_server_start,
            "mcp_server_status": mcp_server_status,
            "mcp_server_stop": mcp_server_stop,
            "mcp_server_test": mcp_server_test,
        }
    )

    @mcp.resource("duckdb://health")
    def duckdb_health_resource() -> str:
        """Expose DuckDB health as an MCP resource."""
        return _safe_json(_resolve_resource("duckdb://health"))

    @mcp.resource("duckdb://tables")
    def duckdb_tables_resource() -> str:
        """Expose available tables as an MCP resource."""
        return _safe_json(_resolve_resource("duckdb://tables"))

    @mcp.resource("duckdb://tools")
    def duckdb_tools_resource() -> str:
        """Expose MCP tool catalog as an MCP resource."""
        return _safe_json(_resolve_resource("duckdb://tools"))

    @mcp.resource("duckdb://tool-targets")
    def duckdb_tool_targets_resource() -> str:
        """Expose callable targets for `mcp_call_tool`."""
        return _safe_json(_resolve_resource("duckdb://tool-targets"))

    return mcp


def run_mcp_server(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8200) -> None:
    """Run MCP server in stdio or streamable-http transport mode."""
    server = create_duckdb_mcp_server()
    if transport == "stdio":
        server.run(transport="stdio")
        return
    if transport == "http":
        server.run(transport="streamable-http", host=host, port=port)
        return
    raise ValueError(f"Unsupported transport: {transport}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DuckDB MCP server for agents backend.")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8200)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_mcp_server(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
