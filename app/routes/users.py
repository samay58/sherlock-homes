"""API routes for user weight learning."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import (UserWeightsResponse, WeightLearningSummary,
                              WeightRecalculationResult, WeightResetResponse)
from app.services.weight_learning import (get_learning_summary,
                                          get_user_weights,
                                          recalculate_user_weights,
                                          reset_user_weights)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/weights", response_model=UserWeightsResponse)
def get_weights(user_id: int, db: Session = Depends(get_db)):
    """Get current weights for a user.

    Returns base weights from config, learned multipliers from feedback,
    and effective weights (base * learned multiplier).
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    result = get_user_weights(user_id, db)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"]
        )

    return UserWeightsResponse(**result)


@router.get("/{user_id}/weights/summary", response_model=WeightLearningSummary)
def get_weights_summary(user_id: int, db: Session = Depends(get_db)):
    """Get a human-readable summary of learned preferences.

    Shows which criteria have been strengthened or weakened based on
    the user's like/dislike feedback, with insight text.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    result = get_learning_summary(user_id, db)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"]
        )

    return WeightLearningSummary(**result)


@router.post("/{user_id}/weights/recalculate", response_model=WeightRecalculationResult)
def recalculate_weights(user_id: int, db: Session = Depends(get_db)):
    """Recalculate weights from all feedback.

    Processes all like/dislike feedback for the user and updates their
    learned weights accordingly. Requires minimum signal counts before
    making changes.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    result = recalculate_user_weights(user_id, db)

    return WeightRecalculationResult(
        weights_updated=result.weights_updated,
        message=result.message,
        total_likes=result.total_likes,
        total_dislikes=result.total_dislikes,
        criteria_adjusted=result.criteria_adjusted,
    )


@router.delete("/{user_id}/weights", response_model=WeightResetResponse)
def reset_weights(user_id: int, db: Session = Depends(get_db)):
    """Reset learned weights to defaults.

    Clears all learned weight adjustments for the user, reverting to
    the base weights from the config file.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    success = reset_user_weights(user_id, db)

    if success:
        return WeightResetResponse(
            success=True, message="Learned weights reset to defaults"
        )
    else:
        return WeightResetResponse(success=False, message="Failed to reset weights")
