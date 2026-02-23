import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.criteria import Criteria
from app.models.listing import PropertyListing
from app.services.criteria_config import (load_buyer_criteria,
                                          get_required_neighborhoods)
from app.models.listing_event import ListingEvent
from app.schemas.listing_event import ListingEvent as ListingEventSchema
from app.schemas.listing_event import \
    ListingEventFeed as ListingEventFeedSchema
from app.schemas.property import PropertyListing as PropertyListingSchema
from app.services.advanced_matching import (PropertyMatcher,
                                            find_advanced_matches)
from app.services.criteria import TEST_USER_ID, get_or_create_user_criteria
from app.services.weight_learning import get_effective_weights_dict
from app.state import ingestion_state

router = APIRouter(tags=["listings"])

logger = logging.getLogger(__name__)

# --- Listings Endpoints ---


@router.get("/listings", response_model=List[PropertyListingSchema])
def read_listings(
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    apply_hard_filters: bool = Query(
        default=False,
        description="When true, apply buyer hard filters from BUYER_CRITERIA_PATH",
    ),
):
    """Retrieve a paginated list of property listings."""
    query = select(PropertyListing)
    if apply_hard_filters:
        config = load_buyer_criteria()
        hard = config.hard_filters
        filters = []

        beds_min = hard.get("bedrooms_min")
        if beds_min is not None:
            filters.append(PropertyListing.beds >= beds_min)

        baths_min = hard.get("bathrooms_min")
        if baths_min is not None:
            filters.append(PropertyListing.baths >= baths_min)

        price_max = hard.get("price_max")
        if price_max is not None:
            filters.append(PropertyListing.price <= price_max)

        sqft_min = hard.get("sqft_min")
        if sqft_min is not None:
            filters.append(PropertyListing.sqft >= sqft_min)

        neighborhoods = get_required_neighborhoods(config)
        if neighborhoods:
            filters.append(PropertyListing.neighborhood.in_(neighborhoods))

        if filters:
            query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit).order_by(PropertyListing.id)
    listings = db.scalars(query).all()
    return list(listings)


@router.get("/listings/{listing_id}", response_model=PropertyListingSchema)
def read_listing(listing_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a single property listing by its database ID."""
    # Note: This uses the internal DB ID. Could also lookup by listing_id (ZPID) if needed.
    db_listing = db.get(PropertyListing, listing_id)
    if db_listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )
    matcher = PropertyMatcher(criteria=None, db=db, include_intelligence=True)
    if not matcher.score_listing(db_listing):
        db_listing.match_narrative = "Does not meet hard filters for this buyer."
    return db_listing


# --- Matching Endpoint (for Test User) ---


@router.get("/matches/user/{user_id}", response_model=List[PropertyListingSchema])
def read_matches_for_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieve property listings matching the active criteria for a specific user."""
    # TODO: Later, protect this and get user_id from authenticated user
    try:
        user_criteria = get_or_create_user_criteria(db=db, user_id=user_id, commit_changes=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving criteria",
        )

    if not user_criteria:
        # This case might be handled by get_or_create, but added defensively
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active criteria found for user",
        )

    try:
        user_weights = get_effective_weights_dict(user_id, db)

        match_data = find_advanced_matches(
            criteria=user_criteria,
            db=db,
            limit=100,
            min_score=0.0,
            vibe_preset=None,
            include_intelligence=True,
            user_weights=user_weights,
        )

        matches = [result["listing"] for result in match_data["results"]]
        return matches
    except Exception as exc:
        logger.error("Error in find_matches: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error finding matches",
        )


# Convenience endpoint for test user
@router.get("/matches/test-user", response_model=List[PropertyListingSchema])
def read_matches_for_test_user(db: Session = Depends(get_db)):
    return read_matches_for_user(user_id=TEST_USER_ID, db=db)


# --- Ingestion Status Endpoint ---


@router.get("/ingestion/status", response_model=Dict[str, Any])
def get_ingestion_status():
    """Get the current status of data ingestion including last update time."""
    now = datetime.now(timezone.utc)

    def ensure_aware(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    status_info = {
        "last_run_start_time": ensure_aware(ingestion_state.last_run_start_time),
        "last_run_end_time": ensure_aware(ingestion_state.last_run_end_time),
        "last_run_summary_count": ingestion_state.last_run_summary_count,
        "last_run_detail_calls": ingestion_state.last_run_detail_calls,
        "last_run_upsert_count": ingestion_state.last_run_upsert_count,
        "last_run_error": ingestion_state.last_run_error,
        "status": "never_run",
    }

    if status_info["last_run_end_time"]:
        time_since_update = now - status_info["last_run_end_time"]
        hours_ago = time_since_update.total_seconds() / 3600

        status_info["hours_since_update"] = round(hours_ago, 1)
        status_info["status"] = (
            "up_to_date" if hours_ago < 6 else "stale" if hours_ago < 24 else "outdated"
        )
        status_info["last_update_display"] = (
            f"{round(hours_ago, 1)} hours ago"
            if hours_ago < 24
            else f"{round(hours_ago / 24, 1)} days ago"
        )

    return status_info


@router.get("/listings/{listing_id}/history", response_model=List[ListingEventSchema])
def read_listing_history(
    listing_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
):
    """Retrieve change history for a single listing."""
    listing = db.get(PropertyListing, listing_id)
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )

    query = (
        select(ListingEvent)
        .where(ListingEvent.listing_id == listing_id)
        .order_by(ListingEvent.created_at.desc())
        .limit(limit)
    )
    events = db.scalars(query).all()
    return list(events)


@router.get("/changes", response_model=List[ListingEventFeedSchema])
def read_recent_changes(
    db: Session = Depends(get_db),
    since: Optional[datetime] = Query(default=None),
    event_types: Optional[str] = Query(
        default=None, description="Comma-separated event types"
    ),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Retrieve recent listing changes across the catalog."""
    query = (
        select(
            ListingEvent,
            PropertyListing.address,
            PropertyListing.price,
            PropertyListing.url,
        )
        .join(PropertyListing, PropertyListing.id == ListingEvent.listing_id)
        .order_by(ListingEvent.created_at.desc())
        .limit(limit)
    )

    if since:
        query = query.where(ListingEvent.created_at >= since)

    if event_types:
        types = [item.strip() for item in event_types.split(",") if item.strip()]
        if types:
            query = query.where(ListingEvent.event_type.in_(types))

    rows = db.execute(query).all()
    response: List[ListingEventFeedSchema] = []
    for event, address, price, url in rows:
        response.append(
            ListingEventFeedSchema(
                id=event.id,
                listing_id=event.listing_id,
                event_type=event.event_type,
                old_value=event.old_value,
                new_value=event.new_value,
                details=event.details,
                created_at=event.created_at,
                address=address,
                price=price,
                url=url,
            )
        )
    return response
