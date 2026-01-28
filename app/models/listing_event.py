"""Listing event and snapshot models for change tracking."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class ListingSnapshot(Base):
    """Snapshot of listing fields used for change detection."""

    __tablename__ = "listing_snapshots"

    id = Column(Integer, primary_key=True)
    listing_id = Column(
        Integer,
        ForeignKey("property_listings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    snapshot_hash = Column(String(64), index=True, nullable=False)
    snapshot_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    listing = relationship("PropertyListing", backref="snapshots")


class ListingEvent(Base):
    """Event representing a meaningful listing change."""

    __tablename__ = "listing_events"

    id = Column(Integer, primary_key=True)
    listing_id = Column(
        Integer,
        ForeignKey("property_listings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_type = Column(String(50), index=True, nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    listing = relationship("PropertyListing", backref="events")
