# Agents Workspace

Standalone monorepo for the extracted agents work.

## Project layout

- `backend/`: FastAPI backend
- `frontend/`: Next.js frontend

## Backend architecture

- `backend/app/main.py`: app factory and API wiring
- `backend/app/core/settings.py`: environment-driven app settings
- `backend/app/api/agents/`: HTTP layer
- `backend/app/services/agents/`: service layer
- `backend/app/mcp_server/`: MCP server + client implementation for DuckDB tool access
- `backend/app/agents/orchestrator.py`: ADK LLM orchestrator that decides tool usage

Design rule: keep API routing/validation in `app/api`, and logic in `app/services`.

## Frontend architecture

- `frontend/src/app/`: Next.js routes
- `frontend/src/components/features/automated-analysis/`: feature UI components
- `frontend/src/components/shared/themes.ts`: shared styling tokens/themes

## Quick start

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

## Ports

- Frontend: `http://localhost:3100`
- Backend: `http://localhost:8101`

## DuckDB support

The backend includes DuckDB support through `/agents/duckdb/*` endpoints:

- `GET /agents/duckdb/health`
- `GET /agents/duckdb/tables`
- `POST /agents/duckdb/query`

Optional environment variables:

- `DUCKDB_PATH` (default: `agents/data/db/agents.duckdb`)
- `DUCKDB_READ_ONLY` (`true`/`false`, default `false`)
- `DUCKDB_ALLOW_WRITE` (`true`/`false`, default `false`)

By default, write SQL is blocked for safety.

## ADK + Vertex LLM

The backend chat flow uses Google ADK with Vertex as provider and Sonnet 4.5 as
the default model.

Required environment variables:

- `VERTEX_PROJECT_ID` (or `GOOGLE_CLOUD_PROJECT`)
- `VERTEX_LOCATION` (default: `europe-west1`)

Optional:

- `LLM_MODEL` (default: `claude-sonnet-4-5`)
- `LLM_PROVIDER` (default: `vertex_anthropic`)

Dependencies are in `backend/requirements.txt`, including:

- `google-adk`
- `anthropic[vertex]`
- `mcp`
- `fastmcp`

## MCP Server (DuckDB)

`backend/app/mcp_server/` contains:

- `server.py`: FastMCP server exposing DuckDB via MCP extension-style tools
- `client.py`: local stdio MCP client wrapper used by API/agents service
- `contracts.py`: tool/resource metadata

Tool flow:

- Use `mcp_call_tool` as execution entrypoint.
- Discover tools via `mcp_list_tools`.
- DuckDB targets for `mcp_call_tool`:
  - `duckdb_health`
  - `duckdb_list_tables`
  - `duckdb_describe_table`
  - `duckdb_query`

Run MCP server directly:

```bash
cd backend
python -m app.mcp_server.server --transport stdio
```

Or streamable HTTP:

```bash
cd backend
python -m app.mcp_server.server --transport http --host 127.0.0.1 --port 8200
```

## Kartverket load into DuckDB

To process Kartverket Excel files with the local agents pipeline and load them
into `main.properties` (excluding Google Maps links):

```bash
cd backend
python scripts/load_kartverket_to_duckdb.py
```

Defaults used by the script:
- Source files: `agents/data/excel/raw/kartverket`
- DuckDB file: `agents/data/db/agents.duckdb`
- Processing pipeline: `backend/app/scripts/kartverket_pipeline.py`
