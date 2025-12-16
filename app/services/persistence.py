from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.listing import PropertyListing


def upsert_listings(listings: List[Dict[str, Any]]):
    """Insert or update listing records in the database.

    Notes:
    - Uses provider `listing_id` when present; falls back to URL.
    - Applies extracted `flags` to boolean keyword columns.
    - Avoids mutating `photos` when merging (kept as JSON list on model).
    """
    db: Session = SessionLocal()
    upserted_count = 0
    try:
        for data in listings:
            if not data.get("address"):
                continue

            try:
                identifier_filter: Dict[str, Any] = {}
                if data.get("listing_id"):
                    identifier_filter["listing_id"] = data["listing_id"]
                else:
                    identifier_filter["url"] = data["url"]

                existing: Optional[PropertyListing] = (
                    db.query(PropertyListing).filter_by(**identifier_filter).first()
                )

                flags = data.get("flags") or {}
                
                # Map of valid flag names to their corresponding model attributes
                valid_flags = {
                    "natural_light": "has_natural_light_keywords",
                    "high_ceilings": "has_high_ceiling_keywords",
                    "outdoor_space": "has_outdoor_space_keywords",
                    "parking": "has_parking_keywords",
                    "view": "has_view_keywords",
                    "updated_systems": "has_updated_systems_keywords",
                    "home_office": "has_home_office_keywords",
                    "storage": "has_storage_keywords",
                    "open_floor_plan": "has_open_floor_plan_keywords",
                    "architectural_details": "has_architectural_details_keywords",
                    "luxury": "has_luxury_keywords",
                    "designer": "has_designer_keywords",
                    "tech_ready": "has_tech_ready_keywords",
                    "price_reduced": "is_price_reduced",
                    "back_on_market": "is_back_on_market",
                    "busy_street": "has_busy_street_keywords",
                    "foundation_issues": "has_foundation_issues_keywords",
                    "hoa_issues": "has_hoa_issues_keywords",
                    "north_facing_only": "is_north_facing_only",
                    "basement_unit": "is_basement_unit",
                }

                if existing:
                    for k, v in data.items():
                        if k == "flags":
                            for fk, fv in flags.items():
                                if fk in valid_flags:
                                    attr = valid_flags[fk]
                                    setattr(existing, attr, fv)
                        elif k != "photos":
                            setattr(existing, k, v)
                    existing.last_updated = datetime.utcnow()
                else:
                    # Prepare attributes with valid flags
                    record_attrs = {k: v for k, v in data.items() if k != "flags"}
                    for fk, fv in flags.items():
                        if fk in valid_flags:
                            record_attrs[valid_flags[fk]] = fv
                    
                    new_record = PropertyListing(**record_attrs)
                    db.add(new_record)
                
                # Commit after each listing to handle duplicates gracefully
                db.commit()
                upserted_count += 1
                
            except Exception as e:
                db.rollback()
                # Log but continue with next listing
                print(f"Failed to upsert listing {data.get('listing_id', 'unknown')}: {e}")
                continue
                
    finally:
        db.close()
        print(f"Successfully upserted {upserted_count} listings")

