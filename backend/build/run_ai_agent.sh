#!/bin/bash

# run_ai_agent.sh - Run AI agent service with Python virtual environment
# Usage: ./run_ai_agent.sh [model]
#   model: "gpt" or "local" (default: "gpt")
# Runs the agent service in the background with timestamped log files

set -e

# ============================================================================
# Agent Service Setup and Start
# ============================================================================

echo "=========================================="
echo "Setting up agent service..."
echo "=========================================="

# Check if agent files exist
if [ ! -f "./run_agent.sh" ]; then
    echo "Error: run_agent.sh not found. Please ensure agent files are present."
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install Python 3."
    exit 1
fi

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

# Determine agent model (default to "gpt", can be overridden via AGENT_MODEL env var or argument)
if [ -n "$1" ]; then
    AGENT_MODEL="$1"
else
    AGENT_MODEL="${AGENT_MODEL:-gpt}"
fi

# Create logs directory if it doesn't exist
LOGS_DIR="./logs"
mkdir -p "$LOGS_DIR"

# Generate timestamp for log files (format: YYYY-MM-DD_HH-MM-SS)
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Set log file path
AGENT_LOG="$LOGS_DIR/${TIMESTAMP}_agent.log"

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

echo ""
echo "=========================================="
echo "Agent service running in background"
echo "=========================================="
echo "Agent service PID: $AGENT_PID"
echo "Model: $AGENT_MODEL"
echo ""
echo "To stop the service, use:"
echo "  kill $AGENT_PID"
echo ""
echo "View logs:"
echo "  tail -f $AGENT_LOG"
echo ""

