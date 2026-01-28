"""API routes for listing feedback."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.feedback import ListingFeedback
from app.models.listing import PropertyListing
from app.schemas.feedback import (FeedbackCreate, FeedbackResponse,
                                  FeedbackSummary, FeedbackType)
from app.services.criteria import TEST_USER_ID

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/{listing_id}", response_model=FeedbackResponse)
def create_or_update_feedback(
    listing_id: int,
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    user_id: int = TEST_USER_ID,  # TODO: Get from auth
):
    """Create or update feedback for a listing."""
    # Verify listing exists
    listing = db.get(PropertyListing, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )

    # Check for existing feedback
    existing = db.execute(
        select(ListingFeedback).where(
            ListingFeedback.listing_id == listing_id, ListingFeedback.user_id == user_id
        )
    ).scalar_one_or_none()

    if existing:
        # Update existing feedback
        existing.feedback_type = feedback.feedback_type.value
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new feedback
        new_feedback = ListingFeedback(
            listing_id=listing_id,
            user_id=user_id,
            feedback_type=feedback.feedback_type.value,
        )
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        return new_feedback


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    listing_id: int,
    db: Session = Depends(get_db),
    user_id: int = TEST_USER_ID,  # TODO: Get from auth
):
    """Delete feedback for a listing (revert to no opinion)."""
    existing = db.execute(
        select(ListingFeedback).where(
            ListingFeedback.listing_id == listing_id, ListingFeedback.user_id == user_id
        )
    ).scalar_one_or_none()

    if existing:
        db.delete(existing)
        db.commit()


@router.get("/user/{user_id}", response_model=List[FeedbackResponse])
def get_user_feedback(
    user_id: int,
    db: Session = Depends(get_db),
    feedback_type: FeedbackType | None = None,
):
    """Get all feedback for a user, optionally filtered by type."""
    query = select(ListingFeedback).where(ListingFeedback.user_id == user_id)
    if feedback_type:
        query = query.where(ListingFeedback.feedback_type == feedback_type.value)
    query = query.order_by(ListingFeedback.updated_at.desc())

    results = db.scalars(query).all()
    return list(results)


@router.get("/listing/{listing_id}", response_model=FeedbackSummary)
def get_listing_feedback_summary(
    listing_id: int,
    db: Session = Depends(get_db),
    user_id: int = TEST_USER_ID,  # TODO: Get from auth
):
    """Get feedback summary for a listing including current user's feedback."""
    # Get counts by type
    counts = db.execute(
        select(
            ListingFeedback.feedback_type,
            func.count(ListingFeedback.id).label("count"),  # pylint: disable=not-callable
        )
        .where(ListingFeedback.listing_id == listing_id)
        .group_by(ListingFeedback.feedback_type)
    ).all()

    summary = FeedbackSummary(listing_id=listing_id)
    for feedback_type, count in counts:
        if feedback_type == "like":
            summary.likes = count
        elif feedback_type == "dislike":
            summary.dislikes = count
        elif feedback_type == "neutral":
            summary.neutrals = count

    # Get current user's feedback
    user_feedback = db.execute(
        select(ListingFeedback.feedback_type).where(
            ListingFeedback.listing_id == listing_id, ListingFeedback.user_id == user_id
        )
    ).scalar_one_or_none()

    if user_feedback:
        summary.user_feedback = FeedbackType(user_feedback)

    return summary
