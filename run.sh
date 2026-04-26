#!/bin/bash
# Sandy's Treedome Lab - Unix/Mac Startup Script

set -e

echo ""
echo "========================================"
echo "Sandy's Treedome Lab - Startup"
echo "========================================"
echo ""

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading .env file..."
    export $(cat .env | grep -v '#' | xargs)
else
    echo "Warning: .env file not found. Copy .env.example to .env and fill in values."
    echo ""
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo ""
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo ""

# Determine mode
if [ "$1" = "prod" ]; then
    echo "Starting in PRODUCTION mode (gunicorn)..."
    echo ""
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
else
    echo "Starting in DEVELOPMENT mode (with auto-reload)..."
    echo "Dashboard: http://localhost:8000/ui"
    echo "API Docs: http://localhost:8000/docs"
    echo ""
    python -m uvicorn main:app --reload
fi
