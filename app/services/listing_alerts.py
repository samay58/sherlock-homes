"""Listing alert evaluation based on events and buyer criteria."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.listing import PropertyListing
from app.models.listing_event import ListingEvent
from app.services.advanced_matching import PropertyMatcher
from app.services.alerts import send_listing_alerts
from app.services.criteria_config import load_buyer_criteria


def _event_details(event: ListingEvent) -> Dict[str, Any]:
    if event.details is None:
        event.details = {}
    return event.details


def _build_alert_payload(listing: PropertyListing, reason: str) -> Dict[str, Any]:
    return {
        "listing_id": listing.id,
        "address": listing.address,
        "price": listing.price,
        "url": listing.url,
        "score_percent": listing.match_score,
        "score_points": listing.score_points,
        "tier": listing.score_tier,
        "top_positives": listing.top_positives,
        "tradeoff": listing.key_tradeoff,
        "why_now": listing.why_now,
        "reason": reason,
    }


def process_listing_alerts(since: Optional[datetime] = None) -> Dict[str, int]:
    criteria = load_buyer_criteria()
    alerts_cfg = criteria.alerts or {}

    immediate_threshold = (alerts_cfg.get("new_listing") or {}).get(
        "score_threshold", 76
    )
    price_drop_threshold = (alerts_cfg.get("price_drop") or {}).get(
        "percent_threshold", 5
    )
    digest_drop_threshold = 3
    dom_threshold = (alerts_cfg.get("dom_stale") or {}).get("days", 45)

    since_time = since or datetime.now(timezone.utc) - timedelta(hours=24)

    db: Session = SessionLocal()
    try:
        matcher = PropertyMatcher(criteria=None, db=db)
        events = (
            db.query(ListingEvent)
            .filter(ListingEvent.created_at >= since_time)
            .order_by(ListingEvent.created_at.desc())
            .all()
        )

        immediate_alerts: List[Dict[str, Any]] = []
        digest_alerts: List[Dict[str, Any]] = []

        for event in events:
            listing = db.get(PropertyListing, event.listing_id)
            if not listing:
                continue

            details = _event_details(event)

            if event.event_type == "new_listing":
                if details.get("alerted_immediate"):
                    continue
                scored = matcher.score_listing(
                    listing, min_score_percent=immediate_threshold
                )
                if not scored:
                    continue
                immediate_alerts.append(_build_alert_payload(listing, "New listing"))
                details["alerted_immediate"] = True

            elif event.event_type == "price_drop":
                percent = (details or {}).get("percent")
                if percent is None:
                    continue
                scored = matcher.score_listing(listing)
                if not scored:
                    continue
                if percent >= price_drop_threshold and not details.get(
                    "alerted_immediate"
                ):
                    immediate_alerts.append(
                        _build_alert_payload(listing, f"Price drop {percent:.0f}%")
                    )
                    details["alerted_immediate"] = True
                elif percent >= digest_drop_threshold and not details.get(
                    "alerted_digest"
                ):
                    digest_alerts.append(
                        _build_alert_payload(listing, f"Price drop {percent:.0f}%")
                    )
                    details["alerted_digest"] = True

            elif event.event_type == "back_on_market":
                if details.get("alerted_immediate"):
                    continue
                scored = matcher.score_listing(listing)
                if not scored:
                    continue
                immediate_alerts.append(_build_alert_payload(listing, "Back on market"))
                details["alerted_immediate"] = True

        # DOM stale digest
        if dom_threshold:
            stale_listings = (
                db.query(PropertyListing)
                .filter(PropertyListing.days_on_market >= dom_threshold)
                .all()
            )
            for listing in stale_listings:
                existing = (
                    db.query(ListingEvent)
                    .filter(
                        ListingEvent.listing_id == listing.id,
                        ListingEvent.event_type == "dom_stale",
                    )
                    .first()
                )
                if existing:
                    continue
                scored = matcher.score_listing(listing)
                if not scored:
                    continue
                dom_event = ListingEvent(
                    listing_id=listing.id,
                    event_type="dom_stale",
                    details={"days_on_market": listing.days_on_market},
                )
                db.add(dom_event)
                digest_alerts.append(
                    _build_alert_payload(listing, f"DOM {listing.days_on_market}")
                )

        if immediate_alerts:
            db.commit()
            send_listing_alerts("immediate", immediate_alerts)
        if digest_alerts:
            db.commit()
            send_listing_alerts("digest", digest_alerts)

        if not immediate_alerts and not digest_alerts:
            db.commit()

        return {
            "immediate": len(immediate_alerts),
            "digest": len(digest_alerts),
        }
    finally:
        db.close()
