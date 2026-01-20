"""Schemas for listing feedback."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FeedbackType(str, Enum):
    """Feedback types for user preferences."""

    LIKE = "like"
    DISLIKE = "dislike"
    NEUTRAL = "neutral"


class FeedbackCreate(BaseModel):
    """Schema for creating/updating feedback."""

    feedback_type: FeedbackType


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""

    id: int
    listing_id: int
    user_id: int
    feedback_type: FeedbackType
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FeedbackSummary(BaseModel):
    """Summary of feedback for a listing."""

    listing_id: int
    likes: int = 0
    dislikes: int = 0
    neutrals: int = 0
    user_feedback: Optional[FeedbackType] = None
