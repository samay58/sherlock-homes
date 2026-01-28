"""User feedback model for listing preferences."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from .base import Base


class FeedbackType(str, PyEnum):
    """Feedback types for user preferences."""

    LIKE = "like"
    DISLIKE = "dislike"
    NEUTRAL = "neutral"


class ListingFeedback(Base):
    """User feedback on a listing (like/dislike/neutral)."""

    __tablename__ = "listing_feedback"

    id = Column(Integer, primary_key=True)
    listing_id = Column(
        Integer,
        ForeignKey("property_listings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    feedback_type = Column(String(20), nullable=False)  # 'like', 'dislike', 'neutral'
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One feedback per user per listing
    __table_args__ = (
        UniqueConstraint("listing_id", "user_id", name="uq_listing_user_feedback"),
    )

    listing = relationship("PropertyListing", backref="feedbacks")
    user = relationship("User", backref="feedbacks")
