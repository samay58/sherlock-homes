"""Bounded weight learning service for personalized scoring.

Adjusts per-user scoring weights based on like/dislike feedback signals,
with bounded deltas to prevent overfitting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feedback import FeedbackType, ListingFeedback
from app.models.listing import PropertyListing
from app.models.user import User
from app.services.criteria_config import load_buyer_criteria

logger = logging.getLogger(__name__)

# Learning algorithm constants
DELTA_PER_SIGNAL = 0.05  # Weight change per feedback signal
MAX_DELTA_PER_RECALC = 0.5  # Maximum change per recalculation (out of 10-point scale)
MIN_SIGNALS_BEFORE_LEARNING = 5  # Minimum likes + dislikes before adjusting weights
MIN_LIKES_REQUIRED = 3  # Need at least this many likes
MIN_DISLIKES_REQUIRED = 2  # Need at least this many dislikes
WEIGHT_MULTIPLIER_MIN = 0.5  # Minimum multiplier (50% of base weight)
WEIGHT_MULTIPLIER_MAX = 2.0  # Maximum multiplier (200% of base weight)
TOP_CRITERIA_COUNT = 3  # Number of top criteria to boost/penalize per feedback


@dataclass
class LearnedWeight:
    """Represents a learned weight adjustment for a criterion."""

    multiplier: float  # Multiplier to apply to base weight (1.0 = no change)
    signal_count: int  # Number of signals that contributed to this weight
    last_updated: str  # ISO timestamp of last update

    def to_dict(self) -> Dict[str, Any]:
        return {
            "multiplier": round(self.multiplier, 3),
            "signal_count": self.signal_count,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearnedWeight":
        return cls(
            multiplier=data.get("multiplier", 1.0),
            signal_count=data.get("signal_count", 0),
            last_updated=data.get("last_updated", datetime.utcnow().isoformat()),
        )


@dataclass
class WeightLearningResult:
    """Result of a weight learning calculation."""

    weights_updated: bool
    message: str
    total_likes: int
    total_dislikes: int
    criteria_adjusted: List[str]
    learned_weights: Dict[str, LearnedWeight]


def _get_listing_top_criteria(
    listing: PropertyListing, count: int = TOP_CRITERIA_COUNT
) -> List[Tuple[str, float]]:
    """Get the top N scoring criteria for a listing.

    Returns list of (criterion_name, weighted_score) tuples, sorted by contribution.
    """
    feature_scores = listing.feature_scores or {}
    contributions = []

    for criterion, data in feature_scores.items():
        if isinstance(data, dict):
            score = data.get("score", 0)
            weight = data.get("weight", 0)
            # Calculate contribution: (score/10) * weight
            contribution = (score / 10.0) * weight if weight > 0 else 0
            contributions.append((criterion, contribution))

    # Sort by contribution descending
    contributions.sort(key=lambda x: x[1], reverse=True)
    return contributions[:count]


def _get_listing_bottom_criteria(
    listing: PropertyListing, count: int = TOP_CRITERIA_COUNT
) -> List[Tuple[str, float]]:
    """Get the bottom N scoring criteria for a listing.

    Returns criteria with lowest scores (potential dealbreakers).
    """
    feature_scores = listing.feature_scores or {}
    scores = []

    for criterion, data in feature_scores.items():
        if isinstance(data, dict):
            score = data.get("score", 0)
            weight = data.get("weight", 0)
            if weight > 0:  # Only consider criteria with weight
                scores.append((criterion, score))

    # Sort by score ascending (lowest first)
    scores.sort(key=lambda x: x[1])
    return scores[:count]


def _apply_bounded_delta(
    current_multiplier: float,
    delta: float,
    min_bound: float = WEIGHT_MULTIPLIER_MIN,
    max_bound: float = WEIGHT_MULTIPLIER_MAX,
) -> float:
    """Apply a delta to a weight multiplier, respecting bounds.

    Args:
        current_multiplier: Current weight multiplier
        delta: Change to apply (positive or negative)
        min_bound: Minimum allowed multiplier
        max_bound: Maximum allowed multiplier

    Returns:
        New multiplier, clamped to bounds
    """
    new_multiplier = current_multiplier + delta
    return max(min_bound, min(max_bound, new_multiplier))


def calculate_weight_updates(
    user_id: int, db: Session
) -> Tuple[Dict[str, float], WeightLearningResult]:
    """Calculate weight updates based on user feedback.

    Analyzes all feedback for a user and calculates weight adjustments:
    - For liked listings: boost weights of top-scoring criteria
    - For disliked listings: reduce weights of top-scoring criteria

    Args:
        user_id: User ID to calculate weights for
        db: Database session

    Returns:
        Tuple of (weight_deltas, result) where weight_deltas maps
        criterion -> delta to apply to multiplier
    """
    # Get all feedback with listings
    feedback_query = (
        select(ListingFeedback, PropertyListing)
        .join(PropertyListing, ListingFeedback.listing_id == PropertyListing.id)
        .where(ListingFeedback.user_id == user_id)
    )
    feedback_rows = db.execute(feedback_query).all()

    likes = []
    dislikes = []

    for feedback, listing in feedback_rows:
        if not listing.feature_scores:
            continue  # Skip listings without scores

        if feedback.feedback_type == FeedbackType.LIKE.value:
            likes.append(listing)
        elif feedback.feedback_type == FeedbackType.DISLIKE.value:
            dislikes.append(listing)

    total_signals = len(likes) + len(dislikes)

    # Check minimum signal requirements
    if total_signals < MIN_SIGNALS_BEFORE_LEARNING:
        return {}, WeightLearningResult(
            weights_updated=False,
            message=f"Need {MIN_SIGNALS_BEFORE_LEARNING} total signals before learning (have {total_signals})",
            total_likes=len(likes),
            total_dislikes=len(dislikes),
            criteria_adjusted=[],
            learned_weights={},
        )

    if len(likes) < MIN_LIKES_REQUIRED:
        return {}, WeightLearningResult(
            weights_updated=False,
            message=f"Need at least {MIN_LIKES_REQUIRED} likes before learning (have {len(likes)})",
            total_likes=len(likes),
            total_dislikes=len(dislikes),
            criteria_adjusted=[],
            learned_weights={},
        )

    if len(dislikes) < MIN_DISLIKES_REQUIRED:
        return {}, WeightLearningResult(
            weights_updated=False,
            message=f"Need at least {MIN_DISLIKES_REQUIRED} dislikes before learning (have {len(dislikes)})",
            total_likes=len(likes),
            total_dislikes=len(dislikes),
            criteria_adjusted=[],
            learned_weights={},
        )

    # Calculate deltas
    criteria_deltas: Dict[str, float] = {}
    criteria_signal_counts: Dict[str, int] = {}

    # Boost criteria that appear in top scores of liked listings
    for listing in likes:
        top_criteria = _get_listing_top_criteria(listing)
        for criterion, _ in top_criteria:
            criteria_deltas[criterion] = (
                criteria_deltas.get(criterion, 0) + DELTA_PER_SIGNAL
            )
            criteria_signal_counts[criterion] = (
                criteria_signal_counts.get(criterion, 0) + 1
            )

    # Penalize criteria that appear in top scores of disliked listings
    # (user dislikes listings where these criteria scored high)
    for listing in dislikes:
        top_criteria = _get_listing_top_criteria(listing)
        for criterion, _ in top_criteria:
            criteria_deltas[criterion] = (
                criteria_deltas.get(criterion, 0) - DELTA_PER_SIGNAL
            )
            criteria_signal_counts[criterion] = (
                criteria_signal_counts.get(criterion, 0) + 1
            )

    # Clamp deltas to max per recalculation
    for criterion in criteria_deltas:
        criteria_deltas[criterion] = max(
            -MAX_DELTA_PER_RECALC, min(MAX_DELTA_PER_RECALC, criteria_deltas[criterion])
        )

    criteria_adjusted = [c for c, d in criteria_deltas.items() if abs(d) > 0.001]

    # Build learned weights structure
    learned_weights = {}
    for criterion, delta in criteria_deltas.items():
        if abs(delta) > 0.001:
            learned_weights[criterion] = LearnedWeight(
                multiplier=_apply_bounded_delta(1.0, delta),
                signal_count=criteria_signal_counts.get(criterion, 0),
                last_updated=datetime.utcnow().isoformat(),
            )

    return criteria_deltas, WeightLearningResult(
        weights_updated=True,
        message=f"Calculated weight adjustments from {len(likes)} likes and {len(dislikes)} dislikes",
        total_likes=len(likes),
        total_dislikes=len(dislikes),
        criteria_adjusted=criteria_adjusted,
        learned_weights=learned_weights,
    )


def recalculate_user_weights(user_id: int, db: Session) -> WeightLearningResult:
    """Recalculate and persist learned weights for a user.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        WeightLearningResult with outcome details
    """
    user = db.get(User, user_id)
    if not user:
        return WeightLearningResult(
            weights_updated=False,
            message="User not found",
            total_likes=0,
            total_dislikes=0,
            criteria_adjusted=[],
            learned_weights={},
        )

    deltas, result = calculate_weight_updates(user_id, db)

    if not result.weights_updated:
        return result

    # Get existing weights or start fresh
    existing_weights = user.learned_weights or {}

    # Apply deltas to existing multipliers
    updated_weights = {}
    for criterion, delta in deltas.items():
        existing = existing_weights.get(criterion, {})
        current_multiplier = existing.get("multiplier", 1.0)
        new_multiplier = _apply_bounded_delta(current_multiplier, delta)

        updated_weights[criterion] = {
            "multiplier": round(new_multiplier, 3),
            "signal_count": result.learned_weights[criterion].signal_count,
            "last_updated": datetime.utcnow().isoformat(),
        }

    # Preserve weights for criteria not in this update
    for criterion, data in existing_weights.items():
        if criterion not in updated_weights:
            updated_weights[criterion] = data

    # Persist
    user.learned_weights = updated_weights
    db.commit()

    logger.info(
        f"Updated weights for user {user_id}: {len(updated_weights)} criteria, "
        f"adjusted: {result.criteria_adjusted}"
    )

    # Update result with persisted weights
    result.learned_weights = {
        c: LearnedWeight.from_dict(d) for c, d in updated_weights.items()
    }

    return result


def get_user_weights(user_id: int, db: Session) -> Dict[str, Any]:
    """Get effective weights for a user.

    Combines base weights from config with learned multipliers.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Dict with base_weights, learned_multipliers, and effective_weights
    """
    user = db.get(User, user_id)
    if not user:
        return {"error": "User not found"}

    # Load base weights from config
    config = load_buyer_criteria()
    base_weights = dict(config.weights)

    # Get learned multipliers
    learned_raw = user.learned_weights or {}
    learned_multipliers = {
        criterion: data.get("multiplier", 1.0)
        for criterion, data in learned_raw.items()
    }

    # Calculate effective weights
    effective_weights = {}
    for criterion, base_weight in base_weights.items():
        multiplier = learned_multipliers.get(criterion, 1.0)
        effective_weights[criterion] = round(base_weight * multiplier, 2)

    # Get signal counts
    signal_counts = {
        criterion: data.get("signal_count", 0)
        for criterion, data in learned_raw.items()
    }

    return {
        "user_id": user_id,
        "base_weights": base_weights,
        "learned_multipliers": learned_multipliers,
        "effective_weights": effective_weights,
        "signal_counts": signal_counts,
        "total_signals": sum(signal_counts.values()),
    }


def get_effective_weights_dict(user_id: int, db: Session) -> Dict[str, float]:
    """Get just the effective weights dict for use in PropertyMatcher.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Dict mapping criterion -> effective weight value
    """
    result = get_user_weights(user_id, db)
    if "error" in result:
        # Fall back to base weights
        config = load_buyer_criteria()
        return dict(config.weights)
    return result["effective_weights"]


def reset_user_weights(user_id: int, db: Session) -> bool:
    """Reset learned weights for a user back to defaults.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        True if reset successful, False if user not found
    """
    user = db.get(User, user_id)
    if not user:
        return False

    user.learned_weights = None
    db.commit()
    logger.info(f"Reset learned weights for user {user_id}")
    return True


def get_learning_summary(user_id: int, db: Session) -> Dict[str, Any]:
    """Get a human-readable summary of learned preferences.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Summary dict with preference insights
    """
    weights_data = get_user_weights(user_id, db)
    if "error" in weights_data:
        return weights_data

    learned_multipliers = weights_data.get("learned_multipliers", {})
    signal_counts = weights_data.get("signal_counts", {})

    # Identify strengthened preferences (multiplier > 1.1)
    boosted = [(c, m) for c, m in learned_multipliers.items() if m > 1.1]
    boosted.sort(key=lambda x: x[1], reverse=True)

    # Identify weakened preferences (multiplier < 0.9)
    reduced = [(c, m) for c, m in learned_multipliers.items() if m < 0.9]
    reduced.sort(key=lambda x: x[1])

    # Map criterion keys to human-readable labels
    from app.services.scoring.primitives import CRITERION_LABELS

    summary = {
        "user_id": user_id,
        "total_signals": weights_data.get("total_signals", 0),
        "preferences_learned": len(learned_multipliers),
        "strengthened_preferences": [
            {
                "criterion": CRITERION_LABELS.get(c, c),
                "boost_percent": round((m - 1.0) * 100),
                "signals": signal_counts.get(c, 0),
            }
            for c, m in boosted[:5]
        ],
        "weakened_preferences": [
            {
                "criterion": CRITERION_LABELS.get(c, c),
                "reduction_percent": round((1.0 - m) * 100),
                "signals": signal_counts.get(c, 0),
            }
            for c, m in reduced[:5]
        ],
    }

    # Generate insight text
    if boosted:
        top_boost = CRITERION_LABELS.get(boosted[0][0], boosted[0][0])
        summary["insight"] = (
            f"Your feedback suggests '{top_boost}' matters more to you than average."
        )
    elif reduced:
        top_reduce = CRITERION_LABELS.get(reduced[0][0], reduced[0][0])
        summary["insight"] = (
            f"Your feedback suggests '{top_reduce}' matters less to you than average."
        )
    else:
        summary["insight"] = "Not enough feedback yet to identify clear preferences."

    return summary
