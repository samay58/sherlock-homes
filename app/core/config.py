import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database - defaults to SQLite for local development
    # Use PostgreSQL URL for Docker/production (set in .env.docker)
    DATABASE_URL: str = Field(default="sqlite:///./sherlock.db")
    RUN_DB_MIGRATIONS_ON_STARTUP: bool = Field(default=False)  # Only for PostgreSQL/Alembic

    ZENROWS_API_KEY: Optional[str] = Field(default=None)
    WALKSCORE_API_KEY: Optional[str] = Field(default=None)
    WALKSCORE_HOST: Optional[str] = Field(default=None)

    # Claude Vision API (for visual property scoring)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    VISUAL_SCORING_ENABLED: bool = Field(default=True)
    VISUAL_PHOTOS_SAMPLE_SIZE: int = Field(default=3)  # Number of photos to analyze per listing

    # Alerting (email/SMS/iMessage)
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_USE_TLS: bool = Field(default=True)
    ALERT_EMAIL_FROM: Optional[str] = Field(default=None)
    ALERT_EMAIL_TO: Optional[str] = Field(default=None)

    IMESSAGE_ENABLED: bool = Field(default=False)
    IMESSAGE_TARGET: Optional[str] = Field(default=None)

    TWILIO_ACCOUNT_SID: Optional[str] = Field(default=None)
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default=None)
    TWILIO_FROM_NUMBER: Optional[str] = Field(default=None)
    TWILIO_TO_NUMBER: Optional[str] = Field(default=None)

    # JWT Settings
    # Use `openssl rand -hex 32` to generate a suitable secret key
    SECRET_KEY: str = Field(default="PLEASE_CHANGE_ME_IN_ENV") 
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Ingestion Settings
    INGESTION_INTERVAL_HOURS: int = Field(default=6)  # How often to run data ingestion
    ENABLE_AUTO_INGESTION: bool = Field(default=True)  # Whether to enable automatic ingestion
    MAX_PAGES: int = Field(default=25)  # Max search pages to fetch per ingestion run
    MAX_DETAIL_CALLS: int = Field(default=200)  # Max property detail calls per ingestion run

    # Location Settings
    SEARCH_LOCATION: str = Field(default="san-francisco-ca")  # Zillow location slug (e.g., "dolores-heights-san-francisco-ca")

    # Search Filter Settings
    SEARCH_PRICE_MIN: int = Field(default=800000)  # Minimum property price
    SEARCH_PRICE_MAX: Optional[int] = Field(default=None)  # Maximum property price (None = no limit)
    SEARCH_BEDS_MIN: int = Field(default=2)  # Minimum bedrooms
    SEARCH_BATHS_MIN: float = Field(default=1.5)  # Minimum bathrooms
    SEARCH_SQFT_MIN: int = Field(default=1000)  # Minimum square footage

    class Config:
        # Load environment variables from a .env file if it exists
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings() 
