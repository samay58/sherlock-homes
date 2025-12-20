from datetime import datetime
import hashlib
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.listing import PropertyListing
from app.models.listing_event import ListingEvent, ListingSnapshot
from app.services.visual_scoring import compute_photos_hash
from app.services.neighborhoods import resolve_neighborhood


def _normalize_price(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_status(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.strip().lower()


def _hash_text(text: Optional[str]) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _build_snapshot(listing: PropertyListing) -> Dict[str, Any]:
    return {
        "price": _normalize_price(listing.price),
        "listing_status": _normalize_status(listing.listing_status),
        "days_on_market": listing.days_on_market,
        "photos_hash": compute_photos_hash(listing.photos or []),
        "description_hash": _hash_text(listing.description),
    }


def _snapshot_hash(snapshot: Dict[str, Any]) -> str:
    basis = {
        "price": snapshot.get("price"),
        "listing_status": snapshot.get("listing_status"),
        "photos_hash": snapshot.get("photos_hash"),
        "description_hash": snapshot.get("description_hash"),
    }
    encoded = json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _get_latest_snapshot(db: Session, listing_id: int) -> Optional[ListingSnapshot]:
    return (
        db.query(ListingSnapshot)
        .filter(ListingSnapshot.listing_id == listing_id)
        .order_by(ListingSnapshot.created_at.desc())
        .first()
    )


def _build_events(
    listing_id: int,
    old_snapshot: Optional[Dict[str, Any]],
    new_snapshot: Dict[str, Any],
) -> List[ListingEvent]:
    events: List[ListingEvent] = []

    if not old_snapshot:
        events.append(
            ListingEvent(
                listing_id=listing_id,
                event_type="new_listing",
                new_value={
                    "price": new_snapshot.get("price"),
                    "listing_status": new_snapshot.get("listing_status"),
                },
            )
        )
        return events

    old_price = old_snapshot.get("price")
    new_price = new_snapshot.get("price")
    if old_price is not None and new_price is not None and old_price != new_price:
        delta = new_price - old_price
        if delta < 0:
            amount = abs(delta)
            percent = (amount / old_price * 100) if old_price else None
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type="price_drop",
                    old_value={"price": old_price},
                    new_value={"price": new_price},
                    details={"amount": amount, "percent": percent},
                )
            )
        else:
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type="price_increase",
                    old_value={"price": old_price},
                    new_value={"price": new_price},
                    details={"amount": delta},
                )
            )

    old_status = old_snapshot.get("listing_status")
    new_status = new_snapshot.get("listing_status")
    if old_status != new_status and new_status:
        if new_status == "active" and old_status in {"pending", "contingent", "sold"}:
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type="back_on_market",
                    old_value={"listing_status": old_status},
                    new_value={"listing_status": new_status},
                )
            )
        else:
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type="status_change",
                    old_value={"listing_status": old_status},
                    new_value={"listing_status": new_status},
                )
            )

    old_photos = old_snapshot.get("photos_hash")
    new_photos = new_snapshot.get("photos_hash")
    if old_photos and new_photos and old_photos != new_photos:
        events.append(
            ListingEvent(
                listing_id=listing_id,
                event_type="photo_change",
                old_value={"photos_hash": old_photos},
                new_value={"photos_hash": new_photos},
            )
        )

    old_desc = old_snapshot.get("description_hash")
    new_desc = new_snapshot.get("description_hash")
    if old_desc and new_desc and old_desc != new_desc:
        events.append(
            ListingEvent(
                listing_id=listing_id,
                event_type="description_change",
                old_value={"description_hash": old_desc},
                new_value={"description_hash": new_desc},
            )
        )

    return events


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

                old_snapshot = _get_latest_snapshot(db, existing.id) if existing else None
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
                        elif k == "photos":
                            if v:
                                setattr(existing, k, v)
                        else:
                            setattr(existing, k, v)
                    existing.last_updated = datetime.utcnow()
                    listing = existing
                else:
                    # Prepare attributes with valid flags
                    record_attrs = {k: v for k, v in data.items() if k != "flags"}
                    for fk, fv in flags.items():
                        if fk in valid_flags:
                            record_attrs[valid_flags[fk]] = fv
                    
                    new_record = PropertyListing(**record_attrs)
                    db.add(new_record)
                    db.flush()
                    listing = new_record

                if listing.neighborhood is None:
                    normalized = resolve_neighborhood(None, listing.lat, listing.lon)
                    if normalized:
                        listing.neighborhood = normalized

                snapshot_data = _build_snapshot(listing)
                snapshot_hash = _snapshot_hash(snapshot_data)
                if not old_snapshot or old_snapshot.snapshot_hash != snapshot_hash:
                    db.add(
                        ListingSnapshot(
                            listing_id=listing.id,
                            snapshot_hash=snapshot_hash,
                            snapshot_data=snapshot_data,
                        )
                    )
                    events = _build_events(
                        listing_id=listing.id,
                        old_snapshot=old_snapshot.snapshot_data if old_snapshot else None,
                        new_snapshot=snapshot_data,
                    )
                    for event in events:
                        db.add(event)
                
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
