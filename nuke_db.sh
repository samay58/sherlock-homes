#!/bin/bash
# Reset SQLite database (nuke and pave)
# Use this when you need a fresh database after model changes

set -e

cd "$(dirname "$0")"

echo "=================================="
echo "Database Reset (Nuke and Pave)"
echo "=================================="

delete_sqlite_family() {
    local base="$1"

    if [ -f "$base" ] || [ -f "${base}-journal" ] || [ -f "${base}-shm" ] || [ -f "${base}-wal" ]; then
        echo "Deleting $base..."
        rm -f "$base" "${base}-journal" "${base}-shm" "${base}-wal"
        return 0
    fi
    return 1
}

found_any=0

# Preferred local path (keeps repo root clean)
if delete_sqlite_family ".local/sherlock.db"; then found_any=1; fi

# Legacy root path
if delete_sqlite_family "sherlock.db"; then found_any=1; fi

# Legacy names from older iterations
if delete_sqlite_family ".local/homehog.db"; then found_any=1; fi
if delete_sqlite_family "homehog.db"; then found_any=1; fi

if [ "$found_any" -eq 0 ]; then
    echo "No SQLite database files found."
else
    echo "Database deleted."
fi

echo ""
echo "Database will be recreated on next app startup."
echo ""
echo "Next steps:"
echo "  1. ./run_local.sh          # Start API (creates tables)"
echo "  2. python scripts/import_from_json.py  # Optional: restore data (.local/data_export.json)"
