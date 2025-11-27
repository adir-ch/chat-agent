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

# Function to print configuration from config.json
print_config() {
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    local config_file="$script_dir/config.json"
    
    echo "Configuration:"
    echo "=============="
    
    # Pretty print the JSON config file using jq
    if [ -f "$config_file" ]; then
        if command -v jq >/dev/null 2>&1; then
            jq . "$config_file" 2>/dev/null || {
                echo "  Warning: Could not parse config.json"
                cat "$config_file"
            }
        else
            echo "  Warning: jq is not installed. Falling back to cat."
            cat "$config_file"
        fi
    else
        echo "  Warning: config.json not found at $config_file"
    fi
}

# Function to check and print API key status
check_api_keys() {
    local model_type="$1"
    
    echo ""
    echo "API Keys:"
    echo "========="
    
    # Check LANGCHAIN_API_KEY
    if [ -n "$LANGCHAIN_API_KEY" ]; then
        echo "  LANGCHAIN_API_KEY: Found in environment variables"
    else
        echo "  LANGCHAIN_API_KEY: Not found in environment variables"
    fi
    
    # Check OPENAI_API_KEY for GPT model
    if [ "$model_type" == "gpt" ]; then
        if [ -n "$OPENAI_API_KEY" ]; then
            echo "  OPENAI_API_KEY: Found in environment variables"
        else
            echo "  OPENAI_API_KEY: Not found in environment variables"
            return 1
        fi
    fi
    
    return 0
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
# API Key Environment Variables (only API keys are set via environment)
# ============================================================================
# Note: All other configuration values are loaded from config.json by default.
# Environment variables can still override JSON values if needed.

# LangSmith API Key (required for tracing)
export LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY:-}"

# ============================================================================
# Local Model Configuration (for Ollama)
# ============================================================================

if [ "$MODEL_NAME" == "local" ]; then
    echo "Starting agent with LOCAL model (Ollama)..."
    echo ""
    
    print_config
    check_api_keys "local"
    
    echo ""
    echo "Starting agent..."
    echo ""
    
    # Run local agent
    python ai-agent.py
fi

# ============================================================================
# GPT Model Configuration (for OpenAI)
# ============================================================================

if [ "$MODEL_NAME" == "gpt" ]; then
    export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
    
    echo "Starting agent with GPT model (OpenAI)..."
    echo ""
    
    print_config
    
    # Check API keys and exit if OPENAI_API_KEY is missing
    if ! check_api_keys "gpt"; then
        echo ""
        echo "Error: OPENAI_API_KEY is required for GPT model but was not found in environment variables."
        echo "Please set OPENAI_API_KEY before running the agent."
        exit 1
    fi
    
    echo ""
    echo "Starting agent..."
    echo ""
    
    # Run GPT agent
    python ai-agent_gpt.py
fi

