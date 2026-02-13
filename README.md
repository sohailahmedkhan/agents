# Agents Workspace

AI-powered municipality intelligence platform for property underwriting and claims analysis. Uses LLM agents with MCP tool access to query and analyze Kartverket property data and insurance claims data.

## Project layout

- `backend/`: FastAPI + Python backend (agents, MCP, DuckDB)
- `frontend/`: Next.js + TypeScript frontend (dashboards, chat)
- `data/`: DuckDB database, Excel source files, API cache

## Backend architecture

- `backend/app/main.py`: app factory and API wiring
- `backend/app/core/settings.py`: environment-driven app settings
- `backend/app/api/agents/`: HTTP layer (routes, schemas, dependencies)
- `backend/app/agents/`: service layer and agent builders
  - `service.py`: core service — insights, chat orchestration, tool invocation
  - `orchestrator.py`: ADK LLM orchestrator (legacy compatibility wrapper)
  - `intent_classifier.py`: routes user questions to property/claims/both domains
  - `property_intelligence.py`: property-focused agent with MCP tools
  - `claims_intelligence.py`: claims-focused agent with MCP tools
  - `catalog.py`: analysis options catalog for UI workflows
- `backend/app/mcp/`: MCP implementation (plugins, client, servers)
  - `plugins/duckdb/server.py`: FastMCP server exposing DuckDB tools
  - `plugins/duckdb/contracts.py`: tool/resource metadata
  - `client/`: MCP client wrapper
- `backend/app/db/duckdb_service.py`: DuckDB wrapper with safety constraints
- `backend/app/modules/kartverket/`: Kartverket data processing pipeline

Design rule: keep API routing/validation in `app/api`, and business logic in `app/agents`.

## Frontend architecture

- `frontend/src/app/`: Next.js App Router routes
  - `main/`: kommune selector and entry point
  - `main/insights/`: municipality insights dashboard
  - `automated-analysis/`: analysis workflow UI
- `frontend/src/components/features/`: feature-specific components
  - `main/`: landing page components
  - `insights/`: dashboard views (property exposure, occupancy, claims)
  - `chat/`: interactive chat UI
  - `automated-analysis/`: analysis workflow components
- `frontend/src/components/ui/`: reusable UI primitives (Radix UI)
- `frontend/src/components/shared/themes.ts`: shared styling tokens/themes

## Quick start

### Environment Setup

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env and set VERTEX_PROJECT_ID at minimum
```

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8101
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --port 3100
```

### Docker Compose

```bash
docker-compose up
```

## Ports

- Frontend: `http://localhost:3100`
- Backend: `http://localhost:8101`
- MCP HTTP server (optional): `http://localhost:8200`

## API endpoints

All routes are prefixed with `/agents`:

| Route | Method | Description |
|-------|--------|-------------|
| `/agents/health` | GET | Agents runtime capability status |
| `/agents/kommuner` | GET | List available municipalities |
| `/agents/kommune-insights` | GET | Full municipality insights (property + claims) |
| `/agents/chat` | POST | Run LLM chat with MCP tool access |
| `/agents/analysis-options` | GET | Selectable analysis options for UI |
| `/agents/duckdb/health` | GET | DuckDB connectivity status |
| `/agents/duckdb/tables` | GET | List available tables |
| `/agents/duckdb/query` | POST | Execute SQL with safety constraints |
| `/agents/tools` | GET | List available tools |
| `/agents/tools/invoke` | POST | Invoke a tool directly |
| `/agents/mcp/resources` | GET | List MCP resources |
| `/agents/mcp/resource` | GET | Read one MCP resource by URI |
| `/agents/mcp/tools` | GET | List MCP tools |

## DuckDB support

Optional environment variables:

- `DUCKDB_PATH` (default: `data/db/agenticDB.duckdb`)
- `DUCKDB_READ_ONLY` (`true`/`false`, default `false`)
- `DUCKDB_ALLOW_WRITE` (`true`/`false`, default `false`)

By default, write SQL is blocked for safety.

## ADK + Vertex LLM

The backend chat flow uses Google ADK with Vertex as provider and Claude Sonnet 4.5 as
the default model. User questions are routed through an intent classifier to
domain-specific agents (property intelligence, claims intelligence, or both).

Required environment variables:

- `VERTEX_PROJECT_ID` (or `GOOGLE_CLOUD_PROJECT`)
- `VERTEX_LOCATION` (default: `europe-west1`)

Optional:

- `LLM_MODEL` (default: `claude-sonnet-4-5`)
- `LLM_PROVIDER` (default: `vertex_anthropic`)
- `ADK_MCP_HTTP_ENABLED` (`true`/`false`, default `false`) — persistent MCP HTTP server vs stdio transport

Dependencies are in `backend/requirements.txt`, including:

- `google-adk`
- `anthropic[vertex]`
- `mcp`
- `fastmcp`

## MCP Server (DuckDB)

`backend/app/mcp/plugins/duckdb/` contains:

- `server.py`: FastMCP server exposing DuckDB via MCP extension-style tools
- `contracts.py`: tool/resource metadata and call target catalog
- `plugin.py`: plugin implementation

Tool flow:

- Use `mcp_call_tool` as execution entrypoint.
- Discover tools via `mcp_list_tools`.
- Core DuckDB targets: `duckdb_health`, `duckdb_list_tables`, `duckdb_describe_table`, `duckdb_query`
- Kommune-specific targets include: `duckdb_kommune_occupancy_distribution`,
  `duckdb_kommune_underwriting_analytics`, `duckdb_kommune_claims_analytics`,
  and sectional tools for exposure, risk mix, age/standard, status, heritage,
  tenant activity, data quality, claims cause/status/trend/concentration.

Run MCP server directly:

```bash
cd backend
python -m app.mcp.plugins.duckdb.server --transport stdio
```

Or streamable HTTP:

```bash
cd backend
python -m app.mcp.plugins.duckdb.server --transport http --host 127.0.0.1 --port 8200
```

## Kartverket load into DuckDB

To load Kartverket Excel files into `main.properties`:

```bash
cd backend
python scripts/load_kartverket_to_duckdb.py
```

Defaults used by the script:
- Source files: `data/excel/raw/kartverket`
- DuckDB file: `data/db/agenticDB.duckdb`
- Processing pipeline: `backend/app/modules/kartverket/service.py`

## Claims load into DuckDB

To load claims Excel files into `main.claims`:

```bash
cd backend
python scripts/load_claims_to_duckdb.py
```

Defaults used by the script:
- Source files: `data/excel/raw/claims`
- DuckDB file: `data/db/agenticDB.duckdb`
