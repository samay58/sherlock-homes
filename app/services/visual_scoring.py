"""
Visual Quality Scoring Service for Sherlock Homes

Analyzes property photos using Claude Vision to score visual appeal,
modernity, condition, brightness, staging, and cleanliness.

This follows the same pattern as geospatial.py and nlp.py for intelligence scoring.
"""

import json
import hashlib
import logging
import base64
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# VISION API PROMPT
# =============================================================================

VISUAL_SCORING_PROMPT = """Analyze this property photo for a real estate listing. Rate each dimension on a scale of 0-100:

1. **Modernity** (0-100): How modern are the finishes, fixtures, and design?
   - 90-100: Brand new or recently renovated (2020s), designer finishes
   - 70-89: Modern/updated (2010s), contemporary fixtures
   - 50-69: Dated but acceptable (2000s), functional
   - 30-49: Clearly dated (1990s or earlier), needs cosmetic updates
   - 0-29: Very dated, original from 1970s or earlier

2. **Condition** (0-100): What is the visible maintenance and repair state?
   - 90-100: Immaculate, no visible wear
   - 70-89: Well-maintained, minor wear
   - 50-69: Average condition, some wear visible
   - 30-49: Needs repairs, visible damage or heavy wear
   - 0-29: Poor condition, significant damage

3. **Brightness** (0-100): How well-lit is the space (natural + artificial)?
   - 90-100: Abundant natural light, bright and airy
   - 70-89: Good lighting, pleasant
   - 50-69: Adequate lighting
   - 30-49: Dim, limited light
   - 0-29: Dark, poorly lit

4. **Staging** (0-100): How well is the space presented?
   - 90-100: Professionally staged, magazine-quality
   - 70-89: Well-arranged, clean presentation
   - 50-69: Lived-in but tidy
   - 30-49: Cluttered or messy
   - 0-29: Poorly presented, distracting mess

5. **Cleanliness** (0-100): How clean and tidy is the space?
   - 90-100: Spotless, pristine
   - 70-89: Clean, well-kept
   - 50-69: Acceptable, minor untidiness
   - 30-49: Dirty or neglected areas visible
   - 0-29: Very dirty, needs deep cleaning

Also identify specific observations:
- **Red flags**: Issues that would concern a buyer (e.g., "water_stains", "outdated_appliances", "visible_damage", "worn_flooring", "popcorn_ceiling")
- **Highlights**: Positive features visible (e.g., "modern_kitchen", "hardwood_floors", "abundant_light", "designer_bathroom", "professional_staging")

Respond with ONLY a valid JSON object, no other text:
{"modernity": <0-100>, "condition": <0-100>, "brightness": <0-100>, "staging": <0-100>, "cleanliness": <0-100>, "red_flags": ["flag1", ...], "highlights": ["highlight1", ...]}"""


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def compute_photos_hash(photos: List[str]) -> str:
    """Compute SHA256 hash of photo URLs for cache invalidation."""
    if not photos:
        return ""
    # Sort URLs for consistent hashing regardless of order
    sorted_urls = sorted(photos)
    content = json.dumps(sorted_urls)
    return hashlib.sha256(content.encode()).hexdigest()


def should_reanalyze(
    existing_hash: Optional[str],
    existing_analyzed_at: Optional[datetime],
    new_photos: List[str],
    max_age_days: int = 30
) -> bool:
    """
    Determine if we should re-analyze photos for a listing.

    Returns True if:
    - No previous analysis exists
    - Photo URLs have changed (hash mismatch)
    - Analysis is older than max_age_days
    """
    if not existing_hash or not existing_analyzed_at:
        return True  # Never analyzed

    new_hash = compute_photos_hash(new_photos)
    if new_hash != existing_hash:
        return True  # Photos changed

    age = datetime.utcnow() - existing_analyzed_at
    if age.days > max_age_days:
        return True  # Analysis is stale

    return False


def sample_photo_indices(total_photos: int, sample_size: int = 3) -> List[int]:
    """
    Return indices of photos to analyze.

    Strategy: [0, 2, 4] to get hero shot, kitchen, and secondary room.
    Falls back to first N if fewer photos available.
    """
    if total_photos == 0:
        return []

    # Preferred indices: hero (0), kitchen (2), secondary (4)
    preferred = [0, 2, 4]

    # Filter to valid indices
    valid = [i for i in preferred if i < total_photos]

    # If we don't have enough, fill with remaining indices
    if len(valid) < sample_size:
        remaining = [i for i in range(total_photos) if i not in valid]
        valid.extend(remaining[:sample_size - len(valid)])

    return valid[:sample_size]


async def analyze_single_photo(photo_url: str) -> Optional[Dict[str, Any]]:
    """
    Analyze a single photo using Claude Vision API.

    Returns dict with scores and signals, or None if analysis fails.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not configured, skipping visual analysis")
        return None

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 500,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": photo_url
                                }
                            },
                            {
                                "type": "text",
                                "text": VISUAL_SCORING_PROMPT
                            }
                        ]
                    }]
                }
            )
            response.raise_for_status()

            result = response.json()
            content = result["content"][0]["text"]

            # Parse JSON response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)

    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error analyzing photo {photo_url}: {e.response.status_code}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse vision response for {photo_url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error analyzing photo {photo_url}: {e}")
        return None


def aggregate_photo_scores(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate scores from multiple photo analyses.

    Returns:
    {
        "score": 0-100 (weighted composite),
        "dimensions": {modernity, condition, brightness, staging, cleanliness},
        "red_flags": [...],
        "highlights": [...],
        "photos_analyzed": int,
        "confidence": "high" | "medium" | "low"
    }
    """
    if not analyses:
        return {
            "score": None,
            "dimensions": {},
            "red_flags": [],
            "highlights": [],
            "photos_analyzed": 0,
            "confidence": "none"
        }

    # Average each dimension across photos
    dimensions = ["modernity", "condition", "brightness", "staging", "cleanliness"]
    averaged = {}

    for dim in dimensions:
        values = [a.get(dim, 50) for a in analyses if dim in a]
        averaged[dim] = int(sum(values) / len(values)) if values else 50

    # Collect all red flags and highlights (deduplicated)
    all_red_flags = set()
    all_highlights = set()
    for a in analyses:
        all_red_flags.update(a.get("red_flags", []))
        all_highlights.update(a.get("highlights", []))

    # Weighted composite score
    weights = {
        "modernity": 0.25,
        "condition": 0.25,
        "brightness": 0.20,
        "staging": 0.15,
        "cleanliness": 0.15
    }
    composite = sum(averaged.get(k, 50) * w for k, w in weights.items())

    # Confidence based on photos analyzed
    photos_analyzed = len(analyses)
    if photos_analyzed >= 3:
        confidence = "high"
    elif photos_analyzed == 2:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "score": int(round(composite)),
        "dimensions": averaged,
        "red_flags": list(all_red_flags),
        "highlights": list(all_highlights),
        "photos_analyzed": photos_analyzed,
        "confidence": confidence
    }


async def analyze_listing_photos(
    photos: List[str],
    listing_id: Optional[str] = None,
    sample_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analyze photos for a property listing.

    Args:
        photos: List of photo URLs
        listing_id: Optional identifier for logging
        sample_size: Number of photos to analyze (default from config)

    Returns:
        Dict with score, dimensions, signals, and metadata
    """
    if not photos:
        logger.debug(f"No photos to analyze for listing {listing_id}")
        return {
            "score": None,
            "dimensions": {},
            "red_flags": [],
            "highlights": [],
            "photos_analyzed": 0,
            "confidence": "none",
            "note": "No photos available"
        }

    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not configured")
        return {
            "score": None,
            "dimensions": {},
            "red_flags": [],
            "highlights": [],
            "photos_analyzed": 0,
            "confidence": "none",
            "note": "API key not configured"
        }

    # Determine sample size
    if sample_size is None:
        sample_size = settings.VISUAL_PHOTOS_SAMPLE_SIZE

    # Get indices to analyze
    indices = sample_photo_indices(len(photos), sample_size)
    photos_to_analyze = [photos[i] for i in indices]

    logger.info(f"Analyzing {len(photos_to_analyze)} photos for listing {listing_id}")

    # Analyze each photo
    analyses = []
    for i, photo_url in enumerate(photos_to_analyze):
        logger.debug(f"  Analyzing photo {i+1}/{len(photos_to_analyze)}: {photo_url[:60]}...")
        result = await analyze_single_photo(photo_url)
        if result:
            analyses.append(result)

    # Aggregate results
    aggregated = aggregate_photo_scores(analyses)
    aggregated["note"] = f"Analyzed photos at indices {indices}"

    logger.info(f"Visual score for {listing_id}: {aggregated['score']} ({aggregated['confidence']} confidence)")

    return aggregated


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_visual_tier(score: Optional[int]) -> str:
    """Get human-readable tier for visual quality score."""
    if score is None:
        return "Unknown"
    if score >= 85:
        return "Stunning"
    elif score >= 70:
        return "Very Appealing"
    elif score >= 55:
        return "Average"
    elif score >= 40:
        return "Below Average"
    else:
        return "Needs Work"


def format_visual_summary(assessment: Optional[Dict[str, Any]]) -> str:
    """Format visual assessment as a human-readable summary."""
    if not assessment or not assessment.get("score"):
        return "Visual analysis not available."

    score = assessment["score"]
    tier = get_visual_tier(score)
    confidence = assessment.get("confidence", "unknown")

    parts = [f"Visual Appeal: {tier} ({score}/100, {confidence} confidence)"]

    if assessment.get("highlights"):
        highlights = ", ".join(assessment["highlights"][:3])
        parts.append(f"Highlights: {highlights}")

    if assessment.get("red_flags"):
        flags = ", ".join(assessment["red_flags"][:3])
        parts.append(f"Concerns: {flags}")

    return " | ".join(parts)
