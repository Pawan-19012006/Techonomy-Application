#!/usr/bin/env bash
# ==============================================================================
# Techonomy Backend LAN Deployment Startup Script
# ==============================================================================
set -e

# Resolve backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${BACKEND_DIR}"

echo "=================================================="
echo "Starting Techonomy Backend Server for Event Deployment..."
echo "Directory: ${BACKEND_DIR}"
echo "=================================================="

# Check for .env file
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found in ${BACKEND_DIR}!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please configure .env with valid DATABASE_URL and API keys before running in production."
fi

# Activate virtual environment if present
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
fi

# Determine Host and Port from environment or defaults
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "Launching Uvicorn web server..."
echo "Listening on: http://${HOST}:${PORT}"
echo "Press Ctrl+C to stop."
echo "=================================================="

exec python3 -m uvicorn app.main:app --host "${HOST}" --port "${PORT}"
