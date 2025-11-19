# Chat Agent MVP

Local-first assistant for real estate agents. The project consists of a Vite/React frontend and two Go services that orchestrate queries to a local Ollama model, a SQLite profile store, and Elasticsearch.

## Prerequisites

- Node.js ≥ 20
- Go ≥ 1.22
- Ollama with a compatible chat model (e.g. `llama3.1`) running locally
- Elasticsearch ≥ 8.x
- Docker (optional for containerised setup)

## Project layout

- `frontend`: React/Vite single-page chat client
- `backend/profile`: Profile service that enriches prompts with agent context, calls Ollama, and persists conversations
- `backend/search`: Search facade over Elasticsearch for people and property lookups

## Quick start (local dev)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend connects to the agent service by default at `http://localhost:8070`. To configure a different URL, create a `.env` or `.env.local` file in the `frontend` directory:

```bash
# .env.local
VITE_AGENT_URL=http://localhost:8070
```

The dev server proxies `/api` requests to the profile service running on `http://localhost:8080` (for backward compatibility).

### Profile service

```bash
cd backend/profile
go mod tidy
go run ./cmd/profile
```

> Tip: `make -C backend build` compiles both services with an embedded Git version string (via `git describe`).

Environment variables:

- `PROFILE_LISTEN_ADDR` (default `:8080`)
- `PROFILE_DB_PATH` (default `profile.db`)
- `OLLAMA_URL` (default `http://localhost:11434`)
- `SEARCH_URL` (default `http://localhost:8090`)
- `SYSTEM_PROMPT` (optional override for base instructions)

Seed the SQLite database before starting:

```bash
sqlite3 profile.db < scripts/seed.sql
```

### Search service

```bash
cd backend/search
go mod tidy
go run ./cmd/search
```

Environment variables:

- `SEARCH_LISTEN_ADDR` (default `:8090`)
- `ELASTICSEARCH_URL` (default `http://localhost:9200`)
- `ES_INDEX_PEOPLE` (default `people`)
- `ES_INDEX_PROPERTY` (default `properties`)
- `ID4ME_API_URL` (required for SmartSearch endpoint)
- `SESSION_ID` (required for SmartSearch endpoint)
- `BEARER_TOKEN` (required for SmartSearch endpoint)

Index sample documents in Elasticsearch before chatting, or hook into your existing data pipeline.

## AI Agent service

Located in `backend/agent/`. Provides the `/chat` API endpoint for the frontend.

### Install 
- `cd backend/agent`
- `python3 -m venv venv`
- `pip install -r requirements.txt`

### Use 
- `source venv/bin/activate`
- `python ai-agent.py`
- `deactivate`

The agent service runs on port 8070 by default. Configure the frontend to use it by setting `VITE_AGENT_URL` in `frontend/.env.local`:

```bash
VITE_AGENT_URL=http://localhost:8070
```

## Docker Compose (optional)

See `docker-compose.yml` for a containerised setup that runs the frontend, both Go services, and Elasticsearch together. Update the Ollama endpoint to match your host environment.

## Next steps

- Add auth / agent identity flows
- Expand function-calling coverage and error handling
- Add unit and integration tests
- Automate Elasticsearch index management

