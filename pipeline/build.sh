#!/bin/bash

# build.sh - Build backend and frontend and deploy to location
# Usage: ./build.sh <location>

set -e

# Usage function
usage() {
    echo "Usage: $0 <location> [os]"
    echo ""
    echo "  location  - Directory path where the application will be deployed"
    echo "  os        - Target operating system for backend: windows, linux, or macos (optional)"
    echo "              If not specified, builds using Go's default environment"
    echo ""
    echo "This script will:"
    echo "  1. Build backend services and deploy to <location>/backend"
    echo "  2. Build frontend application and deploy to <location>/client"
    exit 1
}

# Validate argument
if [ $# -eq 0 ]; then
    echo "Error: location parameter is required"
    usage
fi

LOCATION="$1"
TARGET_OS="${2:-}"

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_BUILD_SCRIPT="$PROJECT_ROOT/backend/build/build.sh"
FRONTEND_BUILD_SCRIPT="$PROJECT_ROOT/frontend/build/build.sh"

echo "=========================================="
echo "Building and deploying application"
echo "=========================================="
echo "Deployment location: $LOCATION"
echo "Project root: $PROJECT_ROOT"
echo ""

# Validate build scripts exist
if [ ! -f "$BACKEND_BUILD_SCRIPT" ]; then
    echo "Error: Backend build script not found at $BACKEND_BUILD_SCRIPT"
    exit 1
fi

if [ ! -f "$FRONTEND_BUILD_SCRIPT" ]; then
    echo "Error: Frontend build script not found at $FRONTEND_BUILD_SCRIPT"
    exit 1
fi

# Create location directory if it doesn't exist
echo "Creating deployment location directory..."
mkdir -p "$LOCATION"

# Build and deploy backend
echo ""
echo "=========================================="
echo "Building and deploying backend..."
echo "=========================================="
BACKEND_LOCATION="$LOCATION/backend"

# Call backend build script with backend location and optional OS parameter
if [ -n "$TARGET_OS" ]; then
    "$BACKEND_BUILD_SCRIPT" "$BACKEND_LOCATION" "$TARGET_OS"
else
    "$BACKEND_BUILD_SCRIPT" "$BACKEND_LOCATION"
fi

if [ $? -ne 0 ]; then
    echo "Error: Backend build failed"
    exit 1
fi

echo "Backend deployed successfully to $BACKEND_LOCATION"
echo ""

# Build frontend
echo "=========================================="
echo "Building frontend..."
echo "=========================================="

# Run frontend build script
"$FRONTEND_BUILD_SCRIPT"

if [ $? -ne 0 ]; then
    echo "Error: Frontend build failed"
    exit 1
fi

echo "Frontend built successfully"
echo ""

# Deploy frontend dist to client location
echo "=========================================="
echo "Deploying frontend to $LOCATION/client..."
echo "=========================================="

FRONTEND_DIST="$PROJECT_ROOT/frontend/dist"
CLIENT_LOCATION="$LOCATION/client"

if [ ! -d "$FRONTEND_DIST" ]; then
    echo "Error: Frontend dist folder not found at $FRONTEND_DIST"
    exit 1
fi

# Remove existing client directory if it exists
if [ -d "$CLIENT_LOCATION" ]; then
    echo "Removing existing client directory..."
    rm -rf "$CLIENT_LOCATION"
fi

# Copy dist contents to client location
echo "Copying frontend dist to $CLIENT_LOCATION..."
mkdir -p "$CLIENT_LOCATION"
cp -r "$FRONTEND_DIST"/* "$CLIENT_LOCATION/"

if [ $? -ne 0 ]; then
    echo "Error: Failed to copy frontend files"
    exit 1
fi

echo "Frontend deployed successfully to $CLIENT_LOCATION"
echo ""

echo "=========================================="
echo "Build and deployment completed successfully!"
echo "=========================================="
echo "Deployment location: $LOCATION"
echo ""
echo "Deployed components:"
echo "  - Backend: $BACKEND_LOCATION"
echo "  - Frontend: $CLIENT_LOCATION"
echo ""

