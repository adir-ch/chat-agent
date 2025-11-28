# Chat Agent MVP

Local-first assistant for real estate agents. The project consists of a Vite/React frontend and two Go services that orchestrate queries to a local Ollama model, a SQLite profile store, and Elasticsearch.

## Prerequisites

- Node.js ≥ 20
- Go ≥ 1.22
- Python 3 (for agent service)
- Ollama with a compatible chat model (e.g. `llama3.1`) running locally
- Elasticsearch ≥ 8.x
- Docker (optional for containerised setup)
- `jq` (optional, for JSON processing in scripts)
- `sqlite3` (for database operations)

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

The frontend connects to the agent service by default at `http://localhost:8070`. To configure different URLs, create a `.env` or `.env.local` file in the `frontend` directory:

```bash
# .env.local
VITE_AGENT_URL=http://localhost:8070
VITE_PROFILE_URL=http://localhost:8080
```

- `VITE_AGENT_URL`: The URL of the agent service API endpoint (default: `http://localhost:8070`)
- `VITE_PROFILE_URL`: The URL of the profile service API endpoint (default: `http://localhost:8080`)

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
- `ID4ME_API_KEY` (required for SmartSearch endpoint - API key for https://admin.id4me.me/SearchAPI)

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

Environment variables:

- `OLLAMA_MODEL` (default `llama3:latest`) - The Ollama model to use (e.g., `llama3:latest`, `gemma3:1b`, `qwen3:0.6b`)
- `OLLAMA_BASE_URL` (default `http://localhost:11434`) - The base URL for the Ollama service
- `FETCH_URL` (default `http://localhost:8090/search/smart`) - The URL for the search service SmartSearch endpoint
- `PROFILE_URL` (default `http://localhost:8080`) - The URL for the profile service
- `SERVER_HOST` (default `0.0.0.0`) - The host address to bind the server to
- `SERVER_PORT` (default `8070`) - The port number to run the server on
- `CORS_ORIGINS` (default `http://localhost:5173,http://localhost:3000`) - Comma-separated list of allowed CORS origins

## Building for Deployment

The project includes build scripts to compile and prepare the application for deployment.

### Prerequisites for Building

- Node.js ≥ 20 (for frontend build)
- Go ≥ 1.22 (for backend build)
- Python 3 (for agent service)
- `jq` (optional, for JSON processing in scripts)
- `sqlite3` (for database initialization)

### Build Scripts

#### Frontend Build

Build the frontend application:

```bash
cd frontend/build
./build.sh
```

This will:
- Install npm dependencies
- Build the application using `npm run build`
- Output the built files to `frontend/dist/`

#### Backend Build

Build backend services and prepare deployment:

```bash
cd backend/build
./build.sh <deployment-location> [os]
```

This will:
- Build profile and search Go binaries for the specified OS (or current OS if not specified)
- Copy binaries and required files to `<deployment-location>/`
- Initialize SQLite database with seed data
- Copy agent Python files and configuration

Parameters:
- `deployment-location`: Directory path where services will be deployed (required)
- `os`: Target operating system - `windows`, `linux`, or `macos` (optional, defaults to current OS)

Examples:
```bash
# Build for current OS
./build.sh /path/to/deploy

# Build for Linux
./build.sh /path/to/deploy linux

# Build for Windows
./build.sh /path/to/deploy windows

# Build for macOS
./build.sh /path/to/deploy macos
```

**Note**: Cross-compilation requires Go to be installed. The binaries will be built for the specified OS regardless of the build machine's OS.

#### Pipeline Build (Recommended)

Build both frontend and backend together:

```bash
cd pipeline
./build.sh <deployment-location> [os]
```

This will:
- Build backend services and deploy to `<deployment-location>/backend`
- Build frontend application and deploy to `<deployment-location>/client`

Parameters:
- `deployment-location`: Directory path where the application will be deployed (required)
- `os`: Target operating system for backend - `windows`, `linux`, or `macos` (optional, defaults to current OS)

Examples:
```bash
# Build for current OS
./build.sh /path/to/deploy

# Build backend for Linux
./build.sh /path/to/deploy linux

# Build backend for Windows
./build.sh /path/to/deploy windows
```

The deployment structure will be:
```
<deployment-location>/
├── backend/          # Backend services and agent files
│   ├── profile      # Profile service binary
│   ├── search       # Search service binary
│   ├── profile.db   # SQLite database
│   ├── ai-agent.py
│   ├── ai-agent_gpt.py
│   ├── config.py
│   ├── config.json
│   ├── requirements.txt
│   └── run_agent.sh
└── client/          # Frontend built files
    ├── index.html
    └── assets/
```

### Running Built Services

After building, use the `run_services.sh` script to start all services:

```bash
cd <deployment-location>/backend
./run_services.sh
```

This script will:
- Start profile service (port 8080)
- Start search service (port 8090)
- Set up Python virtual environment for agent service
- Install Python dependencies
- Start agent service (port 8070, model: local by default)

All services run in the background with timestamped log files in `./logs/`.

#### Environment Variables

You can configure services using environment variables before running:

```bash
# Agent model selection (local or gpt)
export AGENT_MODEL=local  # or gpt

# Profile service
export PROFILE_LISTEN_ADDR=:8080
export PROFILE_DB_PATH=./profile.db

# Search service
export SEARCH_LISTEN_ADDR=:8090
export ELASTICSEARCH_URL=http://localhost:9200

# Agent API keys (required for GPT model)
export OPENAI_API_KEY=your-key-here
export LANGCHAIN_API_KEY=your-key-here

./run_services.sh
```

#### Viewing Logs

```bash
# View all logs
tail -f logs/*.log

# View specific service logs
tail -f logs/YYYY-MM-DD_HH-MM-SS_profile.log
tail -f logs/YYYY-MM-DD_HH-MM-SS_search.log
tail -f logs/YYYY-MM-DD_HH-MM-SS_agent.log
```

#### Stopping Services

The script displays PIDs for each service. Stop them using:

```bash
# Stop all services
kill <PROFILE_PID> <SEARCH_PID> <AGENT_PID>

# Or stop individually
kill <PROFILE_PID>   # Stop profile service
kill <SEARCH_PID>    # Stop search service
kill <AGENT_PID>     # Stop agent service
```

### Agent Configuration

The agent service uses `config.json` for configuration. To view available options:

```bash
cd <deployment-location>/backend
./run_agent.sh docs
```

Configuration values can be overridden via environment variables. API keys (`LANGCHAIN_API_KEY`, `OPENAI_API_KEY`) must be set via environment variables only.

## Docker Compose (optional)

See `docker-compose.yml` for a containerised setup that runs the frontend, both Go services, and Elasticsearch together. Update the Ollama endpoint to match your host environment.

## Next steps

- Add auth / agent identity flows
- Expand function-calling coverage and error handling
- Add unit and integration tests
- Automate Elasticsearch index management

