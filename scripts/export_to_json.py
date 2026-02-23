"""
Export all tables to JSON for SQLite import.

Run this while Docker is still up:
    docker compose exec api python scripts/export_to_json.py
    mkdir -p .local
    docker cp sherlock-api:/code/.local/data_export.json ./.local/data_export.json

Legacy (older versions):
    docker cp sherlock-api:/code/data_export.json ./data_export.json
"""
import json
import sys
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import User, Criteria, PropertyListing, Scout, ScoutRun


def json_serializer(obj):
    """Handle non-JSON-serializable types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def row_to_dict(row) -> dict:
    """Convert SQLAlchemy row to dict, removing internal state and relationships."""
    from sqlalchemy.orm import RelationshipProperty
    from sqlalchemy import inspect

    d = {}
    mapper = inspect(row.__class__)

    # Only include actual columns, not relationships
    column_names = {c.key for c in mapper.columns}

    for key in column_names:
        if hasattr(row, key):
            d[key] = getattr(row, key)

    return d


def export_all():
    """Export all tables to JSON file."""
    db = SessionLocal()

    try:
        # Collect all data
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "users": [row_to_dict(row) for row in db.query(User).all()],
            "criteria": [row_to_dict(row) for row in db.query(Criteria).all()],
            "property_listings": [row_to_dict(row) for row in db.query(PropertyListing).all()],
            "scouts": [row_to_dict(row) for row in db.query(Scout).all()],
            "scout_runs": [row_to_dict(row) for row in db.query(ScoutRun).all()],
        }

        # Write to file
        project_root = Path(__file__).parent.parent
        output_path = project_root / ".local" / "data_export.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=json_serializer)

        # Print summary
        print("=" * 50)
        print("EXPORT COMPLETE")
        print("=" * 50)
        print(f"Users:            {len(data['users'])}")
        print(f"Criteria:         {len(data['criteria'])}")
        print(f"Property Listings: {len(data['property_listings'])}")
        print(f"Scouts:           {len(data['scouts'])}")
        print(f"Scout Runs:       {len(data['scout_runs'])}")
        print(f"\nOutput: {output_path}")

    finally:
        db.close()


if __name__ == "__main__":
    export_all()
