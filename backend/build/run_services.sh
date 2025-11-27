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

echo "Starting both services in the background..."
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

echo "=========================================="
echo "Services running in background"
echo "=========================================="
echo "Profile service PID: $PROFILE_PID"
echo "Search service PID: $SEARCH_PID"
echo ""
echo "To stop the services, use:"
echo "  kill $PROFILE_PID $SEARCH_PID"
echo ""
echo "Or stop them individually:"
echo "  kill $PROFILE_PID  # Stop profile service"
echo "  kill $SEARCH_PID   # Stop search service"
echo ""
echo "View logs:"
echo "  tail -f $PROFILE_LOG  # Profile service logs"
echo "  tail -f $SEARCH_LOG    # Search service logs"
echo ""
