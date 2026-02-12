"""Static MCP catalog metadata shared by API and server runtime."""
from __future__ import annotations

# DuckDB MCP extension-style functions (from duckdb.org extension page).
DUCKDB_MCP_EXTENSION_FUNCTIONS: tuple[dict[str, str], ...] = (
    {
        "name": "mcp_call_tool",
        "description": (
            "Execute a tool call against a named MCP server. "
            "DuckDB call targets: duckdb_health, duckdb_list_tables, duckdb_describe_table, duckdb_query, "
            "duckdb_kommune_occupancy_distribution, duckdb_kommune_largest_occupancy_area, "
            "duckdb_kommune_underwriting_analytics and sectional underwriting tools."
        ),
    },
    {"name": "mcp_get_diagnostics", "description": "Return MCP runtime diagnostics and health metadata."},
    {"name": "mcp_get_prompt", "description": "Get a named prompt payload from the MCP prompt catalog."},
    {"name": "mcp_get_resource", "description": "Fetch one MCP resource by URI."},
    {"name": "mcp_list_prompt_templates", "description": "List registered prompt templates."},
    {"name": "mcp_list_prompts", "description": "List available prompt definitions."},
    {"name": "mcp_list_resources", "description": "List available MCP resources."},
    {"name": "mcp_list_tools", "description": "List available MCP tools."},
    {"name": "mcp_publish_query", "description": "Publish a SQL query result as an MCP resource."},
    {"name": "mcp_publish_table", "description": "Publish a DuckDB table as an MCP resource."},
    {"name": "mcp_publish_tool", "description": "Publish/register a custom MCP tool descriptor."},
    {"name": "mcp_reconnect_server", "description": "Reconnect or refresh MCP server state."},
    {"name": "mcp_register_prompt_template", "description": "Register a prompt template in MCP runtime state."},
    {"name": "mcp_render_prompt_template", "description": "Render a registered prompt template with arguments."},
    {"name": "mcp_server_health", "description": "Return MCP server + DuckDB health status."},
    {"name": "mcp_server_send_request", "description": "Send a low-level RPC-style MCP request."},
    {"name": "mcp_server_start", "description": "Start MCP server runtime metadata state."},
    {"name": "mcp_server_status", "description": "Get current MCP server runtime metadata."},
    {"name": "mcp_server_stop", "description": "Stop MCP server runtime metadata state."},
    {"name": "mcp_server_test", "description": "Run a lightweight MCP server connectivity test."},
)

DUCKDB_CALL_TARGETS: tuple[dict[str, str], ...] = (
    {"name": "duckdb_health", "description": "Callable target for `mcp_call_tool`."},
    {"name": "duckdb_list_tables", "description": "Callable target for `mcp_call_tool`."},
    {"name": "duckdb_describe_table", "description": "Callable target for `mcp_call_tool`."},
    {"name": "duckdb_query", "description": "Callable target for `mcp_call_tool`."},
    {
        "name": "duckdb_kommune_occupancy_distribution",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns occupancy/building category distribution by `Forenklet Bygningskategori` for one kommune."
        ),
    },
    {
        "name": "duckdb_kommune_largest_occupancy_area",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns the category with largest summed `BruksarealTotalt` for one kommune."
        ),
    },
    {
        "name": "duckdb_kommune_exposure_dashboard",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns core exposure metrics, kommune split, and concentration by area."
        ),
    },
    {
        "name": "duckdb_kommune_occupancy_risk_mix",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns occupancy mix by both count share and area share."
        ),
    },
    {
        "name": "duckdb_kommune_age_standard_proxy",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns TEK-standard distribution and grouped age-band mix."
        ),
    },
    {
        "name": "duckdb_kommune_status_underwriting",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns building status distribution plus problematic properties."
        ),
    },
    {
        "name": "duckdb_kommune_large_risk_schedule",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns top-N largest properties with underwriting fields."
        ),
    },
    {
        "name": "duckdb_kommune_heritage_flags",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns heritage/special-handling flags and affected properties."
        ),
    },
    {
        "name": "duckdb_kommune_tenant_activity_proxy",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns tenant and underenheter activity proxies."
        ),
    },
    {
        "name": "duckdb_kommune_data_quality_score",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns field completeness and a composite data-quality score."
        ),
    },
    {
        "name": "duckdb_kommune_underwriting_analytics",
        "description": (
            "Callable target for `mcp_call_tool`. "
            "Returns full underwriting analytics package for one kommune."
        ),
    },
)

MCP_TOOLS: tuple[dict[str, str], ...] = DUCKDB_MCP_EXTENSION_FUNCTIONS

MCP_RESOURCES: tuple[dict[str, str], ...] = (
    {"uri": "duckdb://health", "name": "DuckDB Health", "description": "Connection status and version metadata for DuckDB."},
    {"uri": "duckdb://tables", "name": "DuckDB Tables", "description": "List of user-visible schema/table pairs."},
    {"uri": "duckdb://tools", "name": "DuckDB MCP Tools", "description": "Catalog of available MCP tools."},
    {"uri": "duckdb://tool-targets", "name": "DuckDB Callable Targets", "description": "Targets available for `mcp_call_tool`."},
)
