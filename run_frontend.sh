#!/bin/bash
# Run frontend locally (Vite + React)

set -e

cd "$(dirname "$0")/frontend"

echo "=================================="
echo "Sherlock Homes Frontend (React)"
echo "=================================="

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo "Starting frontend at http://localhost:5173"
echo "Press Ctrl+C to stop"
echo ""

npm run dev
