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

# Select Python (spaCy wheels currently target 3.11/3.12)
PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
    if command -v python3.12 >/dev/null 2>&1; then
        PYTHON_BIN="python3.12"
    elif command -v python3.11 >/dev/null 2>&1; then
        PYTHON_BIN="python3.11"
    else
        PYTHON_BIN="python3"
    fi
fi

PYTHON_MAJOR="$($PYTHON_BIN -c 'import sys; print(sys.version_info.major)')"
PYTHON_MINOR="$($PYTHON_BIN -c 'import sys; print(sys.version_info.minor)')"
if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -lt 11 ] || [ "$PYTHON_MINOR" -gt 12 ]; then
    echo "Python 3.11 or 3.12 is required for dependency wheels (spaCy)."
    echo "Detected: $($PYTHON_BIN --version)"
    echo "Install Python 3.11/3.12 and re-run, or set PYTHON_BIN explicitly."
    exit 1
fi

# Prefer .venv (uv default), fall back to venv if it already exists
VENV_DIR="${VENV_DIR:-}"
if [ -z "$VENV_DIR" ]; then
    if [ -d ".venv" ]; then
        VENV_DIR=".venv"
    elif [ -d "venv" ]; then
        VENV_DIR="venv"
    else
        VENV_DIR=".venv"
    fi
fi

UV_AVAILABLE=0
if command -v uv >/dev/null 2>&1; then
    UV_AVAILABLE=1
fi

# Create/validate venv
VENV_PYTHON="$VENV_DIR/bin/python"
if [ -d "$VENV_DIR" ]; then
    if [ ! -x "$VENV_PYTHON" ]; then
        echo "Existing venv at $VENV_DIR is missing python executable. Remove it and re-run."
        exit 1
    fi
    VENV_MAJOR="$($VENV_PYTHON -c 'import sys; print(sys.version_info.major)')"
    VENV_MINOR="$($VENV_PYTHON -c 'import sys; print(sys.version_info.minor)')"
    if [ "$VENV_MAJOR" -ne 3 ] || [ "$VENV_MINOR" -lt 11 ] || [ "$VENV_MINOR" -gt 12 ]; then
        echo "Existing venv at $VENV_DIR uses unsupported Python ($($VENV_PYTHON --version))."
        echo "Remove $VENV_DIR and re-run with Python 3.11 or 3.12."
        exit 1
    fi
else
    echo "Creating virtual environment at $VENV_DIR with $($PYTHON_BIN --version)..."
    if [ "$UV_AVAILABLE" -eq 1 ]; then
        uv venv "$VENV_DIR" --python "$PYTHON_BIN"
    else
        "$PYTHON_BIN" -m venv "$VENV_DIR"
    fi
fi

echo "Activating virtual environment ($VENV_DIR)..."
source "$VENV_DIR/bin/activate"

# Install dependencies if needed
REQ_FILE="requirements.txt"
REQ_HASH=""
if [ -f "$REQ_FILE" ]; then
    REQ_HASH="$($PYTHON_BIN - <<'PY'
import hashlib
from pathlib import Path

print(hashlib.sha256(Path("requirements.txt").read_bytes()).hexdigest())
PY
)"
fi

INSTALL_MARKER="$VENV_DIR/.installed"
NEED_INSTALL=0
if [ ! -f "$INSTALL_MARKER" ]; then
    NEED_INSTALL=1
elif [ -n "$REQ_HASH" ]; then
    PREV_HASH="$(cat "$INSTALL_MARKER" 2>/dev/null || true)"
    if [ "$REQ_HASH" != "$PREV_HASH" ]; then
        NEED_INSTALL=1
    fi
fi

if [ "$NEED_INSTALL" -eq 1 ]; then
    echo "Installing dependencies..."
    if [ "$UV_AVAILABLE" -eq 1 ]; then
        echo "Using uv for dependency install."
        uv pip install --python "$VENV_PYTHON" -r requirements.txt
    else
        pip install -r requirements.txt
    fi
    if [ -n "$REQ_HASH" ]; then
        echo "$REQ_HASH" > "$INSTALL_MARKER"
    else
        touch "$INSTALL_MARKER"
    fi
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
