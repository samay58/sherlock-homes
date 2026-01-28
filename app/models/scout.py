"""Scout model for managing sophisticated property search profiles."""

from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship

from .base import Base


class Scout(Base):
    """Scout configuration for automated property matching and alerts."""

    __tablename__ = "scouts"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)  # Natural language description

    # Link to criteria
    criteria_id = Column(
        Integer, ForeignKey("criteria.id", ondelete="SET NULL"), nullable=True
    )

    # Scout configuration
    is_active = Column(Boolean, default=True, nullable=False)
    alert_frequency = Column(
        String(20), default="daily"
    )  # "instant", "daily", "weekly"
    min_match_score = Column(Float, default=60.0)  # Minimum score to trigger alert
    max_results_per_alert = Column(Integer, default=10)

    # Search parameters
    search_keywords = Column(JSON, nullable=True)  # Additional keywords to search
    search_neighborhoods = Column(
        JSON, nullable=True
    )  # Specific neighborhoods to focus on

    # Alert preferences
    alert_email = Column(Boolean, default=True)
    alert_sms = Column(Boolean, default=False)
    alert_webhook = Column(String(500), nullable=True)  # Optional webhook URL

    # Tracking
    last_run = Column(DateTime, nullable=True)
    last_alert_sent = Column(DateTime, nullable=True)
    total_matches_found = Column(Integer, default=0)
    total_alerts_sent = Column(Integer, default=0)

    # Seen listings (to avoid duplicates in alerts)
    seen_listing_ids = Column(
        JSON, nullable=True, default=list
    )  # List of listing IDs already alerted

    # Scout learning/feedback
    positive_feedback_listings = Column(
        JSON, nullable=True, default=list
    )  # Liked listings
    negative_feedback_listings = Column(
        JSON, nullable=True, default=list
    )  # Rejected listings

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="scouts")
    criteria = relationship("Criteria", backref="scouts")
    scout_runs = relationship(
        "ScoutRun", back_populates="scout", cascade="all, delete-orphan"
    )


class ScoutRun(Base):
    """Track individual scout execution runs."""

    __tablename__ = "scout_runs"

    id = Column(Integer, primary_key=True)
    scout_id = Column(
        Integer, ForeignKey("scouts.id", ondelete="CASCADE"), nullable=False
    )

    # Run details
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")  # "running", "completed", "failed"

    # Results
    listings_evaluated = Column(Integer, default=0)
    matches_found = Column(Integer, default=0)
    new_matches = Column(Integer, default=0)  # Not previously seen
    alerts_sent = Column(Integer, default=0)

    # Match details
    matched_listings = Column(JSON, nullable=True)  # List of {listing_id, score, url}
    top_score = Column(Float, nullable=True)
    average_score = Column(Float, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Relationships
    scout = relationship("Scout", back_populates="scout_runs")
