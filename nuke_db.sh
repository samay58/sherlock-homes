#!/bin/bash
# Reset SQLite database (nuke and pave)
# Use this when you need a fresh database after model changes

set -e

cd "$(dirname "$0")"

echo "=================================="
echo "Database Reset (Nuke and Pave)"
echo "=================================="

# Remove old homehog.db if it exists (legacy name)
if [ -f "homehog.db" ]; then
    echo "Removing legacy homehog.db..."
    rm -f homehog.db homehog.db-journal homehog.db-shm homehog.db-wal
fi

# Remove sherlock.db
if [ -f "sherlock.db" ]; then
    echo "Deleting sherlock.db..."
    rm -f sherlock.db
    rm -f sherlock.db-journal
    rm -f sherlock.db-shm
    rm -f sherlock.db-wal
    echo "Database deleted."
else
    echo "No database file found (sherlock.db)"
fi

echo ""
echo "Database will be recreated on next app startup."
echo ""
echo "Next steps:"
echo "  1. ./run_local.sh          # Start API (creates tables)"
echo "  2. python scripts/import_from_json.py  # Optional: restore data"
