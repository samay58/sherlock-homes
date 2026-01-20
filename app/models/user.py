from sqlalchemy import String, Integer, Column, JSON
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Learned weights from feedback (bounded weight learning)
    # Structure: { "criterion_name": { "multiplier": float, "signal_count": int, "last_updated": str }, ... }
    learned_weights = Column(JSON, nullable=True)

    # Relationships
    criteria = relationship("Criteria", back_populates="user", cascade="all, delete-orphan")
    scouts = relationship("Scout", back_populates="user", cascade="all, delete-orphan") 