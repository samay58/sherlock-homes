"""Initialize test data for development.

Creates a test user and sample search criteria if they don't exist.
Run this script once after database migrations to enable API functionality.
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.criteria import Criteria

def init_test_data():
    """Create test user and search criteria if they don't exist."""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.id == 1).first()
        if existing_user:
            print("✓ Test user already exists (id=1)")
        else:
            # Create test user with a simple hashed password (for development only!)
            test_user = User(
                id=1,
                email="test@sherlock.app",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJNJ6pV7S7e"  # "password"
            )
            db.add(test_user)
            db.commit()
            print("✓ Created test user (id=1, email=test@sherlock.app)")
            print("  Password: 'password' (development only!)")

        # Check if search criteria exists for test user
        existing_criteria = db.query(Criteria).filter(
            Criteria.user_id == 1
        ).first()

        if existing_criteria:
            print("✓ Search criteria already exists for test user")
        else:
            # Create sample search criteria with comprehensive feature preferences
            criteria = Criteria(
                user_id=1,
                name="SF Luxury Properties",
                is_active=True,
                # Quantitative filters
                price_min=1000000,
                price_max=5000000,
                beds_min=3,
                baths_min=2.0,
                sqft_min=1500,
                # Essential features (required)
                require_natural_light=True,
                require_outdoor_space=False,
                require_parking=False,
                require_view=False,
                require_high_ceilings=False,
                require_updated_systems=False,
                require_home_office=False,
                require_storage=False,
                # Deal preferences
                include_price_reduced=True,
                include_new_listings=True,
                # Red flags to avoid
                avoid_busy_streets=True,
                avoid_north_facing_only=True,
                avoid_basement_units=True,
                # Feature weights for scoring
                feature_weights={
                    "natural_light": 10,
                    "view": 9,
                    "outdoor_space": 8,
                    "updated_systems": 7,
                    "high_ceilings": 7,
                    "parking": 6,
                    "open_floor_plan": 6,
                    "home_office": 5,
                    "architectural_details": 5,
                    "storage": 4,
                    "tech_ready": 4,
                    "luxury": 3,
                    "designer": 3
                }
            )
            db.add(criteria)
            db.commit()
            print("✓ Created search criteria for test user")
            print(f"  Name: {criteria.name}")
            print(f"  Price range: ${int(criteria.price_min):,} - ${int(criteria.price_max):,}")
            print(f"  Required features: natural_light")
            print(f"  Feature weights: {len(criteria.feature_weights)} categories")

        print("\n✅ Test data initialization complete!")
        print("   You can now use the /matches endpoint with user_id=1")

    except Exception as e:
        print(f"❌ Error initializing test data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    init_test_data()
