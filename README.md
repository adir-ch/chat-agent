# Chat Agent MVP

Local-first assistant for real estate agents. The project consists of a Vite/React frontend and two Go services that orchestrate queries to a local Ollama model, a SQLite profile store, and Elasticsearch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Layout](#project-layout)
3. [Quick Start (Local Development)](#quick-start-local-development)
4. [Building for Deployment](#building-for-deployment)
5. [Running on Server (Linux)](#running-on-server-linux)
6. [Docker Compose](#docker-compose-optional)
7. [Next Steps](#next-steps)

## Prerequisites

- Node.js ≥ 20
- Go ≥ 1.22
- Python 3 (for agent service)
- Ollama with a compatible chat model (e.g. `llama3.1`) running locally
- Elasticsearch ≥ 8.x
- Docker (optional for containerised setup)
- `jq` (optional, for JSON processing in scripts)
- `sqlite3` (for database operations)

## Project Layout

- `frontend`: React/Vite single-page chat client
- `backend/profile`: Profile service that enriches prompts with agent context, calls Ollama, and persists conversations
- `backend/search`: Search facade over Elasticsearch for people and property lookups
- `backend/agent`: AI Agent orchestrating the flow

## Quick Start (Local Development)

### Starting All Services

#### 1. Frontend

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

#### 2. Profile Service

```bash
cd backend/profile
go mod tidy
go run ./cmd/profile
```

**Environment variables:**
- `PROFILE_LISTEN_ADDR` (default `:8080`)
- `PROFILE_DB_PATH` (default `profile.db`)
- `OLLAMA_URL` (default `http://localhost:11434`)
- `SEARCH_URL` (default `http://localhost:8090`)
- `SYSTEM_PROMPT` (optional override for base instructions)

**Initial setup:**
```bash
# Seed the SQLite database before starting
sqlite3 profile.db < scripts/seed.sql
```

> **Tip**: `make -C backend build` compiles both services with an embedded Git version string (via `git describe`).

#### 3. Search Service

```bash
cd backend/search
go mod tidy
go run ./cmd/search
```

**Environment variables:**
- `SEARCH_LISTEN_ADDR` (default `:8090`)
- `ELASTICSEARCH_URL` (default `http://localhost:9200`)
- `ES_INDEX_PEOPLE` (default `people`)
- `ES_INDEX_PROPERTY` (default `properties`)
- `ID4ME_API_KEY` (required for SmartSearch endpoint - API key for https://admin.id4me.me/SearchAPI)

**Initial setup:**
Index sample documents in Elasticsearch before chatting, or hook into your existing data pipeline.

#### 4. AI Agent Service

Located in `backend/agent/`. Provides the `/chat` API endpoint for the frontend.

**Installation:**
```bash
cd backend/agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Running:**
```bash
source venv/bin/activate
python ai-agent.py
# or for GPT model
./run_agent.sh gpt
```

**Environment variables:**
- `OLLAMA_MODEL` (default `llama3:latest`) - The Ollama model to use
- `OLLAMA_BASE_URL` (default `http://localhost:11434`) - The base URL for the Ollama service
- `FETCH_URL` (default `http://localhost:8090/search/smart`) - The URL for the search service SmartSearch endpoint
- `PROFILE_URL` (default `http://localhost:8080`) - The URL for the profile service
- `SERVER_HOST` (default `0.0.0.0`) - The host address to bind the server to
- `SERVER_PORT` (default `8070`) - The port number to run the server on
- `CORS_ORIGINS` (default `http://localhost:5173,http://localhost:3000`) - Comma-separated list of allowed CORS origins
- `OPENAI_API_KEY` (required for GPT model)
- `LANGCHAIN_API_KEY` (optional, for LangSmith tracing)

**Configuration:**
The agent service uses `config.json` for configuration. To view available options:
```bash
./run_agent.sh docs
```

Configuration values can be overridden via environment variables. API keys (`LANGCHAIN_API_KEY`, `OPENAI_API_KEY`) must be set via environment variables only.

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
- Build profile and search Go binaries (for specified OS or using Go's default environment)
- Copy binaries and required files to `<deployment-location>/`
- Initialize SQLite database with seed data
- Copy agent Python files and configuration

**Parameters:**
- `deployment-location`: Directory path where services will be deployed (required)
- `os`: Target operating system - `windows`, `linux`, or `macos` (optional)

**Examples:**
```bash
# Build using Go's default environment (current OS)
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

**Parameters:**
- `deployment-location`: Directory path where the application will be deployed (required)
- `os`: Target operating system for backend - `windows`, `linux`, or `macos` (optional)

**Examples:**
```bash
# Build using Go's default environment (current OS)
./build.sh /path/to/deploy

# Build backend for Linux
./build.sh /path/to/deploy linux

# Build backend for Windows
./build.sh /path/to/deploy windows

# Build backend for macOS
./build.sh /path/to/deploy macos
```

**Deployment structure:**
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

**Environment Variables:**

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

**Viewing Logs:**
```bash
# View all logs
tail -f logs/*.log

# View specific service logs
tail -f logs/YYYY-MM-DD_HH-MM-SS_profile.log
tail -f logs/YYYY-MM-DD_HH-MM-SS_search.log
tail -f logs/YYYY-MM-DD_HH-MM-SS_agent.log
```

**Stopping Services:**

The script displays PIDs for each service. Stop them using:

```bash
# Stop all services
kill <PROFILE_PID> <SEARCH_PID> <AGENT_PID>

# Or stop individually
kill <PROFILE_PID>   # Stop profile service
kill <SEARCH_PID>    # Stop search service
kill <AGENT_PID>     # Stop agent service
```

**Agent Configuration:**

The agent service uses `config.json` for configuration. To view available options:

```bash
cd <deployment-location>/backend
./run_agent.sh docs
```

Configuration values can be overridden via environment variables. API keys (`LANGCHAIN_API_KEY`, `OPENAI_API_KEY`) must be set via environment variables only.

## Running on Server (Linux)

This section covers deploying and running the application on a Linux server.

### Dependencies

Before running the application, install the following dependencies:

#### Frontend - Nginx

Install nginx to serve the frontend static files:

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install nginx
```

**CentOS/RHEL:**
```bash
sudo yum install nginx
# or for newer versions
sudo dnf install nginx
```

**Arch Linux:**
```bash
sudo pacman -S nginx
```

#### Backend Services - Go

Install Go (version ≥ 1.22) for running the backend services:

**Debian/Ubuntu:**
```bash
wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
```

Add to `~/.bashrc` or `~/.profile`:
```bash
export PATH=$PATH:/usr/local/go/bin
```

**Using package manager (may have older version):**
```bash
sudo apt install golang-go
```

#### Agent Service - Python 3.12

Install Python 3.12 and virtual environment support:

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

**CentOS/RHEL:**
```bash
sudo yum install python3.12 python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
```

**Verify installation:**
```bash
python3.12 --version
```

**Creating Virtual Environment:**

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

### Environment Variables

Set the following environment variables before running the services. You can create a `.env` file or export them in your shell session.

#### Profile Service

```bash
# Server configuration
export PROFILE_LISTEN_ADDR=":8080"                    # Listen address (default: :8080)
export PROFILE_DB_PATH="./profile.db"                 # SQLite database path (default: ./profile.db)
export PROFILE_LISTINGS_LIMIT="5"                     # Maximum listings to return (default: 5)

# External service URLs
export OLLAMA_URL="http://localhost:11434"            # Ollama service URL (default: http://localhost:11434)
export SEARCH_URL="http://localhost:8090"            # Search service URL (default: http://localhost:8090)

# Optional
export SYSTEM_PROMPT=""                               # Override system prompt (optional)
```

#### Search Service

```bash
# Server configuration
export SEARCH_LISTEN_ADDR=":8090"                     # Listen address (default: :8090)

# Elasticsearch configuration
export ELASTICSEARCH_URL="http://localhost:9200"      # Elasticsearch URL (default: http://localhost:9200)
export ES_INDEX_PEOPLE="people"                       # People index name (default: people)
export ES_INDEX_PROPERTY="properties"                # Property index name (default: properties)
export SMART_SEARCH_SIZE="15"                         # Smart search result size (default: 15)

# Required for SmartSearch endpoint
export ID4ME_API_KEY="your-api-key-here"              # ID4ME API key (required)
```

#### Agent Service

```bash
# Model selection
export AGENT_MODEL="local"                            # Agent model: "local" or "gpt" (default: local)

# Ollama configuration (for local model)
export OLLAMA_MODEL="llama3:latest"                   # Ollama model name (default: llama3:latest)
export OLLAMA_BASE_URL="http://localhost:11434"       # Ollama base URL (default: http://localhost:11434)

# Service URLs
export FETCH_URL="http://localhost:8090/search/smart" # Search service endpoint (default: http://localhost:8090/search/smart)
export PROFILE_URL="http://localhost:8080"            # Profile service URL (default: http://localhost:8080)

# Server configuration
export SERVER_HOST="0.0.0.0"                          # Server host (default: 0.0.0.0)
export SERVER_PORT="8070"                            # Server port (default: 8070)
export CORS_ORIGINS="http://your-domain.com"          # Allowed CORS origins, comma-separated (default: http://localhost:5173,http://localhost:3000)

# LangSmith configuration
export LANGCHAIN_TRACING_V2="true"                    # Enable LangSmith tracing (default: true)
export LANGCHAIN_API_KEY=""                           # LangSmith API key (required for tracing)
export LANGCHAIN_PROJECT="chat-agent"                 # LangSmith project name (default: chat-agent)
export LANGCHAIN_ENDPOINT=""                          # Custom LangSmith endpoint (optional)

# OpenAI configuration (required if AGENT_MODEL=gpt)
export OPENAI_API_KEY=""                              # OpenAI API key (required for GPT model)
export OPENAI_MODEL="gpt-5-mini"                      # OpenAI model name (default: gpt-5-mini)
export OPENAI_TEMPERATURE="0.7"                       # Temperature 0.0-2.0 (default: 0.7)
export OPENAI_MAX_TOKENS=""                           # Max tokens (optional, default: null)
export OPENAI_BASE_URL=""                             # Custom OpenAI endpoint (optional)

# Embedding configuration
export USE_EMBEDDINGS="false"                         # Enable embeddings (default: false)
export EMBEDDING_MODEL="text-embedding-3-small"       # Embedding model (default: text-embedding-3-small)
export EMBEDDING_TOP_K="5"                            # Top K results (default: 5)
```

### Example Setup Script

Create a setup script to export all environment variables:

```bash
#!/bin/bash
# setup-env.sh

# Profile Service
export PROFILE_LISTEN_ADDR=":8080"
export PROFILE_DB_PATH="./profile.db"
export PROFILE_LISTINGS_LIMIT="5"
export OLLAMA_URL="http://localhost:11434"
export SEARCH_URL="http://localhost:8090"

# Search Service
export SEARCH_LISTEN_ADDR=":8090"
export ELASTICSEARCH_URL="http://localhost:9200"
export ES_INDEX_PEOPLE="people"
export ES_INDEX_PROPERTY="properties"
export SMART_SEARCH_SIZE="15"
export ID4ME_API_KEY="your-api-key-here"

# Agent Service
export AGENT_MODEL="local"
export OLLAMA_MODEL="llama3:latest"
export OLLAMA_BASE_URL="http://localhost:11434"
export FETCH_URL="http://localhost:8090/search/smart"
export PROFILE_URL="http://localhost:8080"
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="8070"
export CORS_ORIGINS="http://your-domain.com"
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="your-langchain-key"
export LANGCHAIN_PROJECT="chat-agent"

# If using GPT model, uncomment:
# export AGENT_MODEL="gpt"
# export OPENAI_API_KEY="your-openai-key"
```

Source the script before running services:
```bash
source setup-env.sh
./run_services.sh
```

### Running Services

After setting environment variables, start all services:

```bash
cd <deployment-location>/backend
./run_services.sh
```

The script will:
- Start profile service on port 8080
- Start search service on port 8090
- Create Python virtual environment (if needed)
- Install Python dependencies
- Start agent service on port 8070

### Nginx Configuration

Configure nginx to serve the frontend and proxy API requests. Example configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Serve frontend static files
    root /path/to/deployment/client;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy agent service
    location /chat {
        proxy_pass http://localhost:8070;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Proxy profile service (if needed)
    location /api {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

## Docker Compose (optional)

See `docker-compose.yml` for a containerised setup that runs the frontend, both Go services, and Elasticsearch together. Update the Ollama endpoint to match your host environment.

## Next steps

- Add auth / agent identity flows
- Expand function-calling coverage and error handling
- Add unit and integration tests
- Automate Elasticsearch index management
