"""
Batch Visual Scoring Script for Sherlock Homes

Analyzes property photos using OpenAI Vision and updates database with visual scores.

Usage:
    # Inside Docker container:
    python -m app.scripts.analyze_visual_scores

    # With options:
    python -m app.scripts.analyze_visual_scores --all        # Re-analyze all listings
    python -m app.scripts.analyze_visual_scores --limit 10   # Analyze only 10 listings
    python -m app.scripts.analyze_visual_scores --top-matches 10  # Analyze top 10 matches
    python -m app.scripts.analyze_visual_scores --dry-run    # Preview without API calls
"""

import argparse
import asyncio
import logging
# Setup path for script execution
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.listing import PropertyListing
from app.services.advanced_matching import PropertyMatcher
from app.services.visual_scoring import (analyze_listing_photos,
                                         compute_photos_hash, get_visual_tier,
                                         should_reanalyze)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def analyze_batch(
    db: Session,
    analyze_all: bool = False,
    limit: Optional[int] = None,
    top_matches: Optional[int] = None,
    dry_run: bool = False,
) -> dict:
    """
    Run batch visual analysis on listings.

    Args:
        db: Database session
        analyze_all: If True, re-analyze all listings regardless of cache
        limit: Maximum number of listings to analyze
        dry_run: If True, preview what would be analyzed without calling API

    Returns:
        Stats dict with counts
    """
    stats = {
        "total_listings": 0,
        "with_photos": 0,
        "needs_analysis": 0,
        "analyzed": 0,
        "skipped": 0,
        "failed": 0,
        "estimated_cost": None,
    }

    listings = []
    if top_matches:
        matcher = PropertyMatcher(criteria=None, db=db, include_intelligence=False)
        scored = matcher.find_matches(limit=top_matches, min_score=0.0)
        listings = [listing for listing, _, _ in scored]
    else:
        query = (
            select(PropertyListing)
            .where(PropertyListing.photos.isnot(None))
            .order_by(PropertyListing.id)
        )

        if limit:
            query = query.limit(limit * 2)  # Get extra to account for skips

        listings = db.scalars(query).all()

    stats["total_listings"] = len(listings)
    if top_matches:
        logger.info("Selected top %d matches for visual scoring", top_matches)

    cost_per_image = settings.OPENAI_VISION_COST_PER_IMAGE_USD
    sample_size = settings.VISUAL_PHOTOS_SAMPLE_SIZE

    # Filter to those needing analysis
    to_analyze = []
    for listing in listings:
        if not listing.photos:
            continue

        stats["with_photos"] += 1

        if not analyze_all:
            # Check if we should re-analyze
            needs_it = should_reanalyze(
                existing_hash=listing.photos_hash,
                existing_analyzed_at=listing.visual_analyzed_at,
                new_photos=listing.photos,
            )
            if not needs_it:
                stats["skipped"] += 1
                continue

        to_analyze.append(listing)
        stats["needs_analysis"] += 1
        if cost_per_image is not None:
            photo_count = min(len(listing.photos or []), sample_size)
            stats["estimated_cost"] = (stats["estimated_cost"] or 0.0) + (
                photo_count * cost_per_image
            )

        if limit and len(to_analyze) >= limit:
            break

    logger.info(
        f"Found {stats['total_listings']} listings, {stats['with_photos']} with photos"
    )
    logger.info(
        f"Need to analyze: {len(to_analyze)}, skipping {stats['skipped']} (cached)"
    )
    if stats["estimated_cost"] is not None:
        logger.info(f"Estimated cost: ${stats['estimated_cost']:.2f}")
    else:
        logger.info("Estimated cost: n/a (set OPENAI_VISION_COST_PER_IMAGE_USD)")

    if dry_run:
        logger.info("DRY RUN - not making API calls")
        for listing in to_analyze[:10]:
            photo_count = len(listing.photos) if listing.photos else 0
            logger.info(
                f"  Would analyze: {listing.address[:50]} ({photo_count} photos)"
            )
        if len(to_analyze) > 10:
            logger.info(f"  ... and {len(to_analyze) - 10} more")
        return stats

    # Check API key
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured. Set it in .env.local file.")
        return stats

    running_cost = 0.0

    # Analyze each listing
    for i, listing in enumerate(to_analyze):
        try:
            logger.info(
                f"[{i+1}/{len(to_analyze)}] Analyzing: {listing.address[:50]}..."
            )
            if cost_per_image is not None:
                photo_count = min(len(listing.photos or []), sample_size)
                listing_cost = photo_count * cost_per_image
                running_cost += listing_cost
                logger.info(
                    f"  Est. cost: ${listing_cost:.2f} (running ${running_cost:.2f})"
                )

            # Run visual analysis
            result = await analyze_listing_photos(
                photos=listing.photos, listing_id=listing.listing_id or str(listing.id)
            )

            if result.get("score") is not None:
                # Update database
                listing.visual_quality_score = result["score"]
                listing.visual_assessment = {
                    "dimensions": result.get("dimensions", {}),
                    "red_flags": result.get("red_flags", []),
                    "highlights": result.get("highlights", []),
                    "photos_analyzed": result.get("photos_analyzed", 0),
                    "confidence": result.get("confidence", "unknown"),
                }
                listing.photos_hash = compute_photos_hash(listing.photos)
                listing.visual_analyzed_at = datetime.now(timezone.utc)

                db.commit()

                tier = get_visual_tier(result["score"])
                logger.info(f"  Score: {result['score']} ({tier})")
                stats["analyzed"] += 1
            else:
                logger.warning(f"  No score returned")
                stats["failed"] += 1

            # Rate limit: ~1 request per second
            await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"  Error: {e}")
            stats["failed"] += 1
            db.rollback()

    logger.info(f"\nComplete! Analyzed: {stats['analyzed']}, Failed: {stats['failed']}")
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Batch visual scoring for property listings"
    )
    parser.add_argument(
        "--all", action="store_true", help="Re-analyze all listings (ignore cache)"
    )
    parser.add_argument("--limit", type=int, help="Maximum listings to analyze")
    parser.add_argument(
        "--top-matches", type=int, help="Analyze top N matches (uses scoring engine)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without API calls"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("SHERLOCK HOMES VISUAL SCORING")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        stats = asyncio.run(
            analyze_batch(
                db=db,
                analyze_all=args.all,
                limit=args.limit,
                top_matches=args.top_matches,
                dry_run=args.dry_run,
            )
        )

        # Print summary
        print("\n" + "=" * 40)
        print("SUMMARY")
        print("=" * 40)
        print(f"Total listings:    {stats['total_listings']}")
        print(f"With photos:       {stats['with_photos']}")
        print(f"Analyzed:          {stats['analyzed']}")
        print(f"Skipped (cached):  {stats['skipped']}")
        print(f"Failed:            {stats['failed']}")
        if stats["estimated_cost"] is not None:
            print(f"Estimated cost:    ${stats['estimated_cost']:.2f}")
        else:
            print("Estimated cost:    n/a")

    finally:
        db.close()


if __name__ == "__main__":
    main()
