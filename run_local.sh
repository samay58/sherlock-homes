#!/bin/bash
# Run Sherlock Homes API locally without Docker
# Uses SQLite database for fast iteration

set -e

# Ensure we're in project root
cd "$(dirname "$0")"

echo "=================================="
echo "Sherlock Homes Local Development"
echo "=================================="

# Use local env if it exists
if [ -f .env.local ]; then
    echo "Loading .env.local..."
    set -a
    source .env.local
    set +a
fi

# Create/activate venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
    touch venv/.installed
fi

# Show database info
if [[ "$DATABASE_URL" == sqlite* ]]; then
    echo "Database: SQLite (sherlock.db)"
else
    echo "Database: $DATABASE_URL"
fi

echo ""
echo "Starting API at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Run API with hot reload
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
