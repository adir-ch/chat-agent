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
- `backend/adapter`: API adapter that enriches prompts with agent context, calls Ollama, and persists conversations
- `backend/search`: Search facade over Elasticsearch for people and property lookups

## Quick start (local dev)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` requests to the adapter service running on `http://localhost:8080`.

### Adapter service

```bash
cd backend/adapter
go mod tidy
go run ./cmd/adapter
```

Environment variables:

- `ADAPTER_LISTEN_ADDR` (default `:8080`)
- `ADAPTER_DB_PATH` (default `adapter.db`)
- `OLLAMA_URL` (default `http://localhost:11434`)
- `SEARCH_URL` (default `http://localhost:8090`)
- `SYSTEM_PROMPT` (optional override for base instructions)

Seed the SQLite database before starting:

```bash
sqlite3 adapter.db < scripts/seed.sql
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

Index sample documents in Elasticsearch before chatting, or hook into your existing data pipeline.

## Docker Compose (optional)

See `docker-compose.yml` for a containerised setup that runs the frontend, both Go services, and Elasticsearch together. Update the Ollama endpoint to match your host environment.

## Next steps

- Add auth / agent identity flows
- Expand function-calling coverage and error handling
- Add unit and integration tests
- Automate Elasticsearch index management

