#!/bin/bash

# Initialize and seed the profile database
# Usage: init-db.sh [DB_PATH]
# If DB_PATH is not provided, defaults to ../bin/profile.db

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_DIR="$(dirname "$SCRIPT_DIR")"
INIT_SQL="$SCRIPT_DIR/init-db.sql"
SEED_FILE="$SCRIPT_DIR/seed.sql"

# Determine database path
if [ -n "$1" ]; then
    DB_PATH="$1"
else
    DB_PATH="$PROFILE_DIR/bin/profile.db"
fi

# Get directory of database file
DB_DIR="$(dirname "$DB_PATH")"

echo "Creating and seeding profile database..."
echo "Database path: $DB_PATH"

# Create directory if it doesn't exist
mkdir -p "$DB_DIR"

# Remove existing database if it exists
if [ -f "$DB_PATH" ]; then
    echo "Removing existing database..."
    rm -f "$DB_PATH"
fi

# Check if sqlite3 is available
if ! command -v sqlite3 &> /dev/null; then
    echo "Error: sqlite3 is not installed. Please install it first."
    echo "  macOS: brew install sqlite3"
    echo "  Ubuntu/Debian: sudo apt-get install sqlite3"
    exit 1
fi

# Check if init SQL file exists
if [ ! -f "$INIT_SQL" ]; then
    echo "Error: Init SQL file not found at $INIT_SQL"
    exit 1
fi

# Check if seed file exists
if [ ! -f "$SEED_FILE" ]; then
    echo "Error: Seed file not found at $SEED_FILE"
    exit 1
fi

# Create tables (migrations)
echo "Creating database tables..."
sqlite3 "$DB_PATH" < "$INIT_SQL"

# Seed the database
echo "Seeding database with $SEED_FILE..."
sqlite3 "$DB_PATH" < "$SEED_FILE"

echo "Database created and seeded successfully at $DB_PATH"

