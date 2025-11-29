#!/bin/bash

# run_agent.sh - Run AI agent with local or GPT model
# Usage: ./run_agent.sh [local|gpt|docs]

set -e

# Usage function
usage() {
    echo "Usage: $0 [local|gpt|docs]"
    echo ""
    echo "  local  - Run agent with Ollama (local model)"
    echo "  gpt    - Run agent with OpenAI GPT model"
    echo "  docs   - Print configuration documentation and exit"
    exit 1
}

# Function to validate config.json (prints errors only, no documentation)
validate_config() {
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    local config_file="$script_dir/config.json"
    
    # Check if config.json exists
    if [ ! -f "$config_file" ]; then
        echo "Error: config.json not found at $config_file"
        exit 1
    fi
    
    # Validate JSON syntax
    if command -v jq >/dev/null 2>&1; then
        if ! jq . "$config_file" >/dev/null 2>&1; then
            echo "Error: config.json contains invalid JSON syntax"
            exit 1
        fi
    else
        # Fallback: use Python to validate JSON
        if ! python3 -m json.tool "$config_file" >/dev/null 2>&1; then
            echo "Error: config.json contains invalid JSON syntax"
            exit 1
        fi
    fi
    
    # Try to import config.py to validate values (this will exit if invalid)
    cd "$script_dir"
    if ! python3 -c "import config" 2>&1; then
        # config.py will print its own error messages
        exit 1
    fi
}

# Function to print documentation from config.json
print_documentation() {
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    local config_file="$script_dir/config.json"
    
    if [ ! -f "$config_file" ]; then
        echo "  Could not find config.json"
        return
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        echo "  Error: jq is required to display documentation but is not installed"
        return
    fi
    
    # Check if we can parse the JSON at all
    if ! jq . "$config_file" >/dev/null 2>&1; then
        echo "  Could not parse config.json to extract documentation"
        return
    fi
    
    echo ""
    echo "======================================================================"
    echo "CONFIGURATION DOCUMENTATION"
    echo "======================================================================"
    echo ""
    
    # Print description if it exists
    local description=$(jq -r '._documentation.description // empty' "$config_file" 2>/dev/null)
    if [ -n "$description" ] && [ "$description" != "null" ]; then
        echo "$description"
        echo ""
    fi
    
    # Print available configuration options
    echo "Available Configuration Options:"
    echo "----------------------------------------------------------------------"
    
    # Extract and format each documentation entry (excluding description)
    jq -r '._documentation | to_entries | .[] | select(.key != "description") | "  \(.key): \(.value)"' "$config_file" 2>/dev/null || echo "  Could not load documentation"
    
    echo "======================================================================"
    echo ""
}

# Function to print configuration from config.json (agent_config only)
print_config() {
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    local config_file="$script_dir/config.json"
    
    echo "Configuration:"
    echo "=============="
    
    # Pretty print only the agent_config section using jq
    if [ -f "$config_file" ]; then
        if command -v jq >/dev/null 2>&1; then
            jq '.agent_config' "$config_file" 2>/dev/null || {
                echo "  Warning: Could not parse config.json"
            }
        else
            echo "  Warning: jq is not installed. Cannot display configuration."
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
    echo "Error: parameter is required"
    usage
fi

MODEL_NAME="$1"

# Handle "docs" parameter
if [ "$MODEL_NAME" == "docs" ]; then
    print_documentation
    exit 0
fi

if [ "$MODEL_NAME" != "local" ] && [ "$MODEL_NAME" != "gpt" ]; then
    echo "Error: Invalid parameter. Must be 'local', 'gpt', or 'docs'"
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
# Validate Configuration
# ============================================================================
# Validate config.json before proceeding. This will exit with error if the config is invalid.

validate_config

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
    python ai_agent_local.py
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
    python ai_agent_gpt.py
fi

