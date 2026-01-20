"""
Visual Quality Scoring Service for Sherlock Homes

Analyzes property photos using OpenAI Vision to score visual appeal,
modernity, condition, brightness, staging, and cleanliness.

This follows the same pattern as geospatial.py and nlp.py for intelligence scoring.
"""

import json
import hashlib
import logging
import base64
import httpx
import socket
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# VISION API PROMPT
# =============================================================================

VISUAL_SCORING_PROMPT = """Analyze this property photo for buyer-focused quality. Rate each dimension on a scale of 0-100:

1. Modernity (0-100): finishes, fixtures, and design recency.
2. Condition (0-100): visible maintenance and repair state.
3. Brightness (0-100): natural + artificial light quality.
4. Staging (0-100): presentation quality (not over-staging).
5. Cleanliness (0-100): cleanliness and tidiness.

Also identify specific observations using ONLY these tokens:

Red flags:
- flipper_gray_palette
- lvp_flooring
- staged_furniture
- over_staged
- dark_interior
- deferred_maintenance
- ultra_wide_distortion
- visible_damage
- worn_finishes

Highlights:
- natural_light_visible
- outdoor_greenery
- original_details
- warm_materials
- high_ceilings_visible
- open_layout
- quality_kitchen

Respond with ONLY a valid JSON object, no other text:
{"modernity": <0-100>, "condition": <0-100>, "brightness": <0-100>, "staging": <0-100>, "cleanliness": <0-100>, "red_flags": ["flag1", ...], "highlights": ["highlight1", ...]}"""


def _extract_output_text(payload: Dict[str, Any]) -> Optional[str]:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]

    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"}:
                return content.get("text")

    for choice in payload.get("choices", []) or []:
        message = choice.get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for block in content:
                if block.get("type") in {"text", "output_text"}:
                    return block.get("text")

    return None


def _parse_json_response(content: str) -> Optional[Dict[str, Any]]:
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse vision response JSON: %s", exc)
        return None


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
    Analyze a single photo using OpenAI Vision (Responses API).

    Returns dict with scores and signals, or None if analysis fails.
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping visual analysis")
        return None

    def build_request(image_url: str) -> Dict[str, Any]:
        return {
            "model": settings.OPENAI_VISION_MODEL,
            "temperature": 0.2,
            "max_output_tokens": settings.OPENAI_VISION_MAX_OUTPUT_TOKENS,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": VISUAL_SCORING_PROMPT},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ],
        }

    async def call_openai(client: httpx.AsyncClient, image_url: str) -> httpx.Response:
        return await client.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "content-type": "application/json",
            },
            json=build_request(image_url),
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await call_openai(client, photo_url)
            if response.status_code >= 400:
                error_detail = response.text[:500]
                logger.warning("Vision request failed (%s): %s", response.status_code, error_detail)
                if response.status_code in {400, 422}:
                    try:
                        image_response = await client.get(photo_url)
                        image_response.raise_for_status()
                        content_type = image_response.headers.get("content-type", "image/jpeg")
                        b64 = base64.b64encode(image_response.content).decode("ascii")
                        data_url = f"data:{content_type};base64,{b64}"
                        response = await call_openai(client, data_url)
                    except Exception as exc:
                        logger.warning("Failed to fetch image for base64 fallback: %s", exc)
                        return None

            response.raise_for_status()

            result = response.json()
            content = _extract_output_text(result)
            if not content:
                logger.warning("No output text in vision response for %s", photo_url)
                return None

            return _parse_json_response(content)

    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error analyzing photo {photo_url}: {e.response.status_code}")
        return None
    except httpx.RequestError as e:
        if isinstance(e.__cause__, socket.gaierror):
            logger.warning("Network error contacting OpenAI (DNS resolution failed).")
        logger.warning(f"Request error analyzing photo {photo_url}: {e}")
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

    penalty_map = {
        "flipper_gray_palette": 5,
        "lvp_flooring": 5,
        "staged_furniture": 3,
        "over_staged": 2,
        "dark_interior": 5,
        "deferred_maintenance": 7,
        "ultra_wide_distortion": 2,
        "visible_damage": 6,
        "worn_finishes": 4,
    }
    bonus_map = {
        "natural_light_visible": 4,
        "outdoor_greenery": 3,
        "original_details": 4,
        "warm_materials": 3,
        "high_ceilings_visible": 3,
        "open_layout": 2,
        "quality_kitchen": 3,
    }

    penalty = sum(penalty_map.get(flag, 0) for flag in all_red_flags)
    bonus = sum(bonus_map.get(flag, 0) for flag in all_highlights)
    composite = composite + bonus - penalty

    # Confidence based on photos analyzed
    photos_analyzed = len(analyses)
    if photos_analyzed >= 3:
        confidence = "high"
    elif photos_analyzed == 2:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "score": max(0, min(100, int(round(composite)))),
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

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured")
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
