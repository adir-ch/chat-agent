#!/bin/bash

# run_services.sh - Run profile and search services with environment variables
# Usage: ./run_services.sh
# Always runs both services in the background with timestamped log files

set -e

# ============================================================================
# Profile Service Environment Variables
# ============================================================================

export PROFILE_LISTEN_ADDR="${PROFILE_LISTEN_ADDR:-:8080}"
export PROFILE_DB_PATH="${PROFILE_DB_PATH:-./profile.db}"
export PROFILE_LISTINGS_LIMIT="${PROFILE_LISTINGS_LIMIT:-5}"

# ============================================================================
# Search Service Environment Variables
# ============================================================================

export SEARCH_LISTEN_ADDR="${SEARCH_LISTEN_ADDR:-:8090}"
export ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://localhost:9200}"
export ES_INDEX_PEOPLE="${ES_INDEX_PEOPLE:-people}"
export ES_INDEX_PROPERTY="${ES_INDEX_PROPERTY:-properties}"
export SMART_SEARCH_SIZE="${SMART_SEARCH_SIZE:-15}"
export ID4ME_API_KEY="${ID4ME_API_KEY:-}"

# ============================================================================
# Display Configuration
# ============================================================================

echo "=========================================="
echo "Service Configuration"
echo "=========================================="
echo ""
echo "Profile Service:"
echo "  PROFILE_LISTEN_ADDR: $PROFILE_LISTEN_ADDR"
echo "  PROFILE_DB_PATH: $PROFILE_DB_PATH"
echo "  PROFILE_LISTINGS_LIMIT: $PROFILE_LISTINGS_LIMIT"
echo ""
echo "Search Service:"
echo "  SEARCH_LISTEN_ADDR: $SEARCH_LISTEN_ADDR"
echo "  ELASTICSEARCH_URL: $ELASTICSEARCH_URL"
echo "  ES_INDEX_PEOPLE: $ES_INDEX_PEOPLE"
echo "  ES_INDEX_PROPERTY: $ES_INDEX_PROPERTY"
echo "  SMART_SEARCH_SIZE: $SMART_SEARCH_SIZE"
if [ -n "$ID4ME_API_KEY" ]; then
    echo "  ID4ME_API_KEY: ${ID4ME_API_KEY:0:10}... (set)"
else
    echo "  ID4ME_API_KEY: (not set)"
fi
echo ""
echo "=========================================="
echo ""

# Create logs directory if it doesn't exist
LOGS_DIR="./logs"
mkdir -p "$LOGS_DIR"

# Generate timestamp for log files (format: YYYY-MM-DD_HH-MM-SS)
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Set log file paths
PROFILE_LOG="$LOGS_DIR/${TIMESTAMP}_profile.log"
SEARCH_LOG="$LOGS_DIR/${TIMESTAMP}_search.log"
AGENT_LOG="$LOGS_DIR/${TIMESTAMP}_agent.log"

echo "Starting all services in the background..."
echo ""

# Check if binaries exist
if [ ! -f "./profile" ]; then
    echo "Error: profile binary not found. Please run build.sh first."
    exit 1
fi

if [ ! -f "./search" ]; then
    echo "Error: search binary not found. Please run build.sh first."
    exit 1
fi

# Start profile service in background
echo "Starting profile service..."
./profile > "$PROFILE_LOG" 2>&1 &
PROFILE_PID=$!
echo "Profile service started (PID: $PROFILE_PID)"
echo "  Logs: $PROFILE_LOG"

# Wait a moment for profile to start
sleep 1

# Start search service in background
echo "Starting search service..."
./search > "$SEARCH_LOG" 2>&1 &
SEARCH_PID=$!
echo "Search service started (PID: $SEARCH_PID)"
echo "  Logs: $SEARCH_LOG"
echo ""

# Wait a moment for search to start
sleep 1

# ============================================================================
# Agent Service Setup and Start
# ============================================================================

echo "=========================================="
echo "Setting up agent service..."
echo "=========================================="

# Check if agent files exist
if [ ! -f "./run_agent.sh" ]; then
    echo "Warning: run_agent.sh not found. Skipping agent service."
    AGENT_PID=""
else
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        echo "Warning: python3 is not installed. Skipping agent service."
        AGENT_PID=""
    else
        # Set virtual environment path
        VENV_DIR="./venv"
        
        # Check if virtual environment exists
        if [ ! -d "$VENV_DIR" ]; then
            echo "Virtual environment not found. Creating virtual environment..."
            python3 -m venv "$VENV_DIR"
            
            if [ $? -ne 0 ]; then
                echo "Error: Failed to create virtual environment"
                exit 1
            fi
            
            echo "Virtual environment created successfully"
        else
            echo "Virtual environment found at $VENV_DIR"
        fi
        
        # Activate virtual environment
        echo "Activating virtual environment..."
        source "$VENV_DIR/bin/activate"
        
        # Check if requirements.txt exists
        if [ -f "./requirements.txt" ]; then
            echo "Installing/updating requirements..."
            pip install --quiet --upgrade pip
            pip install --quiet -r requirements.txt
            
            if [ $? -ne 0 ]; then
                echo "Error: Failed to install requirements"
                exit 1
            fi
            
            echo "Requirements installed successfully"
        else
            echo "Warning: requirements.txt not found. Skipping dependency installation."
        fi
        
        # Determine agent model (default to "local", can be overridden via AGENT_MODEL env var)
        AGENT_MODEL="${AGENT_MODEL:-local}"
        
        echo ""
        echo "Starting agent service (model: $AGENT_MODEL)..."
        
        # Start agent service in background with virtual environment activated
        # Use bash -c to ensure venv activation persists in the background process
        bash -c "source '$VENV_DIR/bin/activate' && ./run_agent.sh '$AGENT_MODEL'" > "$AGENT_LOG" 2>&1 &
        AGENT_PID=$!
        echo "Agent service started (PID: $AGENT_PID)"
        echo "  Logs: $AGENT_LOG"
        
        # Deactivate virtual environment (process is already started)
        deactivate
    fi
fi

echo ""

echo "=========================================="
echo "Services running in background"
echo "=========================================="
echo "Profile service PID: $PROFILE_PID"
echo "Search service PID: $SEARCH_PID"
if [ -n "$AGENT_PID" ]; then
    echo "Agent service PID: $AGENT_PID"
fi
echo ""
echo "To stop all services, use:"
if [ -n "$AGENT_PID" ]; then
    echo "  kill $PROFILE_PID $SEARCH_PID $AGENT_PID"
else
    echo "  kill $PROFILE_PID $SEARCH_PID"
fi
echo ""
echo "Or stop them individually:"
echo "  kill $PROFILE_PID  # Stop profile service"
echo "  kill $SEARCH_PID   # Stop search service"
if [ -n "$AGENT_PID" ]; then
    echo "  kill $AGENT_PID   # Stop agent service"
fi
echo ""
echo "View logs:"
echo "  tail -f $PROFILE_LOG  # Profile service logs"
echo "  tail -f $SEARCH_LOG   # Search service logs"
if [ -n "$AGENT_PID" ]; then
    echo "  tail -f $AGENT_LOG    # Agent service logs"
fi
echo ""
