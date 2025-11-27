#!/bin/bash

# run_agent.sh - Run AI agent with local or GPT model
# Usage: ./run_agent.sh [local|gpt]

set -e

# Usage function
usage() {
    echo "Usage: $0 [local|gpt]"
    echo ""
    echo "  local  - Run agent with Ollama (local model)"
    echo "  gpt    - Run agent with OpenAI GPT model"
    exit 1
}

# Validate argument
if [ $# -eq 0 ]; then
    echo "Error: model-name parameter is required"
    usage
fi

MODEL_NAME="$1"

if [ "$MODEL_NAME" != "local" ] && [ "$MODEL_NAME" != "gpt" ]; then
    echo "Error: Invalid model-name. Must be 'local' or 'gpt'"
    usage
fi

# ============================================================================
# Common Environment Variables (shared by both local and GPT)
# ============================================================================

# LangSmith configuration
export LANGCHAIN_TRACING_V2="${LANGCHAIN_TRACING_V2:-true}"
export LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY:-}"
export LANGCHAIN_PROJECT="${LANGCHAIN_PROJECT:-chat-agent}"
export LANGCHAIN_ENDPOINT="${LANGCHAIN_ENDPOINT:-}"

# Service URLs
export FETCH_URL="${FETCH_URL:-http://localhost:8090/search/smart}"
export PROFILE_URL="${PROFILE_URL:-http://localhost:8080}"

# Server configuration
export SERVER_HOST="${SERVER_HOST:-0.0.0.0}"
export SERVER_PORT="${SERVER_PORT:-8070}"

# CORS configuration
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:5173,http://localhost:3000}"

# Embedding configuration
export USE_EMBEDDINGS="${USE_EMBEDDINGS:-false}"
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-text-embedding-3-small}"
export EMBEDDING_TOP_K="${EMBEDDING_TOP_K:-5}"

# ============================================================================
# Local Model Environment Variables (for Ollama)
# ============================================================================

if [ "$MODEL_NAME" == "local" ]; then
    export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3:latest}"
    export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
    
    echo "Starting agent with LOCAL model (Ollama)..."
    echo "  OLLAMA_MODEL: $OLLAMA_MODEL"
    echo "  OLLAMA_BASE_URL: $OLLAMA_BASE_URL"
    echo ""
    
    # Run local agent
    python ai-agent.py
fi

# ============================================================================
# GPT Model Environment Variables (for OpenAI)
# ============================================================================

if [ "$MODEL_NAME" == "gpt" ]; then
    export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
    export OPENAI_MODEL="${OPENAI_MODEL:-gpt-5-mini}"
    export OPENAI_TEMPERATURE="${OPENAI_TEMPERATURE:-0.7}"
    export OPENAI_MAX_TOKENS="${OPENAI_MAX_TOKENS:-}"
    export OPENAI_BASE_URL="${OPENAI_BASE_URL:-}"
    
    echo "Starting agent with GPT model (OpenAI)..."
    echo "  OPENAI_MODEL: $OPENAI_MODEL"
    echo "  OPENAI_TEMPERATURE: $OPENAI_TEMPERATURE"
    if [ -n "$OPENAI_BASE_URL" ]; then
        echo "  OPENAI_BASE_URL: $OPENAI_BASE_URL"
    fi
    echo ""
    
    # Validate OPENAI_API_KEY is set
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "Warning: OPENAI_API_KEY is not set. The agent may fail to start."
    fi
    
    # Run GPT agent
    python ai-agent_gpt.py
fi

