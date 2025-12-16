#!/bin/bash
# Run frontend locally

set -e

cd "$(dirname "$0")/frontend"

echo "=================================="
echo "Sherlock Homes Frontend"
echo "=================================="

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    yarn install
fi

echo "Starting frontend at http://localhost:5173"
echo "Press Ctrl+C to stop"
echo ""

yarn dev
