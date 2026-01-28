"""Scout service for automated property discovery and alerting."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.criteria import Criteria
from app.models.listing import PropertyListing
from app.models.scout import Scout, ScoutRun
from app.services.advanced_matching import PropertyMatcher
from app.services.alerts import send_scout_alerts
from app.services.neighborhoods import normalize_neighborhood_name
from app.services.nlp import calculate_text_quality_score, extract_flags

logger = logging.getLogger(__name__)


class ScoutService:
    """Manages scout operations for automated property discovery."""

    def __init__(self, db: Session):
        self.db = db

    def create_scout(
        self,
        user_id: int,
        name: str,
        description: str,
        criteria_id: Optional[int] = None,
        **kwargs,
    ) -> Scout:
        """Create a new scout configuration."""
        scout = Scout(
            user_id=user_id,
            name=name,
            description=description,
            criteria_id=criteria_id,
            **kwargs,
        )
        self.db.add(scout)
        self.db.commit()
        self.db.refresh(scout)
        logger.info(f"Created scout '{name}' for user {user_id}")
        return scout

    def create_scout_from_description(
        self, user_id: int, name: str, description: str
    ) -> Scout:
        """
        Create a scout and auto-generate criteria from natural language description.
        This uses the sophisticated Scout description to create matching criteria.
        """
        # Parse the description to extract criteria
        criteria = self._parse_scout_description(description, user_id)

        # Create the scout with the parsed criteria
        scout = Scout(
            user_id=user_id,
            name=name,
            description=description,
            criteria_id=criteria.id if criteria else None,
            scout_description=description,
            is_active=True,
            alert_frequency="daily",
            min_match_score=60.0,
        )

        self.db.add(scout)
        self.db.commit()
        self.db.refresh(scout)

        logger.info(f"Created scout '{name}' from description for user {user_id}")
        return scout

    def _parse_scout_description(self, description: str, user_id: int) -> Criteria:
        """Parse natural language scout description into criteria."""
        desc_lower = description.lower()

        # Create new criteria based on the description
        criteria = Criteria(
            user_id=user_id, name="Auto-generated from Scout", is_active=True
        )

        # Price parsing
        if (
            "$1,000,000" in description
            or "$1m" in desc_lower
            or "1 million" in desc_lower
        ):
            criteria.price_min = 1000000
        if (
            "$2,000,000" in description
            or "$2m" in desc_lower
            or "2 million" in desc_lower
        ):
            criteria.price_max = 2000000
        if (
            "$3,000,000" in description
            or "$3m" in desc_lower
            or "3 million" in desc_lower
        ):
            criteria.price_max = 3000000

        # Bedroom parsing
        if (
            "3 bedroom" in desc_lower
            or "3 bed" in desc_lower
            or "three bedroom" in desc_lower
        ):
            criteria.beds_min = 3
        if (
            "4 bedroom" in desc_lower
            or "4 bed" in desc_lower
            or "four bedroom" in desc_lower
        ):
            criteria.beds_min = 4

        # Bathroom parsing
        if "2 bath" in desc_lower or "two bath" in desc_lower:
            criteria.baths_min = 2.0
        if "2.5 bath" in desc_lower:
            criteria.baths_min = 2.5

        # Square footage
        if "1,200" in description or "1200 sq" in desc_lower:
            criteria.sqft_min = 1200
        if "1,800" in description or "1800 sq" in desc_lower:
            criteria.sqft_min = 1800
        if "2,500" in description or "2500 sq" in desc_lower:
            criteria.sqft_max = 2500

        # Essential features
        if (
            "natural light" in desc_lower
            or "sun-drenched" in desc_lower
            or "bright" in desc_lower
        ):
            criteria.require_natural_light = True
        if (
            "high ceiling" in desc_lower
            or "vaulted" in desc_lower
            or "10-foot" in desc_lower
        ):
            criteria.require_high_ceilings = True
        if (
            "outdoor" in desc_lower
            or "deck" in desc_lower
            or "patio" in desc_lower
            or "yard" in desc_lower
        ):
            criteria.require_outdoor_space = True
        if "parking" in desc_lower or "garage" in desc_lower:
            criteria.require_parking = True
        if "view" in desc_lower:
            criteria.require_view = True
        if (
            "updated" in desc_lower
            or "modern system" in desc_lower
            or "renovated" in desc_lower
        ):
            criteria.require_updated_systems = True
        if (
            "home office" in desc_lower
            or "workspace" in desc_lower
            or "work from home" in desc_lower
        ):
            criteria.require_home_office = True

        # Walk score
        if "walk score 85" in desc_lower:
            criteria.min_walk_score = 85
        elif "walkable" in desc_lower or "walk score" in desc_lower:
            criteria.min_walk_score = 75

        # Property types
        property_types = []
        if (
            "single-family" in desc_lower
            or "single family" in desc_lower
            or "house" in desc_lower
        ):
            property_types.append("single_family")
        if "condo" in desc_lower or "condominium" in desc_lower:
            property_types.append("condo")
        if "townhouse" in desc_lower or "townhome" in desc_lower:
            property_types.append("townhouse")
        if "loft" in desc_lower:
            property_types.append("loft")
        if property_types:
            criteria.property_types = property_types

        # Neighborhoods
        sf_neighborhoods = [
            "pacific heights",
            "presidio heights",
            "nob hill",
            "russian hill",
            "marina",
            "cow hollow",
            "hayes valley",
            "noe valley",
            "castro",
            "mission",
            "potrero hill",
            "potrero",
            "dogpatch",
            "soma",
            "south beach",
            "richmond",
            "sunset",
            "cole valley",
            "haight",
            "haight-ashbury",
            "japantown",
            "western addition",
            "bernal heights",
            "glen park",
            "dolores heights",
            "nopa",
            "no pa",
            "north of panhandle",
        ]

        preferred = []
        for neighborhood in sf_neighborhoods:
            if neighborhood in desc_lower:
                canonical = normalize_neighborhood_name(neighborhood)
                if canonical:
                    preferred.append(canonical)
        if preferred:
            criteria.preferred_neighborhoods = preferred
            criteria.neighborhood_mode = "strict"

        # Avoid certain streets
        if (
            "van ness" in desc_lower
            or "geary" in desc_lower
            or "19th ave" in desc_lower
        ):
            criteria.excluded_streets = ["Van Ness", "Geary", "19th Ave"]

        # Red flags
        if "busy street" in desc_lower:
            criteria.avoid_busy_streets = True
        if "north facing" in desc_lower or "north-facing" in desc_lower:
            criteria.avoid_north_facing_only = True
        if "basement" in desc_lower or "garden level" in desc_lower:
            criteria.avoid_basement_units = True

        # Feature weights - sophisticated scoring
        weights = {
            "natural_light": 10 if "natural light" in desc_lower else 7,
            "outdoor_space": 9 if "outdoor" in desc_lower else 6,
            "high_ceilings": 8 if "high ceiling" in desc_lower else 5,
            "view": 10 if "view" in desc_lower else 4,
            "parking": 8 if "garage" in desc_lower else 6,
            "updated_systems": 7 if "updated" in desc_lower else 4,
            "walk_score": 9 if "walkable" in desc_lower else 5,
        }
        criteria.feature_weights = weights

        # Save the full scout description
        criteria.scout_description = description

        self.db.add(criteria)
        self.db.commit()
        self.db.refresh(criteria)

        return criteria

    async def run_scout(self, scout_id: int) -> ScoutRun:
        """Execute a scout run to find matching properties."""
        scout = self.db.query(Scout).filter(Scout.id == scout_id).first()
        if not scout:
            raise ValueError(f"Scout {scout_id} not found")

        # Create run record
        run = ScoutRun(
            scout_id=scout_id, started_at=datetime.utcnow(), status="running"
        )
        self.db.add(run)
        self.db.commit()

        try:
            # Get criteria
            criteria = scout.criteria
            if not criteria:
                # Use default criteria if none specified
                criteria = (
                    self.db.query(Criteria)
                    .filter(
                        Criteria.user_id == scout.user_id, Criteria.is_active == True
                    )
                    .first()
                )

            if not criteria:
                raise ValueError("No criteria found for scout")

            # Find matches using advanced matcher
            matcher = PropertyMatcher(criteria, self.db)
            matches = matcher.find_matches(
                limit=100, min_score=scout.min_match_score or 30.0
            )
            run.listings_evaluated = len(matches)

            # Filter out previously seen listings
            seen_ids = set(scout.seen_listing_ids or [])
            new_matches = []
            all_matches = []

            for match in matches:
                if not isinstance(match, (list, tuple)) or len(match) < 2:
                    continue
                listing = match[0]
                score = match[1]
                intelligence = (
                    match[2] if len(match) > 2 and isinstance(match[2], dict) else {}
                )
                match_data = {
                    "listing_id": listing.listing_id,
                    "score": score,
                    "url": listing.url,
                    "address": listing.address,
                    "price": listing.price,
                }
                if intelligence.get("narrative"):
                    match_data["narrative"] = intelligence["narrative"]
                all_matches.append(match_data)

                if listing.listing_id not in seen_ids:
                    new_matches.append(match_data)
                    seen_ids.add(listing.listing_id)

            # Update scout with seen listings
            scout.seen_listing_ids = list(seen_ids)
            scout.last_run = datetime.utcnow()
            scout.total_matches_found += len(new_matches)

            # Update run record
            run.completed_at = datetime.utcnow()
            run.status = "completed"
            run.matches_found = len(all_matches)
            run.new_matches = len(new_matches)
            run.matched_listings = new_matches[: scout.max_results_per_alert]

            if all_matches:
                scores = [m["score"] for m in all_matches]
                run.top_score = max(scores)
                run.average_score = sum(scores) / len(scores)

            # Send alerts if new matches found
            if new_matches and scout.is_active:
                await self._send_alerts(
                    scout, new_matches[: scout.max_results_per_alert]
                )
                run.alerts_sent = 1
                scout.last_alert_sent = datetime.utcnow()
                scout.total_alerts_sent += 1

            self.db.commit()
            logger.info(f"Scout run completed: {len(new_matches)} new matches found")

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self.db.commit()
            logger.error(f"Scout run failed: {e}")
            raise

        return run

    async def _send_alerts(self, scout: Scout, matches: List[Dict[str, Any]]):
        """Send alerts for new matches."""
        results = await send_scout_alerts(scout, matches)
        if results:
            logger.info("Scout alert results: %s", results)

    def get_active_scouts(self) -> List[Scout]:
        """Get all active scouts that need to run."""
        return self.db.query(Scout).filter(Scout.is_active == True).all()

    def should_run_scout(self, scout: Scout) -> bool:
        """Check if a scout should run based on its frequency."""
        if not scout.last_run:
            return True

        now = datetime.utcnow()
        time_since_last = now - scout.last_run

        if scout.alert_frequency == "instant":
            # Run every hour for "instant" alerts
            return time_since_last > timedelta(hours=1)
        elif scout.alert_frequency == "daily":
            return time_since_last > timedelta(days=1)
        elif scout.alert_frequency == "weekly":
            return time_since_last > timedelta(days=7)

        return False

    def record_feedback(self, scout_id: int, listing_id: str, is_positive: bool):
        """Record user feedback on a listing for scout learning."""
        scout = self.db.query(Scout).filter(Scout.id == scout_id).first()
        if not scout:
            return

        if is_positive:
            positive = scout.positive_feedback_listings or []
            if listing_id not in positive:
                positive.append(listing_id)
                scout.positive_feedback_listings = positive
        else:
            negative = scout.negative_feedback_listings or []
            if listing_id not in negative:
                negative.append(listing_id)
                scout.negative_feedback_listings = negative

        self.db.commit()
        logger.info(
            f"Recorded {'positive' if is_positive else 'negative'} feedback for listing {listing_id}"
        )


async def run_all_scouts(db: Session):
    """Run all active scouts that are due."""
    service = ScoutService(db)
    scouts = service.get_active_scouts()

    for scout in scouts:
        if service.should_run_scout(scout):
            try:
                await service.run_scout(scout.id)
            except Exception as e:
                logger.error(f"Failed to run scout {scout.id}: {e}")
