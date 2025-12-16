"""Advanced matching algorithm with scoring and ranking.

Sherlock Homes Deduction Engine:
- Multi-factor scoring with configurable weights
- Geospatial intelligence (Tranquility Score)
- Light potential analysis
- Vibe-based preset filtering
- Human-readable match narratives
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func
import logging

from app.models.criteria import Criteria
from app.models.listing import PropertyListing
from app.core.config import settings


def case_insensitive_like(column, pattern):
    """Cross-database case-insensitive LIKE.

    SQLite: LIKE is case-insensitive for ASCII by default.
    PostgreSQL: Needs ilike for case-insensitivity.
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        return column.like(pattern)
    else:
        return column.ilike(pattern)


from app.services.nlp import calculate_text_quality_score, estimate_light_potential
from app.services.geospatial import calculate_tranquility_score, get_tranquility_tier
from app.services.vibe_presets import (
    get_preset,
    apply_preset_weights,
    get_preset_boost_keywords,
    get_preset_penalize_keywords,
    DEFAULT_FEATURE_WEIGHTS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# MATCH NARRATIVE GENERATION
# =============================================================================

# Human-readable feature names for narratives
FEATURE_DISPLAY_NAMES = {
    "natural_light": "natural light",
    "high_ceilings": "high ceilings",
    "outdoor_space": "outdoor space",
    "parking": "parking",
    "view": "views",
    "updated_systems": "updated systems",
    "home_office": "home office potential",
    "storage": "storage",
    "open_floor_plan": "open layout",
    "architectural_details": "architectural character",
    "luxury": "luxury finishes",
    "designer": "designer touches",
    "tech_ready": "smart home features",
    "walk_score": "walkability",
    "transit_score": "transit access",
    "price_reduced": "price reduction",
    "tranquility": "quiet location",
    "light_potential": "light potential",
    "neighborhood_match": "preferred neighborhood",
    "visual_quality": "visual appeal",
}


def generate_match_narrative(
    listing: "PropertyListing",
    match_score: float,
    feature_scores: Dict[str, Any],
    tranquility_data: Optional[Dict] = None,
    light_data: Optional[Dict] = None,
    visual_data: Optional[Dict] = None,
) -> str:
    """
    Generate a human-readable narrative explaining WHY this property matched.

    The narrative follows Sherlock Homes' philosophy: explain the deduction,
    not just show the score. This is what differentiates insight from inventory.

    Args:
        listing: The property listing
        match_score: Overall match score (0-100)
        feature_scores: Dict of feature -> score contribution
        tranquility_data: Optional geospatial tranquility analysis
        light_data: Optional light potential analysis

    Returns:
        A 1-2 sentence narrative explaining the match quality
    """
    if not feature_scores:
        return "Meets your basic requirements."

    # Sort features by score contribution (highest first)
    sorted_features = sorted(
        feature_scores.items(),
        key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
        reverse=True
    )

    # Get top 2-3 contributing features
    top_features = []
    for feature, score in sorted_features[:3]:
        display_name = FEATURE_DISPLAY_NAMES.get(feature, feature.replace("_", " "))
        if score and score > 0:
            top_features.append(display_name)

    # Build narrative based on score tier
    if match_score >= 85:
        # Exceptional match
        if len(top_features) >= 2:
            narrative = f"Excellent match — exceptional {top_features[0]} and {top_features[1]}."
        elif len(top_features) == 1:
            narrative = f"Excellent match — standout {top_features[0]}."
        else:
            narrative = "Excellent match across your criteria."

    elif match_score >= 70:
        # Strong match
        if len(top_features) >= 2:
            narrative = f"Strong match — great {top_features[0]} with solid {top_features[1]}."
        elif len(top_features) == 1:
            narrative = f"Strong match with notable {top_features[0]}."
        else:
            narrative = "Strong match on your key requirements."

    elif match_score >= 55:
        # Good match
        if top_features:
            narrative = f"Good fit with {top_features[0]}."
        else:
            narrative = "Good fit for your criteria."

    elif match_score >= 40:
        # Moderate match
        if top_features:
            narrative = f"Worth considering — has {top_features[0]}."
        else:
            narrative = "Worth a look if other priorities are flexible."

    else:
        # Below threshold
        narrative = "Meets some requirements but missing key features."

    # Add special callouts for intelligence signals
    callouts = []

    # Tranquility callout
    if tranquility_data and tranquility_data.get("score"):
        tranq_score = tranquility_data["score"]
        if tranq_score >= 80:
            callouts.append("Very quiet location.")
        elif tranq_score <= 40 and tranquility_data.get("warnings"):
            # Only mention if it's notably bad
            warning = tranquility_data["warnings"][0] if tranquility_data["warnings"] else None
            if warning:
                callouts.append(f"Note: {warning}.")

    # Light potential callout
    if light_data and light_data.get("score"):
        light_score = light_data["score"]
        if light_score >= 75:
            callouts.append("Excellent light potential.")
        elif light_score <= 35:
            callouts.append("Limited natural light expected.")

    # Visual quality callout
    if visual_data and visual_data.get("score"):
        visual_score = visual_data["score"]
        if visual_score >= 85:
            callouts.append("Beautifully maintained with modern finishes.")
        elif visual_score >= 70:
            callouts.append("Well-presented property.")
        elif visual_score <= 45:
            callouts.append("May need cosmetic updates.")

    # Combine narrative with callouts
    if callouts:
        narrative = narrative + " " + " ".join(callouts)

    return narrative


def generate_skip_summary(
    total_analyzed: int,
    matches_shown: int,
    filters_applied: List[str],
) -> str:
    """
    Generate a summary of the filtering process.

    Example: "Analyzed 847 listings. Showing 12 that matter."
    """
    skipped = total_analyzed - matches_shown

    if skipped > 0:
        summary = f"Analyzed {total_analyzed:,} listings. Showing {matches_shown} that matter."
        if filters_applied:
            summary += f" Filtered by: {', '.join(filters_applied[:3])}"
            if len(filters_applied) > 3:
                summary += f" +{len(filters_applied) - 3} more"
    else:
        summary = f"Showing all {matches_shown} matching listings."

    return summary


class PropertyMatcher:
    """Sophisticated property matching with multi-factor scoring.

    The Sherlock Homes Deduction Engine applies multiple intelligence layers:
    1. Hard filters (price, beds, neighborhoods to avoid)
    2. Feature detection (NLP keyword analysis)
    3. Geospatial intelligence (Tranquility Score)
    4. Light potential analysis
    5. Vibe-based weight adjustments
    6. Human-readable match narratives
    """

    def __init__(self, criteria: Criteria, db: Session, vibe_preset: Optional[str] = None):
        self.criteria = criteria
        self.db = db
        self.vibe_preset = vibe_preset
        self.weights = self._initialize_weights()
        self.boost_keywords = get_preset_boost_keywords(vibe_preset)
        self.penalize_keywords = get_preset_penalize_keywords(vibe_preset)
    
    def _initialize_weights(self) -> Dict[str, float]:
        """Initialize feature weights from criteria, vibe preset, or defaults.

        Priority order:
        1. Explicit criteria weights (user-specified)
        2. Vibe preset weights (if vibe selected)
        3. Default weights
        """
        # Start with defaults
        base_weights = DEFAULT_FEATURE_WEIGHTS.copy()

        # Apply vibe preset if selected
        if self.vibe_preset:
            base_weights = apply_preset_weights(base_weights, self.vibe_preset)

        # User criteria weights override everything
        if self.criteria.feature_weights:
            base_weights.update(self.criteria.feature_weights)

        return base_weights
    
    def find_matches(
        self,
        limit: int = 100,
        min_score: float = 0.0,
        include_intelligence: bool = True,
    ) -> List[Tuple[PropertyListing, float, Dict[str, Any]]]:
        """Find and score property matches with full intelligence analysis.

        Args:
            limit: Maximum number of results
            min_score: Minimum match score threshold
            include_intelligence: Calculate tranquility/light scores (slower but richer)

        Returns:
            List of tuples: (listing, score, intelligence_data)
            intelligence_data contains tranquility, light_potential, and narrative
        """

        # Build base query with hard filters
        query = self._build_base_query()

        # Execute query
        listings = self.db.scalars(query).all()
        self.total_analyzed = len(listings)

        # Score each listing
        scored_listings = []
        for listing in listings:
            # Core match score
            score = self._calculate_match_score(listing)

            if score >= min_score:
                # Get feature breakdown
                feature_scores = self._get_feature_breakdown(listing)

                # Intelligence analysis (optional but recommended)
                intelligence = {}
                if include_intelligence:
                    # Tranquility Score (geospatial)
                    if listing.lat and listing.lon:
                        tranquility = calculate_tranquility_score(listing.lat, listing.lon)
                        intelligence["tranquility"] = tranquility

                        # Factor tranquility into score
                        tranq_weight = self.weights.get("tranquility", 6)
                        tranq_bonus = (tranquility["score"] / 100) * tranq_weight
                        score = min(100, score + tranq_bonus * 0.3)  # 30% weight

                    # Light Potential Score (NLP + heuristics)
                    light_data = estimate_light_potential(
                        description=listing.description,
                        is_north_facing_only=listing.is_north_facing_only or False,
                        is_basement_unit=listing.is_basement_unit or False,
                        has_natural_light_keywords=listing.has_natural_light_keywords or False,
                        photo_count=len(listing.photos) if listing.photos else 0,
                    )
                    intelligence["light_potential"] = light_data

                    # Factor light into score for Light Chaser vibe
                    if self.vibe_preset == "light_chaser":
                        light_bonus = (light_data["score"] / 100) * 10
                        score = min(100, score + light_bonus * 0.5)

                    # Visual Quality Score (from Claude Vision photo analysis)
                    if listing.visual_quality_score is not None:
                        visual_data = {
                            "score": listing.visual_quality_score,
                            "dimensions": listing.visual_assessment.get("dimensions", {}) if listing.visual_assessment else {},
                            "red_flags": listing.visual_assessment.get("red_flags", []) if listing.visual_assessment else [],
                            "highlights": listing.visual_assessment.get("highlights", []) if listing.visual_assessment else [],
                            "confidence": listing.visual_assessment.get("confidence", "unknown") if listing.visual_assessment else "unknown",
                        }
                        intelligence["visual_quality"] = visual_data

                        # Factor visual quality into score
                        visual_weight = self.weights.get("visual_quality", 8)
                        visual_bonus = (listing.visual_quality_score / 100) * visual_weight
                        score = min(100, score + visual_bonus * 0.25)

                        # Red flag penalty
                        red_flags = visual_data.get("red_flags", [])
                        score = max(0, score - len(red_flags) * 3)

                    # Generate match narrative
                    narrative = generate_match_narrative(
                        listing=listing,
                        match_score=score,
                        feature_scores=feature_scores,
                        tranquility_data=intelligence.get("tranquility"),
                        light_data=intelligence.get("light_potential"),
                        visual_data=intelligence.get("visual_quality"),
                    )
                    intelligence["narrative"] = narrative

                # Apply vibe-specific keyword adjustments
                if listing.description:
                    desc_lower = listing.description.lower()

                    # Boost for matching vibe keywords
                    boost_count = sum(1 for kw in self.boost_keywords if kw in desc_lower)
                    score = min(100, score + boost_count * 1.5)

                    # Penalize for anti-vibe keywords
                    penalty_count = sum(1 for kw in self.penalize_keywords if kw in desc_lower)
                    score = max(0, score - penalty_count * 2)

                # Update the listing's match score and data
                listing.match_score = score
                listing.feature_scores = feature_scores

                scored_listings.append((listing, score, intelligence))

        # Sort by score (highest first)
        scored_listings.sort(key=lambda x: x[1], reverse=True)

        # Apply limit
        return scored_listings[:limit]
    
    def _build_base_query(self):
        """Build the base query with hard filters."""
        query = select(PropertyListing)
        filters = []
        
        # Price filters
        if self.criteria.price_min is not None:
            filters.append(PropertyListing.price >= self.criteria.price_min)
        if self.criteria.price_max is not None:
            filters.append(PropertyListing.price <= self.criteria.price_max)
        
        # Size filters
        if self.criteria.beds_min is not None:
            filters.append(PropertyListing.beds >= self.criteria.beds_min)
        if self.criteria.beds_max is not None:
            filters.append(PropertyListing.beds <= self.criteria.beds_max)
        if self.criteria.baths_min is not None:
            filters.append(PropertyListing.baths >= self.criteria.baths_min)
        if self.criteria.sqft_min is not None:
            filters.append(PropertyListing.sqft >= self.criteria.sqft_min)
        if self.criteria.sqft_max is not None:
            filters.append(PropertyListing.sqft <= self.criteria.sqft_max)
        
        # Property type filter
        if self.criteria.property_types:
            filters.append(PropertyListing.property_type.in_(self.criteria.property_types))
        
        # Neighborhood filters
        if self.criteria.preferred_neighborhoods:
            # Soft preference - will boost score but not exclude
            pass
        if self.criteria.avoid_neighborhoods:
            filters.append(
                or_(
                    PropertyListing.neighborhood.notin_(self.criteria.avoid_neighborhoods),
                    PropertyListing.neighborhood.is_(None)
                )
            )
        
        # Red flag exclusions
        if self.criteria.avoid_busy_streets:
            filters.append(PropertyListing.has_busy_street_keywords == False)
        if self.criteria.avoid_north_facing_only:
            filters.append(PropertyListing.is_north_facing_only == False)
        if self.criteria.avoid_basement_units:
            filters.append(PropertyListing.is_basement_unit == False)
        
        # Excluded streets (use cross-database case-insensitive LIKE)
        if self.criteria.excluded_streets:
            for street in self.criteria.excluded_streets:
                filters.append(~case_insensitive_like(PropertyListing.address, f"%{street}%"))
        
        # Days on market filter
        if self.criteria.max_days_on_market is not None:
            filters.append(PropertyListing.days_on_market <= self.criteria.max_days_on_market)
        
        # Apply all filters
        if filters:
            query = query.where(and_(*filters))
        
        return query
    
    def _calculate_match_score(self, listing: PropertyListing) -> float:
        """Calculate comprehensive match score for a listing."""
        score = 0.0
        max_score = 0.0
        
        # Essential features scoring
        features_to_check = [
            ("natural_light", listing.has_natural_light_keywords, self.criteria.require_natural_light),
            ("high_ceilings", listing.has_high_ceiling_keywords, self.criteria.require_high_ceilings),
            ("outdoor_space", listing.has_outdoor_space_keywords, self.criteria.require_outdoor_space),
            ("parking", listing.has_parking_keywords, self.criteria.require_parking),
            ("view", listing.has_view_keywords, self.criteria.require_view),
            ("updated_systems", listing.has_updated_systems_keywords, self.criteria.require_updated_systems),
            ("home_office", listing.has_home_office_keywords, self.criteria.require_home_office),
            ("storage", listing.has_storage_keywords, self.criteria.require_storage),
        ]
        
        for feature_name, has_feature, is_required in features_to_check:
            weight = self.weights.get(feature_name, 5)
            if is_required:
                max_score += weight * 2  # Double weight for required features
                if has_feature:
                    score += weight * 2
            else:
                max_score += weight
                if has_feature:
                    score += weight
        
        # Quality indicators
        if listing.has_luxury_keywords:
            score += self.weights.get("luxury", 3)
        if listing.has_designer_keywords:
            score += self.weights.get("designer", 3)
        if listing.has_tech_ready_keywords:
            score += self.weights.get("tech_ready", 4)
        
        max_score += self.weights.get("luxury", 3) + self.weights.get("designer", 3) + self.weights.get("tech_ready", 4)
        
        # Neighborhood scoring
        if self.criteria.preferred_neighborhoods and listing.neighborhood:
            if listing.neighborhood in self.criteria.preferred_neighborhoods:
                score += self.weights.get("neighborhood_match", 9)
            max_score += self.weights.get("neighborhood_match", 9)
        
        # Walk score
        if self.criteria.min_walk_score and listing.walk_score:
            if listing.walk_score >= self.criteria.min_walk_score:
                score += self.weights.get("walk_score", 8)
            else:
                # Partial credit for close walk scores
                diff = self.criteria.min_walk_score - listing.walk_score
                if diff <= 10:
                    score += self.weights.get("walk_score", 8) * (1 - diff/20)
            max_score += self.weights.get("walk_score", 8)
        
        # Price value scoring (lower price within range is better)
        if self.criteria.price_min and self.criteria.price_max and listing.price:
            price_range = self.criteria.price_max - self.criteria.price_min
            if price_range > 0:
                price_position = (listing.price - self.criteria.price_min) / price_range
                # Lower prices get higher scores
                price_score = (1 - price_position) * self.weights.get("price_match", 10)
                score += price_score
                max_score += self.weights.get("price_match", 10)
        
        # Deal quality scoring
        if listing.is_price_reduced:
            score += self.weights.get("deal_quality", 5)
        if listing.is_back_on_market:
            score += self.weights.get("deal_quality", 5) * 0.5
        max_score += self.weights.get("deal_quality", 5)
        
        # Text quality scoring (if description available)
        if listing.description:
            text_score = calculate_text_quality_score(
                listing.description, 
                {"feature_weights": self.weights}
            )
            # Text score is 0-100, normalize to our scale
            score += (text_score / 100) * 20
            max_score += 20
        
        # Parking type matching
        if self.criteria.parking_type and listing.parking_type:
            if listing.parking_type == self.criteria.parking_type:
                score += 5
            elif self.criteria.parking_type == "any" and listing.parking_type:
                score += 3
            max_score += 5
        
        # Penalize red flags that weren't filtered out
        if listing.has_foundation_issues_keywords:
            score -= 10
        if listing.has_hoa_issues_keywords:
            score -= 8
        
        # Calculate final percentage score
        if max_score > 0:
            final_score = (score / max_score) * 100
        else:
            final_score = 50  # Default middle score if no criteria
        
        return max(0, min(100, final_score))  # Clamp between 0-100
    
    def _get_feature_breakdown(self, listing: PropertyListing) -> Dict[str, Any]:
        """Get detailed breakdown of feature scores."""
        breakdown = {}
        
        # Check each feature
        features = {
            "natural_light": listing.has_natural_light_keywords,
            "high_ceilings": listing.has_high_ceiling_keywords,
            "outdoor_space": listing.has_outdoor_space_keywords,
            "parking": listing.has_parking_keywords,
            "view": listing.has_view_keywords,
            "updated_systems": listing.has_updated_systems_keywords,
            "home_office": listing.has_home_office_keywords,
            "storage": listing.has_storage_keywords,
            "luxury": listing.has_luxury_keywords,
            "designer": listing.has_designer_keywords,
            "tech_ready": listing.has_tech_ready_keywords,
        }
        
        for feature, has_it in features.items():
            if has_it:
                breakdown[feature] = self.weights.get(feature, 1)
        
        # Add other scoring factors
        if listing.walk_score and self.criteria.min_walk_score:
            if listing.walk_score >= self.criteria.min_walk_score:
                breakdown["walk_score"] = self.weights.get("walk_score", 8)
        
        if listing.is_price_reduced:
            breakdown["price_reduced"] = self.weights.get("deal_quality", 5)
        
        return breakdown


def find_advanced_matches(
    criteria: Criteria,
    db: Session,
    limit: int = 50,
    min_score: float = 30.0,
    vibe_preset: Optional[str] = None,
    include_intelligence: bool = True,
) -> Dict[str, Any]:
    """
    Find property matches using the Sherlock Homes Deduction Engine.

    Returns a dict containing:
    - results: List of match dicts with listing data, score, and intelligence
    - summary: Skip summary explaining what was filtered
    - total_analyzed: Number of listings that were scored
    - filters_applied: List of active filter names

    Args:
        criteria: User's search criteria
        db: Database session
        limit: Maximum results to return
        min_score: Minimum match score threshold
        vibe_preset: Optional vibe preset ID ('light_chaser', 'urban_professional', 'deal_hunter')
        include_intelligence: Calculate tranquility/light scores (recommended)
    """
    matcher = PropertyMatcher(criteria, db, vibe_preset=vibe_preset)
    matches = matcher.find_matches(
        limit=limit,
        min_score=min_score,
        include_intelligence=include_intelligence,
    )

    # Build results list with full intelligence data
    results = []
    for listing, score, intelligence in matches:
        result = {
            "listing": listing,
            "match_score": round(score, 1),
            "feature_scores": listing.feature_scores,
            "address": listing.address,
            "price": listing.price,
            "url": listing.url,
            "days_on_market": listing.days_on_market,
            # Intelligence data
            "narrative": intelligence.get("narrative", ""),
            "tranquility": intelligence.get("tranquility"),
            "light_potential": intelligence.get("light_potential"),
            "visual_quality": intelligence.get("visual_quality"),
        }
        results.append(result)

    # Determine which filters were applied
    filters_applied = []
    if criteria.price_max:
        filters_applied.append(f"price ≤ ${criteria.price_max:,}")
    if criteria.beds_min:
        filters_applied.append(f"{criteria.beds_min}+ beds")
    if criteria.preferred_neighborhoods:
        filters_applied.append(f"in {', '.join(criteria.preferred_neighborhoods[:2])}")
    if criteria.avoid_busy_streets:
        filters_applied.append("quiet streets")
    if criteria.require_natural_light:
        filters_applied.append("natural light")
    if vibe_preset:
        preset = get_preset(vibe_preset)
        if preset:
            filters_applied.append(f"{preset.name} vibe")

    # Generate skip summary
    summary = generate_skip_summary(
        total_analyzed=matcher.total_analyzed,
        matches_shown=len(results),
        filters_applied=filters_applied,
    )

    logger.info(f"Sherlock Homes: {summary}")

    return {
        "results": results,
        "summary": summary,
        "total_analyzed": matcher.total_analyzed,
        "matches_shown": len(results),
        "filters_applied": filters_applied,
        "vibe_preset": vibe_preset,
    }