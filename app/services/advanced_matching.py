"""Buyer-specific matching and scoring engine for Sherlock Homes."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.listing import PropertyListing
from app.models.listing_event import ListingEvent
from app.services.criteria_config import (BuyerCriteria,
                                          get_required_neighborhoods,
                                          load_buyer_criteria)
from app.services.geospatial import (apply_location_modifiers,
                                     calculate_tranquility_score)
from app.services.nlp import (analyze_text_signals, estimate_light_potential,
                              is_generic_description)
from app.services.scoring.primitives import (CENTRAL_HVAC_KEYWORDS,
                                             CRITERION_LABELS,
                                             DISHWASHER_KEYWORDS,
                                             GAS_STOVE_KEYWORDS,
                                             INDOOR_OUTDOOR_KEYWORDS,
                                             LAUNDRY_BUILDING_KEYWORDS,
                                             LAUNDRY_KEYWORDS, LAYOUT_KEYWORDS,
                                             LAYOUT_NEGATIVE_KEYWORDS,
                                             NO_PARKING_KEYWORDS,
                                             OFFICE_KEYWORDS,
                                             PARKING_STREET_ONLY_KEYWORDS,
                                             MatchSignals, ScoreComponent,
                                             _blend_scores, _find_hits,
                                             _hoa_penalty, _score_from_hits,
                                             _score_percent, _score_tier,
                                             _soft_cap_penalty)
from app.services.text_intelligence import \
    enrich_listings_with_text_intelligence

logger = logging.getLogger(__name__)

TOTAL_POINTS = 126


def _build_why_now(listing: PropertyListing, db: Session) -> Optional[str]:
    if listing.is_price_reduced and listing.price_reduction_amount:
        if listing.price:
            percent = (
                listing.price_reduction_amount
                / (listing.price + listing.price_reduction_amount)
            ) * 100
            return f"Price dropped {percent:.0f}% recently"
        return "Price dropped recently"

    recent_event = (
        db.query(ListingEvent)
        .filter(ListingEvent.listing_id == listing.id)
        .order_by(ListingEvent.created_at.desc())
        .first()
    )
    if recent_event:
        if recent_event.event_type == "price_drop":
            details = recent_event.details or {}
            percent = details.get("percent")
            if percent:
                return f"Price dropped {percent:.0f}% recently"
            return "Price dropped recently"
        if recent_event.event_type == "back_on_market":
            return "Back on market"

    if listing.days_on_market is not None:
        if listing.days_on_market <= 7:
            return f"New listing ({listing.days_on_market} DOM)"
        if listing.days_on_market >= 45:
            return f"Overlooked at {listing.days_on_market} DOM"
    return None


class PropertyMatcher:
    """Buyer-specific matcher using YAML criteria and weighted scoring."""

    def __init__(
        self,
        criteria: Optional[Any],
        db: Session,
        include_intelligence: bool = True,
        user_weights: Optional[Dict[str, float]] = None,
    ):
        self.criteria = criteria
        self.db = db
        self.include_intelligence = include_intelligence
        self.config: BuyerCriteria = load_buyer_criteria()
        self.total_analyzed = 0
        # Use provided user weights or fall back to config weights
        self._effective_weights = (
            user_weights if user_weights else dict(self.config.weights)
        )

    def _build_listing_context(
        self, listing: PropertyListing
    ) -> Tuple[str, str, dict, Optional[float]]:
        description = listing.description or ""
        text_lower = description.lower()
        nlp_hits = analyze_text_signals(description, self.config.nlp_signals)

        tranquility_score = listing.tranquility_score
        if (
            tranquility_score is None
            and self.include_intelligence
            and listing.lat
            and listing.lon
        ):
            tranquility_score = calculate_tranquility_score(
                listing.lat, listing.lon
            ).get("score")
            listing.tranquility_score = tranquility_score

        return description, text_lower, nlp_hits, tranquility_score

    def _build_base_query(self):
        query = select(PropertyListing)
        filters = []
        hard = self.config.hard_filters

        price_max = hard.get("price_max")
        if price_max is not None:
            filters.append(PropertyListing.price <= price_max)

        beds_min = hard.get("bedrooms_min")
        if beds_min is not None:
            filters.append(PropertyListing.beds >= beds_min)

        baths_min = hard.get("bathrooms_min")
        if baths_min is not None:
            filters.append(PropertyListing.baths >= baths_min)

        sqft_min = hard.get("sqft_min")
        if sqft_min is not None:
            filters.append(PropertyListing.sqft >= sqft_min)

        neighborhoods = get_required_neighborhoods(self.config)
        if neighborhoods:
            filters.append(PropertyListing.neighborhood.in_(neighborhoods))

        inactive_statuses = [
            "pending",
            "contingent",
            "sold",
            "off market",
            "off_market",
        ]
        status_filters = [
            ~PropertyListing.listing_status.ilike(f"%{status}%")
            for status in inactive_statuses
        ]
        filters.append(
            or_(
                PropertyListing.listing_status.is_(None),
                and_(*status_filters),
            )
        )

        if filters:
            query = query.where(and_(*filters))
        return query

    def _passes_hard_filters(self, listing: PropertyListing) -> Tuple[bool, List[str]]:
        failures: List[str] = []
        hard = self.config.hard_filters

        price_max = hard.get("price_max")
        if price_max is not None:
            if listing.price is None or listing.price > price_max:
                failures.append("price above max")

        beds_min = hard.get("bedrooms_min")
        if beds_min is not None:
            if listing.beds is None or listing.beds < beds_min:
                failures.append("bedrooms below min")

        baths_min = hard.get("bathrooms_min")
        if baths_min is not None:
            if listing.baths is None or listing.baths < baths_min:
                failures.append("bathrooms below min")

        sqft_min = hard.get("sqft_min")
        if sqft_min is not None:
            if listing.sqft is None or listing.sqft < sqft_min:
                failures.append("sqft below min")

        neighborhoods = get_required_neighborhoods(self.config)
        if neighborhoods:
            if not listing.neighborhood or listing.neighborhood not in neighborhoods:
                failures.append("neighborhood excluded")

        status = (listing.listing_status or "").lower()
        inactive_statuses = [
            "pending",
            "contingent",
            "sold",
            "off market",
            "off_market",
        ]
        if status and any(flag in status for flag in inactive_statuses):
            failures.append("inactive status")

        return (len(failures) == 0, failures)

    def _passes_additional_hard_filters(
        self,
        listing: PropertyListing,
        text_lower: str,
        nlp_hits: dict,
        tranquility_score: Optional[float],
    ) -> Tuple[bool, List[str]]:
        failures: List[str] = []

        dark_hits = nlp_hits.get("negative_hits", {}).get("dark")
        if dark_hits and not nlp_hits.get("positive_hits", {}).get("light"):
            failures.append("dark interior signals")

        if listing.has_busy_street_keywords:
            failures.append("busy street signal")
        if tranquility_score is not None and tranquility_score < 40:
            failures.append("low tranquility score")

        layout_negative = _find_hits(text_lower, LAYOUT_NEGATIVE_KEYWORDS)
        if layout_negative:
            failures.append("layout red flags")

        if settings.SEARCH_MODE != "rent":
            no_parking_hits = _find_hits(text_lower, NO_PARKING_KEYWORDS)
            if no_parking_hits:
                failures.append("no parking")

        if settings.SEARCH_MODE == "rent" and listing.is_no_pets:
            failures.append("no pets allowed")

        return (len(failures) == 0, failures)

    def _apply_scorecard(
        self,
        listing: PropertyListing,
        total_points: float,
        components: Dict[str, ScoreComponent],
        signals: MatchSignals,
        total_possible: float,
        score_percent_value: float,
    ) -> None:
        contributions = [
            (key, (comp.score / 10.0) * comp.weight)
            for key, comp in components.items()
            if comp.weight > 0 and comp.score > 0
        ]
        contributions.sort(key=lambda item: item[1], reverse=True)
        top_positives = [CRITERION_LABELS.get(key, key) for key, _ in contributions[:3]]

        tradeoff = None
        price_penalty = _soft_cap_penalty(
            listing.price,
            self.config.soft_caps.get("price_soft"),
            self.config.hard_filters.get("price_max"),
        )
        hoa_penalty = _hoa_penalty(listing.hoa_fee)
        if price_penalty > 0:
            tradeoff = "Above ideal price"
        elif hoa_penalty > 0:
            tradeoff = "High HOA"
        else:
            weighted_components = [
                (key, comp) for key, comp in components.items() if comp.weight > 0
            ]
            if weighted_components:
                lowest = min(weighted_components, key=lambda item: item[1].score)
                tradeoff = f"Low on {CRITERION_LABELS.get(lowest[0], lowest[0])}"

        why_now = _build_why_now(listing, self.db)

        listing.match_score = round(score_percent_value, 1)
        listing.score_points = round(total_points, 1)
        listing.score = listing.score_points
        listing.feature_scores = {
            key: {
                "score": comp.score,
                "weight": comp.weight,
                "evidence": comp.evidence,
                "confidence": comp.confidence,
            }
            for key, comp in components.items()
        }
        listing.match_reasons = top_positives
        listing.match_tradeoff = tradeoff
        listing.score_percent = _score_percent(total_points, total_possible)
        listing.score_tier = _score_tier(score_percent_value)
        listing.top_positives = top_positives
        listing.key_tradeoff = tradeoff
        listing.signals = {
            "tranquility_score": signals.tranquility_score,
            "light_potential": signals.light_potential,
            "visual_quality": signals.visual_quality,
            "nlp_character_score": signals.nlp_character_score,
        }
        listing.why_now = why_now

    def _score_listing(
        self,
        listing: PropertyListing,
        nlp_hits: dict,
        text_lower: str,
    ) -> Tuple[float, Dict[str, ScoreComponent], MatchSignals]:
        description = listing.description or ""

        light_potential_score = listing.light_potential_score
        if light_potential_score is None and self.include_intelligence:
            light_data = estimate_light_potential(
                description=description,
                is_north_facing_only=listing.is_north_facing_only or False,
                is_basement_unit=listing.is_basement_unit or False,
                has_natural_light_keywords=listing.has_natural_light_keywords or False,
                photo_count=len(listing.photos or []),
            )
            light_potential_score = light_data.get("score")

        tranquility_score = listing.tranquility_score
        if (
            tranquility_score is None
            and listing.lat
            and listing.lon
            and self.include_intelligence
        ):
            tranquility = calculate_tranquility_score(listing.lat, listing.lon)
            tranquility_score = tranquility.get("score")

        visual_brightness = None
        if listing.visual_assessment:
            dimensions = listing.visual_assessment.get("dimensions") or {}
            visual_brightness = dimensions.get("brightness")

        weights = self._effective_weights
        components: Dict[str, ScoreComponent] = {}

        def add_component(
            key: str, score: float, evidence: List[str], confidence: str = "medium"
        ):
            weight = float(weights.get(key, 0))
            components[key] = ScoreComponent(
                score=score, weight=weight, evidence=evidence, confidence=confidence
            )

        # Natural light
        light_hits = nlp_hits.get("positive_hits", {}).get("light", [])
        light_base = _score_from_hits(len(light_hits))
        blended = [light_base]
        if light_potential_score is not None:
            blended.append(light_potential_score / 10)
        if visual_brightness is not None:
            blended.append(visual_brightness / 10)
        light_score = _blend_scores(blended)
        light_multiplier = float(
            self.config.nlp_signals.get("positive", {})
            .get("light", {})
            .get("weight", 1.0)
        )
        if light_score:
            light_score = min(10.0, light_score * light_multiplier)
        dark_multiplier = float(
            self.config.nlp_signals.get("negative", {})
            .get("dark", {})
            .get("weight", 1.0)
        )
        if nlp_hits.get("negative_hits", {}).get("dark") and not light_hits:
            light_score = light_score * dark_multiplier
        add_component(
            "natural_light",
            score=round(light_score, 2),
            evidence=[f"mentions '{hit}'" for hit in light_hits[:3]]
            + (
                [f"light potential {light_potential_score}"]
                if light_potential_score is not None
                else []
            )
            + (
                [f"brightness {visual_brightness}"]
                if visual_brightness is not None
                else []
            ),
            confidence=(
                "high" if len(light_hits) >= 2 or light_potential_score else "medium"
            ),
        )

        # Outdoor space
        outdoor_hits = nlp_hits.get("positive_hits", {}).get("outdoor", [])
        outdoor_score = _score_from_hits(len(outdoor_hits))
        if listing.has_outdoor_space_keywords:
            outdoor_score = max(outdoor_score, 7.5)
        outdoor_multiplier = float(
            self.config.nlp_signals.get("positive", {})
            .get("outdoor", {})
            .get("weight", 1.0)
        )
        if outdoor_score:
            outdoor_score = min(10.0, outdoor_score * outdoor_multiplier)
        weak_outdoor_multiplier = float(
            self.config.nlp_signals.get("negative", {})
            .get("weak_outdoor", {})
            .get("weight", 1.0)
        )
        if nlp_hits.get("negative_hits", {}).get("weak_outdoor"):
            outdoor_score = outdoor_score * weak_outdoor_multiplier
        add_component(
            "outdoor_space",
            score=round(outdoor_score, 2),
            evidence=[f"mentions '{hit}'" for hit in outdoor_hits[:3]],
        )

        # Character & soul
        character_hits = nlp_hits.get("positive_hits", {}).get("character", [])
        quality_hits = nlp_hits.get("positive_hits", {}).get("quality", [])
        character_score = _score_from_hits(len(character_hits) + len(quality_hits))
        if listing.has_architectural_details_keywords:
            character_score = max(character_score, 7.0)
        if listing.year_built:
            if listing.year_built <= 1940:
                character_score = min(10.0, character_score + 2.0)
            elif listing.year_built <= 1960:
                character_score = min(10.0, character_score + 1.0)
        character_multiplier = float(
            self.config.nlp_signals.get("positive", {})
            .get("character", {})
            .get("weight", 1.0)
        )
        if character_score:
            character_score = min(10.0, character_score * character_multiplier)
        quality_multiplier = float(
            self.config.nlp_signals.get("positive", {})
            .get("quality", {})
            .get("weight", 1.0)
        )
        if quality_hits and character_score:
            character_score = min(10.0, character_score * quality_multiplier)
        flipper_multiplier = float(
            self.config.nlp_signals.get("negative", {})
            .get("flipper", {})
            .get("weight", 1.0)
        )
        if nlp_hits.get("negative_hits", {}).get("flipper") and is_generic_description(
            description, nlp_hits.get("positive_hits")
        ):
            character_score = character_score * flipper_multiplier
        add_component(
            "character_soul",
            score=round(character_score, 2),
            evidence=[
                f"mentions '{hit}'" for hit in (character_hits + quality_hits)[:3]
            ]
            + ([f"year built {listing.year_built}"] if listing.year_built else []),
        )

        # Kitchen quality
        kitchen_hits = nlp_hits.get("positive_hits", {}).get("kitchen", [])
        kitchen_score = _score_from_hits(len(kitchen_hits))
        kitchen_multiplier = float(
            self.config.nlp_signals.get("positive", {})
            .get("kitchen", {})
            .get("weight", 1.0)
        )
        if kitchen_score:
            kitchen_score = min(10.0, kitchen_score * kitchen_multiplier)
        add_component(
            "kitchen_quality",
            score=round(kitchen_score, 2),
            evidence=[f"mentions '{hit}'" for hit in kitchen_hits[:3]],
        )

        # Location quiet
        quiet_evidence: List[str] = []
        quiet_score = 5.0
        quiet_confidence = "low"
        if tranquility_score is not None:
            quiet_score = min(10.0, tranquility_score / 10)
            quiet_confidence = "high"
            quiet_evidence.append(f"tranquility {tranquility_score}")
        if listing.has_busy_street_keywords:
            quiet_score = max(0.0, quiet_score - 3.0)
            quiet_evidence.append("busy street signal")
        noise_hits = nlp_hits.get("negative_hits", {}).get("location_noise", [])
        if noise_hits:
            noise_multiplier = float(
                self.config.nlp_signals.get("negative", {})
                .get("location_noise", {})
                .get("weight", 1.0)
            )
            quiet_score = quiet_score * noise_multiplier
            quiet_evidence.extend([f"mentions '{hit}'" for hit in noise_hits[:2]])

        modifiers = self.config.location_modifiers or {}
        mod_result = apply_location_modifiers(
            listing.address,
            description,
            modifiers,
            has_busy_street=listing.has_busy_street_keywords,
            noise_hits=noise_hits,
        )
        quiet_score = max(
            0.0, min(10.0, quiet_score + mod_result.get("adjustment", 0.0))
        )
        quiet_evidence.extend(mod_result.get("evidence", []))

        add_component(
            "location_quiet",
            score=round(quiet_score, 2),
            evidence=quiet_evidence,
            confidence=quiet_confidence,
        )

        # Office space
        office_hits = _find_hits(text_lower, OFFICE_KEYWORDS)
        office_score = _score_from_hits(len(office_hits))
        if listing.has_home_office_keywords:
            office_score = max(office_score, 7.0)
        add_component(
            "office_space",
            score=round(office_score, 2),
            evidence=[f"mentions '{hit}'" for hit in office_hits[:3]],
        )

        # Indoor-outdoor flow
        flow_hits = _find_hits(text_lower, INDOOR_OUTDOOR_KEYWORDS)
        flow_score = _score_from_hits(len(flow_hits))
        if (
            flow_score == 0
            and outdoor_score >= 6
            and _find_hits(text_lower, LAYOUT_KEYWORDS)
        ):
            flow_score = 6.5
        add_component(
            "indoor_outdoor_flow",
            score=round(flow_score, 2),
            evidence=[f"mentions '{hit}'" for hit in flow_hits[:2]],
        )

        # High ceilings
        ceiling_score = 0.0
        if listing.has_high_ceiling_keywords:
            ceiling_score = 8.0
        if "10 ft" in text_lower or "10-foot" in text_lower or "11 ft" in text_lower:
            ceiling_score = max(ceiling_score, 9.0)
        add_component(
            "high_ceilings",
            score=round(ceiling_score, 2),
            evidence=["ceiling keywords"] if ceiling_score else [],
        )

        # Layout intelligence
        layout_hits = _find_hits(text_lower, LAYOUT_KEYWORDS)
        layout_score = _score_from_hits(len(layout_hits))
        add_component(
            "layout_intelligence",
            score=round(layout_score, 2),
            evidence=[f"mentions '{hit}'" for hit in layout_hits[:2]],
        )

        # Move-in ready
        move_hits = _find_hits(
            text_lower,
            [
                "move-in ready",
                "move in ready",
                "turn-key",
                "turnkey",
                "updated",
                "renovated",
            ],
        )
        move_score = _score_from_hits(len(move_hits))
        if listing.visual_quality_score:
            move_score = max(move_score, min(10.0, listing.visual_quality_score / 10))
        if nlp_hits.get("negative_hits", {}).get("flipper") and is_generic_description(
            description, nlp_hits.get("positive_hits")
        ):
            move_score = move_score * 0.8
        condition_multiplier = float(
            self.config.nlp_signals.get("negative", {})
            .get("condition", {})
            .get("weight", 1.0)
        )
        if nlp_hits.get("negative_hits", {}).get("condition"):
            move_score = move_score * condition_multiplier
        move_evidence = [f"mentions '{hit}'" for hit in move_hits[:2]]
        if nlp_hits.get("negative_hits", {}).get("condition"):
            move_evidence.append("condition concerns")
        add_component(
            "move_in_ready", score=round(move_score, 2), evidence=move_evidence
        )

        # Views
        view_score = 0.0
        if listing.has_view_keywords:
            view_score = 8.0
        add_component(
            "views",
            score=round(view_score, 2),
            evidence=["view keywords"] if view_score else [],
        )

        # In-unit laundry
        laundry_hits = _find_hits(text_lower, LAUNDRY_KEYWORDS)
        laundry_score = _score_from_hits(len(laundry_hits))
        if not laundry_hits and _find_hits(text_lower, LAUNDRY_BUILDING_KEYWORDS):
            laundry_score = 4.0
        add_component(
            "in_unit_laundry",
            score=round(laundry_score, 2),
            evidence=[f"mentions '{hit}'" for hit in laundry_hits[:2]],
        )

        # Parking
        parking_score = 0.0
        if listing.has_parking_keywords:
            parking_score = 7.0
        if listing.parking_type:
            if listing.parking_type.lower() in {"garage", "carport", "driveway"}:
                parking_score = max(parking_score, 9.0)
        if _find_hits(text_lower, PARKING_STREET_ONLY_KEYWORDS):
            parking_score = max(parking_score, 4.0)
        add_component(
            "parking",
            score=round(parking_score, 2),
            evidence=["parking mention"] if parking_score else [],
        )

        # Central HVAC
        hvac_hits = _find_hits(text_lower, CENTRAL_HVAC_KEYWORDS)
        hvac_score = _score_from_hits(len(hvac_hits))
        add_component(
            "central_hvac",
            score=round(hvac_score, 2),
            evidence=[f"mentions '{hit}'" for hit in hvac_hits[:2]],
        )

        # Gas stove
        gas_hits = _find_hits(text_lower, GAS_STOVE_KEYWORDS)
        gas_score = _score_from_hits(len(gas_hits))
        add_component(
            "gas_stove",
            score=round(gas_score, 2),
            evidence=[f"mentions '{hit}'" for hit in gas_hits[:2]],
        )

        # Dishwasher
        dishwasher_hits = _find_hits(text_lower, DISHWASHER_KEYWORDS)
        dishwasher_score = _score_from_hits(len(dishwasher_hits))
        add_component(
            "dishwasher",
            score=round(dishwasher_score, 2),
            evidence=[f"mentions '{hit}'" for hit in dishwasher_hits[:2]],
        )

        # Storage
        storage_score = 0.0
        if listing.has_storage_keywords:
            storage_score = 8.0
        add_component(
            "storage",
            score=round(storage_score, 2),
            evidence=["storage mention"] if storage_score else [],
        )

        # Pet friendly
        pet_evidence: List[str] = []
        pet_score = 0.0
        pet_hits = nlp_hits.get("positive_hits", {}).get("pet", [])
        if listing.is_pet_friendly:
            pet_score = 10.0
            pet_evidence.append("pet_friendly flag")
        elif pet_hits:
            pet_score = _score_from_hits(len(pet_hits))
            pet_evidence.extend([f"mentions '{hit}'" for hit in pet_hits[:3]])
        pet_multiplier = float(
            self.config.nlp_signals.get("positive", {})
            .get("pet", {})
            .get("weight", 1.0)
        )
        if pet_score:
            pet_score = min(10.0, pet_score * pet_multiplier)
        no_pets_multiplier = float(
            self.config.nlp_signals.get("negative", {})
            .get("no_pets", {})
            .get("weight", 1.0)
        )
        if nlp_hits.get("negative_hits", {}).get("no_pets"):
            pet_score = pet_score * no_pets_multiplier
            pet_evidence.append("no pets signal")
        add_component(
            "pet_friendly",
            score=round(pet_score, 2),
            evidence=pet_evidence,
        )

        # Gym / fitness
        gym_evidence: List[str] = []
        gym_score = 0.0
        gym_hits = nlp_hits.get("positive_hits", {}).get("gym", [])
        if listing.has_gym_keywords:
            gym_score = 10.0
            gym_evidence.append("gym_fitness flag")
        elif gym_hits:
            gym_score = _score_from_hits(len(gym_hits))
            gym_evidence.extend([f"mentions '{hit}'" for hit in gym_hits[:3]])
        gym_multiplier = float(
            self.config.nlp_signals.get("positive", {})
            .get("gym", {})
            .get("weight", 1.0)
        )
        if gym_score:
            gym_score = min(10.0, gym_score * gym_multiplier)
        add_component(
            "gym_fitness",
            score=round(gym_score, 2),
            evidence=gym_evidence,
        )

        # Building quality
        bq_evidence: List[str] = []
        bq_score = 0.0
        if listing.has_building_quality_keywords:
            bq_score = max(bq_score, 7.0)
            bq_evidence.append("building_quality flag")
        if listing.visual_quality_score:
            visual_bq = listing.visual_quality_score / 10
            bq_score = _blend_scores([bq_score, visual_bq]) if bq_score else visual_bq
            bq_evidence.append(f"visual quality {listing.visual_quality_score}")
        bq_multiplier = float(
            self.config.nlp_signals.get("positive", {})
            .get("quality", {})
            .get("weight", 1.0)
        )
        if bq_score:
            bq_score = min(10.0, bq_score * bq_multiplier)
        gross_highrise_multiplier = float(
            self.config.nlp_signals.get("negative", {})
            .get("gross_highrise", {})
            .get("weight", 1.0)
        )
        if nlp_hits.get("negative_hits", {}).get("gross_highrise"):
            bq_score = bq_score * gross_highrise_multiplier
            bq_evidence.append("gross high-rise signal")
        add_component(
            "building_quality",
            score=round(bq_score, 2),
            evidence=bq_evidence,
        )

        # Doorman / concierge
        dm_evidence: List[str] = []
        dm_score = 0.0
        if listing.has_doorman_keywords:
            dm_score = 8.0
            dm_evidence.append("doorman flag")
        amenity_hits = nlp_hits.get("positive_hits", {}).get("amenities", [])
        doorman_amenity_hits = [
            h
            for h in amenity_hits
            if any(
                kw in h
                for kw in [
                    "doorman",
                    "concierge",
                    "lobby attendant",
                    "virtual doorman",
                    "live-in super",
                ]
            )
        ]
        if doorman_amenity_hits:
            dm_score = max(dm_score, _score_from_hits(len(doorman_amenity_hits)))
            dm_evidence.extend(
                [f"mentions '{hit}'" for hit in doorman_amenity_hits[:2]]
            )
        if any(
            kw in text_lower for kw in ["24-hour doorman", "full-time doorman"]
        ):
            dm_score = 10.0
            if "24h/full-time" not in " ".join(dm_evidence):
                dm_evidence.append("24h/full-time doorman")
        elif any(
            kw in text_lower for kw in ["virtual doorman", "part-time doorman"]
        ):
            dm_score = max(dm_score, 6.0)
        add_component(
            "doorman_concierge",
            score=round(dm_score, 2),
            evidence=dm_evidence,
        )

        signals = MatchSignals(
            tranquility_score=(
                round((tranquility_score or 0) / 10, 1)
                if tranquility_score is not None
                else None
            ),
            light_potential=(
                round((light_potential_score or 0) / 10, 1)
                if light_potential_score is not None
                else None
            ),
            visual_quality=(
                round((listing.visual_quality_score or 0) / 10, 1)
                if listing.visual_quality_score is not None
                else None
            ),
            nlp_character_score=(
                round(_score_from_hits(len(character_hits) + len(quality_hits)), 1)
                if character_hits or quality_hits
                else None
            ),
        )

        total = 0.0
        for component in components.values():
            total += (component.score / 10.0) * component.weight

        price_penalty = _soft_cap_penalty(
            listing.price,
            self.config.soft_caps.get("price_soft"),
            self.config.hard_filters.get("price_max"),
        )
        hoa_penalty = (
            _hoa_penalty(listing.hoa_fee) if settings.SEARCH_MODE != "rent" else 0.0
        )
        total = max(0.0, total - price_penalty - hoa_penalty)

        return total, components, signals

    def score_listing(
        self, listing: PropertyListing, min_score_percent: float = 0.0
    ) -> bool:
        total_possible = sum(self._effective_weights.values()) or TOTAL_POINTS

        passes, _ = self._passes_hard_filters(listing)
        if not passes:
            return False

        description, text_lower, nlp_hits, tranquility_score = (
            self._build_listing_context(listing)
        )

        passes, _ = self._passes_additional_hard_filters(
            listing, text_lower, nlp_hits, tranquility_score
        )
        if not passes:
            return False

        total_points, components, signals = self._score_listing(
            listing, nlp_hits, text_lower
        )
        score_percent_value = (total_points / total_possible) * 100
        self._apply_scorecard(
            listing,
            total_points,
            components,
            signals,
            total_possible,
            score_percent_value,
        )

        return score_percent_value >= min_score_percent

    def find_matches(
        self,
        limit: int = 100,
        min_score: float = 0.0,
    ) -> List[Tuple[PropertyListing, float, Dict[str, Any]]]:
        query = self._build_base_query()
        total_possible = sum(self._effective_weights.values()) or TOTAL_POINTS
        listings = self.db.scalars(query).all()
        self.total_analyzed = len(listings)

        scored_listings: List[Tuple[PropertyListing, float, Dict[str, Any]]] = []

        for listing in listings:
            _, text_lower, nlp_hits, tranquility_score = self._build_listing_context(
                listing
            )

            passes, failures = self._passes_additional_hard_filters(
                listing, text_lower, nlp_hits, tranquility_score
            )
            if not passes:
                continue

            total_points, components, signals = self._score_listing(
                listing, nlp_hits, text_lower
            )
            score_percent_value = (total_points / total_possible) * 100
            if score_percent_value < min_score:
                continue

            self._apply_scorecard(
                listing,
                total_points,
                components,
                signals,
                total_possible,
                score_percent_value,
            )
            scored_listings.append((listing, total_points, listing.signals))

        scored_listings.sort(key=lambda item: item[1], reverse=True)
        if self.include_intelligence:
            enrich_listings_with_text_intelligence(
                [item[0] for item in scored_listings], self.db
            )
        return scored_listings[:limit]


def find_advanced_matches(
    criteria: Any,
    db: Session,
    limit: int = 50,
    min_score: float = 0.0,
    vibe_preset: Optional[str] = None,
    include_intelligence: bool = True,
    user_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    matcher = PropertyMatcher(
        criteria,
        db,
        include_intelligence=include_intelligence,
        user_weights=user_weights,
    )
    matches = matcher.find_matches(limit=limit, min_score=min_score)

    results = []
    for listing, score, signals in matches:
        results.append(
            {
                "listing": listing,
                "match_score": listing.match_score,
                "score_points": listing.score_points,
                "feature_scores": listing.feature_scores,
                "address": listing.address,
                "price": listing.price,
                "url": listing.url,
                "days_on_market": listing.days_on_market,
                "signals": signals,
                "why_now": listing.why_now,
            }
        )

    summary = f"Analyzed {matcher.total_analyzed:,} listings. Showing {len(results)} that matter."

    return {
        "results": results,
        "summary": summary,
        "total_analyzed": matcher.total_analyzed,
        "matches_shown": len(results),
        "filters_applied": ["hard_filters"],
        "vibe_preset": vibe_preset,
    }
