#!/bin/bash

# run_agent.sh - Run AI agent with selected model type from config
# Usage: ./run_agent.sh [model_type|docs]
# Example: ./run_agent.sh ollama
# Example: ./run_agent.sh openai

set -e

# Usage function
usage() {
    echo "Usage: $0 [model_type|docs]"
    echo ""
    echo "  model_type  - Model type from config.json models array (e.g., 'ollama', 'openai')"
    echo "  docs        - Print configuration documentation and exit"
    echo ""
    echo "Available model types are defined in config.json under agent_config.models"
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

# Function to get available model types from config
get_available_model_types() {
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    cd "$script_dir"
    python3 -c "from config import Config; import json; types = Config.get_available_model_types(); print(json.dumps(types))" 2>/dev/null || echo "[]"
}

# Function to validate model type exists in config
validate_model_type() {
    local model_type="$1"
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    cd "$script_dir"
    python3 -c "from config import Config; import sys; sys.exit(0 if Config.validate_model_type('$model_type') else 1)" 2>/dev/null
}

# Function to show available model types
show_available_models() {
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    local config_file="$script_dir/config.json"
    
    echo "Available model types in config.json:"
    echo "====================================="
    
    if command -v jq >/dev/null 2>&1; then
        jq -r '.agent_config.models[] | "  - \(.type) (model: \(.model))"' "$config_file" 2>/dev/null || {
            echo "  Warning: Could not parse config.json to extract model types"
        }
    else
        echo "  Warning: jq is not installed. Cannot display available model types."
    fi
    echo ""
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
    
    # Check OPENAI_API_KEY for OpenAI model
    if [ "$model_type" == "openai" ]; then
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
    echo "Error: model type parameter is required"
    echo ""
    show_available_models
    usage
fi

MODEL_TYPE="$1"

# Handle "docs" parameter
if [ "$MODEL_TYPE" == "docs" ]; then
    print_documentation
    exit 0
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
# Validate Model Type
# ============================================================================
# Validate that the selected model type exists in config.json

if ! validate_model_type "$MODEL_TYPE"; then
    echo "Error: Model type '$MODEL_TYPE' not found in config.json"
    echo ""
    show_available_models
    echo "Please select one of the available model types listed above."
    exit 1
fi

# ============================================================================
# Run Agent with Selected Model Type
# ============================================================================

# Map model type to script and API key requirements
case "$MODEL_TYPE" in
    "ollama")
        echo "Starting agent with OLLAMA model..."
        echo ""
        
        print_config
        check_api_keys "ollama"
        
        echo ""
        echo "Starting agent..."
        echo ""
        
        # Run local agent
        python ai_agent_local.py
        ;;
    "openai")
        export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
        
        echo "Starting agent with OPENAI model..."
        echo ""
        
        print_config
        
        # Check API keys and exit if OPENAI_API_KEY is missing
        if ! check_api_keys "openai"; then
            echo ""
            echo "Error: OPENAI_API_KEY is required for OpenAI model but was not found in environment variables."
            echo "Please set OPENAI_API_KEY before running the agent."
            exit 1
        fi
        
        echo ""
        echo "Starting agent..."
        echo ""
        
        # Run GPT agent
        python ai_agent_gpt.py
        ;;
    *)
        echo "Error: Unsupported model type '$MODEL_TYPE'"
        echo ""
        show_available_models
        exit 1
        ;;
esac

