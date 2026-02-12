"""Agents service facade used by the API layer."""
from __future__ import annotations

import importlib.util
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

from app.agents.orchestrator import build_agent_orchestrator
from app.core.db_limits import DB_DEFAULT_RESULT_ROWS
from app.core.settings import AppSettings
from app.db.duckdb_service import DuckDBService
from app.mcp_server import DuckDBMCPClient
from app.utils.dataframe import extract_kartverket_kommune_name

logger = logging.getLogger(__name__)


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def _extract_text_from_event(event: Any) -> str:
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or []
    chunks: list[str] = []
    for part in parts:
        text = getattr(part, "text", None)
        if isinstance(text, str) and text.strip():
            chunks.append(text.strip())
    return "\n".join(chunks).strip()


def _extract_tool_runs_from_event(event: Any) -> list[dict[str, Any]]:
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or []
    runs: list[dict[str, Any]] = []

    for part in parts:
        call = getattr(part, "function_call", None)
        if call is not None:
            runs.append(
                {
                    "name": str(getattr(call, "name", "")),
                    "args": getattr(call, "args", {}) or {},
                    "type": "call",
                }
            )

        response = getattr(part, "function_response", None)
        if response is not None:
            runs.append(
                {
                    "name": str(getattr(response, "name", "")),
                    "response": getattr(response, "response", None),
                    "type": "response",
                }
            )
    return runs


class AgentsService:
    """Service facade for agents endpoints."""

    def __init__(self, duckdb: DuckDBService | None = None):
        """Initialize service dependencies."""
        self.settings = AppSettings.from_env()
        self.project_root = Path(__file__).resolve().parents[2]
        self.duckdb = duckdb or DuckDBService(
            db_path=self.settings.duckdb_path,
            read_only=self.settings.duckdb_read_only,
            allow_write=self.settings.duckdb_allow_write,
        )
        self.mcp_client = DuckDBMCPClient()

    async def startup(self) -> None:
        """Initialize long-lived service resources."""
        try:
            await self.mcp_client.start()
        except Exception as exc:  # pragma: no cover - runtime/env dependent
            logger.warning("Failed to start persistent MCP session: %s", exc)

    async def shutdown(self) -> None:
        """Release long-lived service resources."""
        try:
            await self.mcp_client.stop()
        except Exception as exc:  # pragma: no cover - runtime/env dependent
            logger.warning("Failed to stop persistent MCP session: %s", exc)

    def health_report(self) -> dict[str, Any]:
        """Return current service capability status."""
        adk_available = _module_available("google.adk")
        mcp_sdk_available = _module_available("mcp")
        fastmcp_available = _module_available("fastmcp")
        mcp_runtime_available = fastmcp_available and mcp_sdk_available

        duckdb_ok = False
        duckdb_error: str | None = None
        try:
            _ = self.duckdb.health()
            duckdb_ok = True
        except Exception as exc:  # pragma: no cover - env/runtime dependent
            duckdb_error = str(exc)

        return {
            "status": "ok" if duckdb_ok else "degraded",
            "features": {
                "chat_workflow": adk_available and mcp_runtime_available,
                "tool_execution": mcp_runtime_available,
                "mcp_resources": mcp_runtime_available,
                "duckdb": duckdb_ok,
                "google_adk": adk_available,
                "fastmcp": fastmcp_available,
                "mcp_sdk": mcp_sdk_available,
            },
            "message": "Agents backend is configured for an MCP-based DuckDB tool flow.",
            "duckdb_error": duckdb_error,
            "llm": {
                "provider": self.settings.llm_provider,
                "model": self.settings.llm_model,
                "vertex_project_id": bool(self.settings.vertex_project_id),
                "vertex_location": self.settings.vertex_location,
            },
        }

    async def list_tools(self) -> list[dict[str, Any]]:
        """Return available MCP tools."""
        return await self.list_mcp_tools()

    async def invoke_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Invoke one MCP tool."""
        return await self.mcp_client.call_tool(name=name, args=args)

    async def list_mcp_resources(self) -> list[dict[str, Any]]:
        """List MCP resources."""
        return await self.mcp_client.list_resources()

    async def read_mcp_resource(self, uri: str) -> dict[str, Any]:
        """Read one MCP resource by URI."""
        return await self.mcp_client.read_resource(uri)

    async def list_mcp_tools(self) -> list[dict[str, Any]]:
        """List MCP tools."""
        return await self.mcp_client.list_tools()

    def list_available_kommuner(self) -> list[dict[str, str]]:
        """List available kommune names from local Kartverket Excel files."""
        source_dir = self.project_root.parent / "data" / "excel" / "raw" / "kartverket"
        if not source_dir.exists():
            return []

        file_paths: list[Path] = []
        for pattern in ("*_Properties.xlsx", "*_Properties_Imputed.xlsx"):
            file_paths.extend(source_dir.glob(pattern))

        kommune_labels: dict[str, str] = {}
        for file_path in sorted(set(file_paths)):
            if file_path.name.startswith("~$"):
                continue

            extracted = extract_kartverket_kommune_name(file_path)
            base_name = extracted.split("___", 1)[0]
            label = " ".join(base_name.replace("_", " ").split()).strip()
            if not label:
                continue

            key = label.lower()
            if key not in kommune_labels:
                kommune_labels[key] = label

        return [{"key": key, "label": kommune_labels[key]} for key in sorted(kommune_labels, key=kommune_labels.get)]

    def _resolve_kommune_label(self, kommune_name_or_key: str) -> str:
        """Resolve kommune key/label input to the canonical label used in file discovery."""
        value = str(kommune_name_or_key or "").strip()
        if not value:
            raise ValueError("kommune is required.")

        options = self.list_available_kommuner()
        lookup: dict[str, str] = {}
        for option in options:
            key = str(option.get("key", "")).strip().lower()
            label = str(option.get("label", "")).strip()
            if key and label:
                lookup[key] = label
                lookup[label.lower()] = label

        return lookup.get(value.lower(), value)

    @staticmethod
    def _normalized_kommune_expr(column_ref: str) -> str:
        return f"lower(trim(replace(replace({column_ref}, ' Kommune', ''), ' kommune', '')))"

    @staticmethod
    def _rows_to_objects(result: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert DuckDB result payload rows to list-of-dicts."""
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        if not isinstance(columns, list) or not isinstance(rows, list):
            return []

        out: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, list):
                continue
            out.append({str(columns[idx]): row[idx] for idx in range(min(len(columns), len(row)))})
        return out

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _normalize_distribution_rows(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Ensure occupancy distribution uses area-based share and stable area ordering."""
        if not rows:
            return []

        normalized: list[dict[str, Any]] = [dict(row) for row in rows if isinstance(row, dict)]
        total_area = sum(cls._to_float(row.get("total_bruksareal")) for row in normalized)

        for row in normalized:
            area = cls._to_float(row.get("total_bruksareal"))
            share = 0.0 if total_area <= 0 else round((100.0 * area) / total_area, 2)
            row["share_percent"] = share

        normalized.sort(key=lambda row: (-cls._to_float(row.get("total_bruksareal")), str(row.get("occupancy_category", ""))))
        return normalized

    @staticmethod
    def _mcp_result_dict(value: Any) -> dict[str, Any]:
        """Unwrap MCP payloads into a plain DuckDB result dict (columns/rows)."""

        def _json_load_maybe(node: Any) -> Any:
            if not isinstance(node, str):
                return node
            payload = node.strip()
            if not payload:
                return node
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                return node

        def _walk(node: Any, depth: int = 0) -> dict[str, Any]:
            if depth > 12:
                return {}

            if hasattr(node, "model_dump"):
                node = node.model_dump()
            elif hasattr(node, "dict"):
                node = node.dict()

            node = _json_load_maybe(node)

            if isinstance(node, dict):
                columns = node.get("columns")
                rows = node.get("rows")
                if isinstance(columns, list) and isinstance(rows, list):
                    return node

                # Prioritize common MCP wrapper keys, then fall back to full traversal.
                for key in ("result", "data", "content", "contents", "response", "payload", "value", "text"):
                    if key in node:
                        found = _walk(node[key], depth + 1)
                        if found:
                            return found

                for value in node.values():
                    found = _walk(value, depth + 1)
                    if found:
                        return found
                return {}

            if isinstance(node, (list, tuple, set)):
                for item in node:
                    found = _walk(item, depth + 1)
                    if found:
                        return found
                return {}

            # Handle tool/client objects that expose content-ish attributes.
            for attr in ("text", "data", "content", "contents", "response"):
                if hasattr(node, attr):
                    found = _walk(getattr(node, attr), depth + 1)
                    if found:
                        return found
            return {}

        return _walk(value)

    async def _call_mcp_duckdb_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call one DuckDB tool via MCP and normalize the returned result."""
        response = await self.mcp_client.call_tool(
            name="mcp_call_tool",
            args={"tool": tool_name, "args": args},
        )
        result = self._mcp_result_dict(response)
        if not result:
            raise ValueError(f"Unexpected MCP response format for tool `{tool_name}`.")
        return result

    def _duckdb_kommune_occupancy_distribution(self, kommune_name: str, limit: int = 30) -> dict[str, Any]:
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")
        if limit < 1 or limit > 500:
            raise ValueError("limit must be in range [1, 500].")

        kommune_expr = self._normalized_kommune_expr("kommune")
        param_expr = self._normalized_kommune_expr("?")
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
        return self.duckdb.query(sql=sql, params=[normalized, int(limit)], limit=limit)

    def _duckdb_kommune_largest_occupancy_area(self, kommune_name: str) -> dict[str, Any]:
        normalized = str(kommune_name or "").strip()
        if not normalized:
            raise ValueError("kommune_name is required.")

        kommune_expr = self._normalized_kommune_expr("kommune")
        param_expr = self._normalized_kommune_expr("?")
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
        return self.duckdb.query(sql=sql, params=[normalized], limit=1)

    def _query_objects(
        self,
        sql: str,
        params: list[Any] | None = None,
        limit: int = DB_DEFAULT_RESULT_ROWS,
    ) -> list[dict[str, Any]]:
        return self._rows_to_objects(self.duckdb.query(sql=sql, params=params, limit=limit))

    @staticmethod
    def _normalize_kommune_value(value: str) -> str:
        base = " ".join(str(value or "").split()).strip().lower()
        if base.endswith(" kommune"):
            base = base[: -len(" kommune")]
        return base

    @classmethod
    def _as_int(cls, value: Any) -> int:
        return int(round(cls._to_float(value)))

    @classmethod
    def _as_round(cls, value: Any, digits: int = 2) -> float:
        return round(cls._to_float(value), digits)

    def _build_underwriting_insights(self, kommune_label: str) -> dict[str, Any]:
        kommune_expr = self._normalized_kommune_expr("kommune")
        param_expr = self._normalized_kommune_expr("?")
        params = [kommune_label]

        portfolio_total_row = self._query_objects(
            sql="""
            SELECT
              COUNT(*) AS total_properties,
              SUM(COALESCE("BruksarealTotalt", 0)) AS total_bruksareal
            FROM main.properties
            """,
            params=None,
            limit=1,
        )[0]
        selected_total_row = self._query_objects(
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
        by_kommune_rows = self._query_objects(
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
        normalized_selected = self._normalize_kommune_value(kommune_label)
        for row in by_kommune_rows:
            row["is_selected"] = self._normalize_kommune_value(str(row.get("kommune", ""))) == normalized_selected

        concentration_row = self._query_objects(
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
        top_properties_rows = self._query_objects(
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
            WHERE rn <= 10
            ORDER BY rn
            """,
            params=params,
            limit=10,
        )

        occupancy_mix_rows = self._query_objects(
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
            """,
            params=params,
            limit=200,
        )
        occupancy_top_by_count = sorted(
            [dict(row) for row in occupancy_mix_rows],
            key=lambda row: (-self._to_float(row.get("building_count")), -self._to_float(row.get("total_bruksareal"))),
        )[:10]

        tek_distribution_rows = self._query_objects(
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
            params=params,
            limit=200,
        )
        age_band_rows = self._query_objects(
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
            params=params,
            limit=50,
        )

        status_distribution_rows = self._query_objects(
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
            params=params,
            limit=100,
        )

        problematic_rows = self._query_objects(
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
            LIMIT 50
            """,
            params=params,
            limit=50,
        )
        problematic_statuses = sorted(
            {
                str(row.get("bygningsstatus", "")).strip()
                for row in status_distribution_rows
                if any(
                    token in str(row.get("bygningsstatus", "")).lower()
                    for token in ("riving", "brenning", "kondemn", "ikke godkjent")
                )
            }
        )

        large_risk_rows = self._query_objects(
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
            LIMIT 20
            """,
            params=params,
            limit=20,
        )
        for idx, row in enumerate(large_risk_rows, start=1):
            row["rank"] = idx

        heritage_rows = self._query_objects(
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
            LIMIT 50
            """,
            params=params,
            limit=50,
        )
        heritage_summary_row = self._query_objects(
            sql=f"""
            SELECT
              SUM(CASE WHEN COALESCE("HarSefrakminne", 0) = 1 THEN 1 ELSE 0 END) AS sefrak_count,
              SUM(CASE WHEN COALESCE("HarKulturminne", 0) = 1 THEN 1 ELSE 0 END) AS kulturminne_count,
              SUM(CASE WHEN COALESCE("Skjermingsverdig", 0) = 1 THEN 1 ELSE 0 END) AS skjermingsverdig_count
            FROM main.properties
            WHERE {kommune_expr} = {param_expr}
            """,
            params=params,
            limit=1,
        )[0]

        tenant_summary_row = self._query_objects(
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
            params=params,
            limit=1,
        )[0]
        tenant_top_rows = self._query_objects(
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
            LIMIT 20
            """,
            params=params,
            limit=20,
        )

        quality_row = self._query_objects(
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
            params=params,
            limit=1,
        )[0]

        total_properties = max(self._as_int(quality_row.get("total_properties")), 1)
        quality_fields = [
            {
                "field": "area_valid",
                "label": "Valid Area (>0)",
                "present_count": self._as_int(quality_row.get("area_valid_count")),
            },
            {
                "field": "address_present",
                "label": "Address",
                "present_count": self._as_int(quality_row.get("address_present_count")),
            },
            {
                "field": "geo_present",
                "label": "Lat/Lon",
                "present_count": self._as_int(quality_row.get("geo_present_count")),
            },
            {
                "field": "utilities_present",
                "label": "Water + Sewage",
                "present_count": self._as_int(quality_row.get("utilities_present_count")),
            },
            {
                "field": "heating_energy_present",
                "label": "Heating/Energy",
                "present_count": self._as_int(quality_row.get("heating_energy_present_count")),
            },
            {
                "field": "status_present",
                "label": "Building Status",
                "present_count": self._as_int(quality_row.get("status_present_count")),
            },
            {
                "field": "tek_present",
                "label": "TEK Standard",
                "present_count": self._as_int(quality_row.get("tek_present_count")),
            },
        ]
        for entry in quality_fields:
            entry["completeness_percent"] = round(100.0 * entry["present_count"] / total_properties, 2)
            entry["missing_count"] = total_properties - entry["present_count"]

        score_fields = [item for item in quality_fields if item["field"] in {
            "area_valid",
            "address_present",
            "geo_present",
            "utilities_present",
            "heating_energy_present",
        }]
        data_quality_score = round(
            sum(float(item["completeness_percent"]) for item in score_fields) / max(len(score_fields), 1),
            2,
        )

        selected_total_area = self._to_float(selected_total_row.get("total_bruksareal"))
        portfolio_total_area = self._to_float(portfolio_total_row.get("total_bruksareal"))
        selected_total_properties = self._as_int(selected_total_row.get("total_properties"))
        portfolio_total_properties = self._as_int(portfolio_total_row.get("total_properties"))
        tenant_total_properties = max(self._as_int(tenant_summary_row.get("total_properties")), 1)
        with_tenants_count = self._as_int(tenant_summary_row.get("with_tenants_count"))

        return {
            "exposure_dashboard": {
                "portfolio_total_properties": portfolio_total_properties,
                "portfolio_total_bruksareal": self._as_round(portfolio_total_area, 1),
                "selected_kommune_properties": selected_total_properties,
                "selected_kommune_bruksareal": self._as_round(selected_total_area, 1),
                "selected_property_share_percent": round(
                    100.0 * selected_total_properties / max(portfolio_total_properties, 1), 2
                ),
                "selected_area_share_percent": round(
                    100.0 * selected_total_area / max(portfolio_total_area, 1.0), 2
                ),
                "by_kommune": by_kommune_rows,
                "concentration": {
                    "top5_area": self._as_round(concentration_row.get("top5_area"), 1),
                    "top5_share_percent": self._as_round(concentration_row.get("top5_share_percent"), 2),
                    "top10_area": self._as_round(concentration_row.get("top10_area"), 1),
                    "top10_share_percent": self._as_round(concentration_row.get("top10_share_percent"), 2),
                },
                "top_properties_by_area": top_properties_rows,
            },
            "occupancy_risk_mix": {
                "by_category": occupancy_mix_rows,
                "top_categories_by_area": occupancy_mix_rows[:10],
                "top_categories_by_count": occupancy_top_by_count,
            },
            "age_standard_proxy": {
                "tek_distribution": tek_distribution_rows,
                "age_band_distribution": age_band_rows,
            },
            "status_underwriting": {
                "distribution": status_distribution_rows,
                "problematic_statuses": problematic_statuses,
                "problematic_properties": problematic_rows,
            },
            "large_risk_schedule": {
                "rows": large_risk_rows,
            },
            "heritage_flags": {
                "summary": {
                    "sefrak_count": self._as_int(heritage_summary_row.get("sefrak_count")),
                    "kulturminne_count": self._as_int(heritage_summary_row.get("kulturminne_count")),
                    "skjermingsverdig_count": self._as_int(heritage_summary_row.get("skjermingsverdig_count")),
                    "any_flag_count": len(heritage_rows),
                },
                "rows": heritage_rows,
            },
            "tenant_activity_proxy": {
                "summary": {
                    "total_properties": self._as_int(tenant_summary_row.get("total_properties")),
                    "with_tenants_count": with_tenants_count,
                    "with_tenants_share_percent": round(100.0 * with_tenants_count / tenant_total_properties, 2),
                    "with_tenants_area": self._as_round(tenant_summary_row.get("with_tenants_area"), 1),
                    "max_underenheter": self._as_int(tenant_summary_row.get("max_underenheter")),
                    "multi_owner_count": self._as_int(tenant_summary_row.get("multi_owner_count")),
                },
                "top_rows": tenant_top_rows,
            },
            "data_quality": {
                "score_percent": data_quality_score,
                "total_properties": self._as_int(quality_row.get("total_properties")),
                "fields": quality_fields,
                "gaps": [item for item in quality_fields if float(item["completeness_percent"]) < 90.0],
            },
        }

    async def get_kommune_insights(self, kommune_name_or_key: str) -> dict[str, Any]:
        """Fetch municipality-level insights for dashboard and underwriting views."""
        kommune_label = self._resolve_kommune_label(kommune_name_or_key)
        distribution_result = self._duckdb_kommune_occupancy_distribution(kommune_name=kommune_label, limit=30)
        largest_result = self._duckdb_kommune_largest_occupancy_area(kommune_name=kommune_label)

        distribution_rows = self._normalize_distribution_rows(self._rows_to_objects(distribution_result))
        largest_rows = self._rows_to_objects(largest_result)
        underwriting = self._build_underwriting_insights(kommune_label=kommune_label)

        return {
            "kommune": kommune_label,
            "occupancy_distribution": {
                "source_column": "Forenklet Bygningskategori",
                "rows": distribution_rows,
            },
            "largest_occupancy": {
                "source_column": "Forenklet Bygningskategori",
                "metric_column": "BruksarealTotalt",
                "row": largest_rows[0] if largest_rows else None,
            },
            "underwriting": underwriting,
            "tool_runs": [
                {"tool": "duckdb_kommune_occupancy_distribution", "status": "ok", "source": "duckdb"},
                {"tool": "duckdb_kommune_largest_occupancy_area", "status": "ok", "source": "duckdb"},
                {"tool": "duckdb_kommune_underwriting_analytics", "status": "ok", "source": "duckdb"},
            ],
        }

    def _mcp_server_env(self) -> dict[str, str]:
        pythonpath_parts = [item for item in os.getenv("PYTHONPATH", "").split(os.pathsep) if item]
        project_root_str = str(self.project_root)
        if project_root_str not in pythonpath_parts:
            pythonpath_parts.insert(0, project_root_str)

        return {
            "PATH": os.getenv("PATH", ""),
            "PYTHONPATH": os.pathsep.join(pythonpath_parts),
            "DUCKDB_PATH": self.settings.duckdb_path,
            "DUCKDB_READ_ONLY": "true" if self.settings.duckdb_read_only else "false",
            "DUCKDB_ALLOW_WRITE": "true" if self.settings.duckdb_allow_write else "false",
        }

    def _configure_llm_env(self) -> str:
        """Configure Vertex + Anthropic model registration for ADK."""
        if self.settings.llm_provider != "vertex_anthropic":
            return self.settings.llm_model

        if not self.settings.vertex_project_id:
            raise ValueError(
                "VERTEX_PROJECT_ID (or GOOGLE_CLOUD_PROJECT) is required for Vertex Anthropic models."
            )

        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", self.settings.vertex_project_id)
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", self.settings.vertex_location)

        try:
            from google.adk.models.anthropic_llm import Claude
            from google.adk.models.registry import LLMRegistry
        except ModuleNotFoundError as exc:
            raise NotImplementedError(
                "Vertex Anthropic provider requires `anthropic[vertex]` and `google-adk`."
            ) from exc

        try:
            LLMRegistry.register(Claude)
        except Exception:
            # Ignore duplicate registration or registry lifecycle errors.
            pass

        return self.settings.llm_model

    async def _run_chat_with_adk_mcp(self, message: str, workflow: str) -> tuple[str, list[dict[str, Any]]]:
        try:
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
            from google.genai import types as genai_types
            from mcp import StdioServerParameters
        except ModuleNotFoundError as exc:
            raise NotImplementedError(
                "Missing dependencies for ADK + MCP chat flow. Install `google-adk`, `mcp`, `fastmcp`, and `anthropic[vertex]`."
            ) from exc

        connection_params = StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", "app.mcp_server.server", "--transport", "stdio"],
                env=self._mcp_server_env(),
            ),
            timeout=30,
        )

        model_name = self._configure_llm_env()
        root_agent = build_agent_orchestrator(
            model=model_name,
            connection_params=connection_params,
            workflow=workflow,
        )
        session_service = InMemorySessionService()

        app_name = "agents_backend"
        user_id = "api_user"
        session_id = str(uuid4())
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )

        runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)
        content = genai_types.Content(role="user", parts=[genai_types.Part(text=message)])

        final_text = ""
        tool_runs: list[dict[str, Any]] = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            tool_runs.extend(_extract_tool_runs_from_event(event))
            text = _extract_text_from_event(event)
            if text:
                final_text = text

        return final_text.strip(), tool_runs

    async def run_chat(self, request: dict[str, Any]) -> dict[str, Any]:
        """Run ADK chat workflow backed by MCP DuckDB tools."""
        workflow = str(request.get("workflow") or "kommune_match_overview")
        message = str(request.get("message") or "").strip()
        if not message:
            raise ValueError("message is required.")

        if not bool(request.get("use_llm", True)):
            return {
                "status": "disabled",
                "workflow": workflow,
                "message": message,
                "summary": "LLM execution is disabled by request.",
                "insights": [],
                "tool_runs": [],
            }

        summary, tool_runs = await self._run_chat_with_adk_mcp(message=message, workflow=workflow)
        if not summary:
            summary = "No textual response generated by the LLM."

        return {
            "status": "success",
            "workflow": workflow,
            "message": message,
            "summary": summary,
            "insights": [],
            "tool_runs": tool_runs,
        }

    def duckdb_health(self) -> dict[str, Any]:
        """Return DuckDB connectivity status and metadata."""
        return self.duckdb.health()

    def duckdb_tables(self) -> list[dict[str, str]]:
        """List tables available in DuckDB."""
        return self.duckdb.list_tables()

    def duckdb_query(self, sql: str, params: list[Any] | None = None, limit: int = DB_DEFAULT_RESULT_ROWS) -> dict[str, Any]:
        """Execute SQL against DuckDB with configured safety rules."""
        return self.duckdb.query(sql=sql, params=params, limit=limit)
