#!/usr/bin/env bash
# ==============================================================================
# Techonomy Frontend LAN Deployment Startup Script
# ==============================================================================
set -e

# Resolve repository root and frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

cd "${FRONTEND_DIR}"

echo "=================================================="
echo "Starting Techonomy Frontend Server for Event Deployment..."
echo "Directory: ${FRONTEND_DIR}"
echo "=================================================="

# Check for .env file
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found in ${FRONTEND_DIR}!"
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
    fi
fi

# Ensure VITE_API_BASE_URL is printed for user verification
if [ -f ".env" ]; then
    echo "Current Frontend Environment Configuration:"
    cat .env
else
    echo "VITE_API_BASE_URL not set in .env (Defaulting to http://127.0.0.1:8000)"
fi

echo "=================================================="
echo "Launching Vite dev server exposed to LAN (0.0.0.0:3000)..."
echo "Press Ctrl+C to stop."
echo "=================================================="

exec npm run dev -- --host 0.0.0.0 --port 3000
