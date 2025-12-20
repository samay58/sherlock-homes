"""
Vibe Presets for Sherlock Homes

Personality-based filtering presets that apply different weights
to property features based on lifestyle preferences.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class VibePreset:
    """Represents a vibe preset configuration."""
    id: str
    name: str
    tagline: str
    icon: str
    description: str
    weights: Dict[str, int]  # Feature -> weight (0-20)
    filters: Dict[str, Any]  # Hard filters to apply
    boost_keywords: List[str] = field(default_factory=list)  # Extra keywords to look for
    penalize_keywords: List[str] = field(default_factory=list)  # Keywords to penalize


# =============================================================================
# PRESET DEFINITIONS
# =============================================================================

VIBE_PRESETS: Dict[str, VibePreset] = {
    "light_chaser": VibePreset(
        id="light_chaser",
        name="Light Chaser",
        tagline="South-facing, big windows, views for days",
        icon="",
        description="Maximizes natural light, prioritizes views and high ceilings. "
                   "Perfect for those who need sunlight for their mental health or work-from-home setup.",
        weights={
            "natural_light": 20,
            "view": 15,
            "high_ceilings": 12,
            "open_floor_plan": 8,
            "outdoor_space": 6,
            "architectural_details": 5,
            "updated_systems": 4,
            "tranquility": 3,  # Less important
            "parking": 2,
        },
        filters={
            "avoid_north_facing_only": True,
            "avoid_basement_units": True,
        },
        boost_keywords=[
            "south-facing", "southwest", "floor-to-ceiling", "panoramic",
            "sunny", "bright", "skylights", "corner unit", "top floor",
            "penthouse", "artist loft", "light-filled"
        ],
        penalize_keywords=[
            "north-facing", "garden level", "basement", "lower unit",
            "interior unit", "no view", "dark"
        ]
    ),

    "urban_professional": VibePreset(
        id="urban_professional",
        name="Urban Professional",
        tagline="Walk to work, near nightlife, modern finishes",
        icon="",
        description="Optimizes for walkability, transit access, and modern amenities. "
                   "Ideal for young professionals who prioritize convenience over space.",
        weights={
            "walk_score": 15,
            "transit_score": 12,
            "updated_systems": 10,
            "tech_ready": 8,
            "natural_light": 6,
            "view": 6,
            "open_floor_plan": 5,
            "parking": 3,  # Less important in urban areas
            "outdoor_space": 3,
            "storage": 2,
        },
        filters={
            "min_walk_score": 85,
            "property_types": ["condo", "loft", "townhouse"],
        },
        boost_keywords=[
            "walkable", "steps from", "urban", "modern", "renovated",
            "smart home", "fiber", "gym", "rooftop", "doorman",
            "concierge", "bike storage", "ev charging"
        ],
        penalize_keywords=[
            "suburban", "cul-de-sac", "remote", "no transit"
        ]
    ),

    "deal_hunter": VibePreset(
        id="deal_hunter",
        name="Deal Hunter",
        tagline="Price drops, motivated sellers, negotiation potential",
        icon="",
        description="Focuses on properties with deal signals: price reductions, "
                   "days on market, and motivated seller language. For the strategic buyer.",
        weights={
            "deal_quality": 20,
            "price_position": 15,
            "days_on_market_bonus": 10,
            "natural_light": 5,
            "updated_systems": 5,
            "outdoor_space": 4,
            "parking": 4,
            "tranquility": 3,
            "view": 3,
        },
        filters={
            "include_price_reduced": True,
            "min_days_on_market": 14,  # Properties that have sat a bit
        },
        boost_keywords=[
            "price reduced", "motivated", "must sell", "priced to sell",
            "bring offers", "just reduced", "new price", "seller relocating",
            "estate sale", "foreclosure", "fixer", "as-is", "investor special"
        ],
        penalize_keywords=[
            "multiple offers", "highest and best", "over asking",
            "bidding war", "sold as-is"
        ]
    ),
}


# =============================================================================
# PRESET APPLICATION FUNCTIONS
# =============================================================================

def get_preset(preset_id: str) -> Optional[VibePreset]:
    """Get a preset by ID."""
    return VIBE_PRESETS.get(preset_id)


def get_all_presets() -> List[Dict]:
    """Get all presets as a list of dicts (for API response)."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "tagline": p.tagline,
            "icon": p.icon,
            "description": p.description,
        }
        for p in VIBE_PRESETS.values()
    ]


def apply_preset_weights(
    base_weights: Dict[str, int],
    preset_id: Optional[str]
) -> Dict[str, int]:
    """
    Apply preset weights on top of base weights.
    Preset weights take precedence where defined.
    """
    if not preset_id:
        return base_weights

    preset = get_preset(preset_id)
    if not preset:
        return base_weights

    # Merge: preset weights override base weights
    merged = {**base_weights, **preset.weights}
    return merged


def apply_preset_filters(
    base_filters: Dict[str, Any],
    preset_id: Optional[str]
) -> Dict[str, Any]:
    """
    Apply preset filters on top of base filters.
    Preset filters take precedence where defined.
    """
    if not preset_id:
        return base_filters

    preset = get_preset(preset_id)
    if not preset:
        return base_filters

    # Merge: preset filters override base filters
    merged = {**base_filters, **preset.filters}
    return merged


def get_preset_boost_keywords(preset_id: Optional[str]) -> List[str]:
    """Get the boost keywords for a preset."""
    if not preset_id:
        return []

    preset = get_preset(preset_id)
    return preset.boost_keywords if preset else []


def get_preset_penalize_keywords(preset_id: Optional[str]) -> List[str]:
    """Get the penalize keywords for a preset."""
    if not preset_id:
        return []

    preset = get_preset(preset_id)
    return preset.penalize_keywords if preset else []


# =============================================================================
# DEFAULT WEIGHTS (used when no preset is selected)
# =============================================================================

DEFAULT_FEATURE_WEIGHTS = {
    "natural_light": 10,
    "outdoor_space": 8,
    "view": 9,
    "high_ceilings": 7,
    "parking": 6,
    "updated_systems": 7,
    "home_office": 5,
    "storage": 4,
    "open_floor_plan": 5,
    "architectural_details": 4,
    "tranquility": 6,
    "walk_score": 5,
    "transit_score": 4,
    "tech_ready": 3,
    "deal_quality": 3,
    "price_position": 5,
    "days_on_market_bonus": 2,
    "budget_fit": 7,
    "recency": 4,
    "visual_quality": 8,  # Visual appeal from Claude Vision photo analysis
}
