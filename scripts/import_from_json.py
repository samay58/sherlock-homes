"""
Import data from JSON export into SQLite.

Usage:
    python scripts/import_from_json.py

Looks for `.local/data_export.json` first, then falls back to `data_export.json`
in the project root for backwards compatibility.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models import Base, User, Criteria, PropertyListing, Scout, ScoutRun


def parse_datetime(value):
    """Parse ISO datetime string to datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Handle various ISO formats
        try:
            # Remove Z suffix and handle timezone
            cleaned = value.replace("Z", "+00:00")
            # Handle microseconds with different precision
            if "." in cleaned:
                # Truncate microseconds to 6 digits
                parts = cleaned.split(".")
                if "+" in parts[1]:
                    micro, tz = parts[1].split("+")
                    parts[1] = micro[:6] + "+" + tz
                elif "-" in parts[1]:
                    micro, tz = parts[1].split("-")
                    parts[1] = micro[:6] + "-" + tz
                else:
                    parts[1] = parts[1][:6]
                cleaned = ".".join(parts)
            return datetime.fromisoformat(cleaned)
        except ValueError:
            # Fallback to basic ISO parsing
            return datetime.fromisoformat(value.replace("Z", ""))
    return value


def _resolve_data_export_path() -> Path:
    project_root = Path(__file__).parent.parent
    preferred = project_root / ".local" / "data_export.json"
    legacy = project_root / "data_export.json"

    if preferred.exists():
        return preferred
    return legacy


def import_all():
    """Import all tables from JSON file."""
    data_path = _resolve_data_export_path()

    if not data_path.exists():
        print(f"ERROR: {data_path} not found")
        print("Run the export script first:")
        print("  docker compose exec api python scripts/export_to_json.py")
        print("  mkdir -p .local")
        print("  docker cp sherlock-api:/code/.local/data_export.json ./.local/data_export.json")
        print("  # Legacy path (older versions):")
        print("  docker cp sherlock-api:/code/data_export.json ./data_export.json")
        sys.exit(1)

    # Create tables first
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    with open(data_path, "r") as f:
        data = json.load(f)

    db = SessionLocal()

    # Define import order (respecting foreign key constraints)
    models = [
        ("users", User),
        ("criteria", Criteria),
        ("property_listings", PropertyListing),
        ("scouts", Scout),
        ("scout_runs", ScoutRun),
    ]

    print("=" * 50)
    print("IMPORTING DATA")
    print("=" * 50)

    try:
        for table_name, model in models:
            rows = data.get(table_name, [])
            imported = 0

            for row in rows:
                # Parse datetime fields
                for key, value in row.items():
                    if key.endswith("_at") or key.endswith("_date") or key == "last_updated":
                        row[key] = parse_datetime(value)

                try:
                    obj = model(**row)
                    db.merge(obj)  # merge handles existing records
                    imported += 1
                except Exception as e:
                    print(f"  Warning: Could not import {table_name} row: {e}")

            db.commit()
            print(f"{table_name}: {imported} records imported")

        print("=" * 50)
        print("IMPORT COMPLETE")
        print("=" * 50)

    except Exception as e:
        print(f"Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_all()
