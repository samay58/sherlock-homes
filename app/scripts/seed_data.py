"""
Seed script to populate database with sample listings for testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.listing import PropertyListing
from app.models.criteria import UserCriteria
import random

def create_sample_listings(db: Session):
    """Create sample property listings with varied characteristics"""
    
    # SF neighborhoods for realistic addresses
    neighborhoods = [
        "Pacific Heights", "Marina", "Mission", "SOMA", "Nob Hill",
        "Russian Hill", "Castro", "Hayes Valley", "Potrero Hill", "Bernal Heights"
    ]
    
    streets = [
        "California St", "Fillmore St", "Valencia St", "Market St", "Powell St",
        "Lombard St", "Castro St", "Hayes St", "18th St", "Cortland Ave"
    ]
    
    sample_listings = []
    
    for i in range(30):
        # Generate varied properties
        beds = random.choice([0, 1, 2, 3, 4, 5])
        baths = random.choice([1, 1.5, 2, 2.5, 3, 3.5])
        sqft = random.randint(400, 4000)
        price = random.randint(500000, 5000000)
        
        # Make price somewhat correlated with size
        price = int(price * (sqft / 1500))
        
        listing = PropertyListing(
            id=str(uuid4()),
            zillow_id=f"test_{i:04d}",
            address=f"{random.randint(100, 9999)} {random.choice(streets)}, {random.choice(neighborhoods)}, SF",
            price=price,
            beds=beds,
            baths=baths,
            sqft=sqft,
            year_built=random.randint(1900, 2024),
            lot_size=random.randint(1000, 8000),
            property_type=random.choice(["Single Family", "Condo", "Townhouse", "Multi Family"]),
            description=f"Beautiful {beds} bedroom, {baths} bath home in {random.choice(neighborhoods)}",
            photos=[
                f"https://picsum.photos/seed/{i}/800/600",
                f"https://picsum.photos/seed/{i+100}/800/600",
                f"https://picsum.photos/seed/{i+200}/800/600"
            ],
            # Varied feature flags for interesting filtering
            natural_light_flag=random.choice([True, False, False]),  # 33% chance
            high_ceilings_flag=random.choice([True, False, False, False]),  # 25% chance
            outdoor_space_flag=random.choice([True, False]),  # 50% chance
            modern_kitchen_flag=random.choice([True, False, False]),  # 33% chance
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add some special properties
        if i < 3:  # First 3 are premium with all features
            listing.natural_light_flag = True
            listing.high_ceilings_flag = True
            listing.outdoor_space_flag = True
            listing.modern_kitchen_flag = True
            listing.price = random.randint(3000000, 5000000)
            
        if i % 10 == 0:  # Every 10th is newly listed
            listing.is_new = True
            
        if i % 7 == 0:  # Some have price reductions
            listing.price_reduction = True
            
        sample_listings.append(listing)
    
    # Add listings to database
    for listing in sample_listings:
        existing = db.query(PropertyListing).filter_by(zillow_id=listing.zillow_id).first()
        if not existing:
            db.add(listing)
    
    db.commit()
    print(f"✓ Created {len(sample_listings)} sample listings")

def create_test_user_criteria(db: Session):
    """Create default criteria for test user"""
    
    # Check if criteria already exists
    existing = db.query(UserCriteria).filter_by(user_id="test-user").first()
    
    if not existing:
        criteria = UserCriteria(
            id=str(uuid4()),
            user_id="test-user",
            min_price=800000,
            max_price=2500000,
            min_beds=2,
            min_baths=1.5,
            min_sqft=1000,
            max_sqft=3000,
            natural_light_priority=True,
            high_ceilings_priority=False,
            outdoor_space_priority=True,
            modern_kitchen_priority=True,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(criteria)
        db.commit()
        print("✓ Created test user criteria")
    else:
        print("✓ Test user criteria already exists")

def main():
    """Run the seed script"""
    print("\n🌱 Seeding database with sample data...\n")
    
    db = SessionLocal()
    try:
        create_sample_listings(db)
        create_test_user_criteria(db)
        
        # Print summary
        total_listings = db.query(PropertyListing).count()
        with_natural_light = db.query(PropertyListing).filter_by(natural_light_flag=True).count()
        with_outdoor_space = db.query(PropertyListing).filter_by(outdoor_space_flag=True).count()
        
        print(f"\n📊 Database Summary:")
        print(f"   Total Listings: {total_listings}")
        print(f"   With Natural Light: {with_natural_light}")
        print(f"   With Outdoor Space: {with_outdoor_space}")
        print(f"\n✅ Seeding complete!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()