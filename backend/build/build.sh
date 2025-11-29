#!/bin/bash

# build.sh - Build services and prepare deployment location
# Usage: ./build.sh <location> [os]
#   os: windows, linux, or macos (optional, defaults to current OS)

set -e

# Usage function
usage() {
    echo "Usage: $0 <location> [os]"
    echo ""
    echo "  location  - Directory path where services will be deployed"
    echo "  os        - Target operating system: windows, linux, or macos (optional)"
    echo "              If not specified, builds using Go's default environment"
    echo ""
    echo "This script will:"
    echo "  1. Build profile and search services using Makefile"
    echo "  2. Copy binaries to the location directory"
    echo "  3. Initialize profile database with seed data"
    echo "  4. Copy agent files to the location directory"
    exit 1
}

# Validate argument
if [ $# -eq 0 ]; then
    echo "Error: location parameter is required"
    usage
fi

LOCATION="$1"
TARGET_OS="${2:-}"

# Initialize BINARY_EXT variable
BINARY_EXT=""

# Map OS parameter to GOOS and GOARCH if provided
if [ -n "$TARGET_OS" ]; then
    case "$TARGET_OS" in
        windows)
            export GOOS=windows
            export GOARCH=amd64
            BINARY_EXT=".exe"
            ;;
        linux)
            export GOOS=linux
            export GOARCH=arm64
            BINARY_EXT=""
            ;;
        macos|darwin)
            export GOOS=darwin
            export GOARCH=amd64
            BINARY_EXT=""
            ;;
        *)
            echo "Error: Invalid OS parameter: $TARGET_OS"
            echo "Valid options: windows, linux, macos"
            exit 1
            ;;
    esac
    
    # Set CGO_ENABLED if not already set (default to 1 for non-Linux, 0 for Linux)
    if [ "$GOOS" = "linux" ] && [ -z "$CGO_ENABLED" ]; then
        export CGO_ENABLED=1
    elif [ -z "$CGO_ENABLED" ]; then
        export CGO_ENABLED=1
    fi
    
    echo "Building for target OS: $TARGET_OS (GOOS=$GOOS, GOARCH=$GOARCH, CGO_ENABLED=$CGO_ENABLED)"
else
    # Use Go's default environment (no explicit OS set)
    echo "Building using Go's default environment"
fi

# Get the script directory and backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"

echo "=========================================="
echo "Building services and preparing deployment"
echo "=========================================="
echo "Location: $LOCATION"
echo "Backend directory: $BACKEND_DIR"
echo ""

# Create location directory if it doesn't exist
echo "Creating deployment location directory..."
mkdir -p "$LOCATION"

# Clean and build services using Makefile
echo ""
echo "Cleaning previous builds..."
cd "$BACKEND_DIR"
make clean

echo ""
echo "Building services using Makefile..."
make build

# Verify binaries were created
# If OS was specified, use BINARY_EXT, otherwise check for both .exe and no extension
if [ -n "$TARGET_OS" ]; then
    PROFILE_BIN="$BACKEND_DIR/profile/bin/profile$BINARY_EXT"
    SEARCH_BIN="$BACKEND_DIR/search/bin/search$BINARY_EXT"
else
    # Try to find binary (could be .exe on Windows or no extension on Unix)
    if [ -f "$BACKEND_DIR/profile/bin/profile.exe" ]; then
        PROFILE_BIN="$BACKEND_DIR/profile/bin/profile.exe"
        SEARCH_BIN="$BACKEND_DIR/search/bin/search.exe"
        BINARY_EXT=".exe"
    else
        PROFILE_BIN="$BACKEND_DIR/profile/bin/profile"
        SEARCH_BIN="$BACKEND_DIR/search/bin/search"
        BINARY_EXT=""
    fi
fi

if [ ! -f "$PROFILE_BIN" ]; then
    echo "Error: Profile binary not found at $PROFILE_BIN"
    exit 1
fi

if [ ! -f "$SEARCH_BIN" ]; then
    echo "Error: Search binary not found at $SEARCH_BIN"
    exit 1
fi

echo "Services built successfully"
echo ""

# Copy binaries to location
echo "Copying binaries to $LOCATION..."
cp "$PROFILE_BIN" "$LOCATION/profile$BINARY_EXT"
cp "$SEARCH_BIN" "$LOCATION/search$BINARY_EXT"

# Only set executable permissions on Unix-like systems
if [ -z "$GOOS" ] || [ "$GOOS" != "windows" ]; then
    chmod +x "$LOCATION/profile$BINARY_EXT"
    chmod +x "$LOCATION/search$BINARY_EXT"
fi

echo "Binaries copied successfully"
echo ""

# Copy SQL files to location
echo "Copying SQL files to $LOCATION..."
INIT_SQL="$BACKEND_DIR/profile/scripts/init-db.sql"
SEED_SQL="$BACKEND_DIR/profile/scripts/seed.sql"

if [ ! -f "$INIT_SQL" ]; then
    echo "Error: init-db.sql not found at $INIT_SQL"
    exit 1
fi

if [ ! -f "$SEED_SQL" ]; then
    echo "Error: seed.sql not found at $SEED_SQL"
    exit 1
fi

cp "$INIT_SQL" "$LOCATION/init-db.sql"
cp "$SEED_SQL" "$LOCATION/seed.sql"
echo "SQL files copied successfully"
echo ""

# Initialize profile database
echo "Initializing profile database..."
DB_PATH="$LOCATION/profile.db"

# Check if sqlite3 is available
if ! command -v sqlite3 &> /dev/null; then
    echo "Error: sqlite3 is not installed. Please install it first."
    echo "  macOS: brew install sqlite3"
    echo "  Ubuntu/Debian: sudo apt-get install sqlite3"
    exit 1
fi

# Remove existing database if it exists
if [ -f "$DB_PATH" ]; then
    echo "Removing existing database..."
    rm -f "$DB_PATH"
fi

# Create tables
echo "Creating database tables..."
sqlite3 "$DB_PATH" < "$LOCATION/init-db.sql"

# Seed the database
echo "Seeding database..."
sqlite3 "$DB_PATH" < "$LOCATION/seed.sql"

echo "Database initialized successfully at $DB_PATH"
echo ""

# Copy run_services.sh
cp "$BACKEND_DIR/build/run_services.sh" "$LOCATION/"
chmod +x "$LOCATION/run_services.sh"

# Copy run_ai_agent.sh
cp "$BACKEND_DIR/build/run_ai_agent.sh" "$LOCATION/"
chmod +x "$LOCATION/run_ai_agent.sh"

# Copy agent files
echo "Copying agent files to $LOCATION..."
AGENT_DIR="$BACKEND_DIR/agent"

# Copy Python files
cp "$AGENT_DIR/agent.py" "$LOCATION/"
cp "$AGENT_DIR/ai_agent_local.py" "$LOCATION/"
cp "$AGENT_DIR/ai_agent_gpt.py" "$LOCATION/"
cp "$AGENT_DIR/config.py" "$LOCATION/"
cp "$AGENT_DIR/prompts.py" "$LOCATION/"
cp "$AGENT_DIR/embeddings.py" "$LOCATION/"

# Copy requirements.txt
cp "$AGENT_DIR/requirements.txt" "$LOCATION/"

# Copy config.json
cp "$AGENT_DIR/config.json" "$LOCATION/"

# Copy run_agent.sh
cp "$AGENT_DIR/run_agent.sh" "$LOCATION/"
chmod +x "$LOCATION/run_agent.sh"

echo "Agent files copied successfully"
echo ""

echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
echo "Deployment location: $LOCATION"
echo ""
echo "Files created:"
if [ -n "$TARGET_OS" ]; then
    echo "  - profile$BINARY_EXT (binary for $GOOS/$GOARCH)"
    echo "  - search$BINARY_EXT (binary for $GOOS/$GOARCH)"
else
    echo "  - profile$BINARY_EXT (binary)"
    echo "  - search$BINARY_EXT (binary)"
fi
echo "  - profile.db (database)"
echo "  - init-db.sql"
echo "  - seed.sql"
echo "  - agent.py"
echo "  - ai_agent_local.py"
echo "  - ai_agent_gpt.py"
echo "  - config.py"
echo "  - prompts.py"
echo "  - embeddings.py"
echo "  - requirements.txt"
echo "  - run_agent.sh"
echo "  - run_services.sh"
echo "  - run_ai_agent.sh"
echo ""

