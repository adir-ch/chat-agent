#!/bin/bash

# build.sh - Build frontend application using npm
# Usage: ./build.sh

set -e

# Get the script directory and frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Building frontend application"
echo "=========================================="
echo "Frontend directory: $FRONTEND_DIR"
echo ""

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found in $FRONTEND_DIR"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "Dependencies installed successfully"
echo ""

# Build the application
echo "Building application..."
npm run build

if [ $? -ne 0 ]; then
    echo "Error: Failed to build application"
    exit 1
fi

# Verify dist folder was created
DIST_DIR="$FRONTEND_DIR/dist"
if [ ! -d "$DIST_DIR" ]; then
    echo "Error: dist folder not found after build"
    exit 1
fi

echo ""
echo "=========================================="
echo "Frontend build completed successfully!"
echo "=========================================="
echo "Build output: $DIST_DIR"
echo ""

