import textwrap

from app.core.config import settings
from app.models.listing import PropertyListing
from app.services.advanced_matching import PropertyMatcher
from app.services.criteria_config import load_buyer_criteria


def _write_test_criteria(tmp_path):
    criteria = textwrap.dedent(
        """
        hard_filters:
          price_max: 3500000
          bedrooms_min: 3
          bathrooms_min: 2
          sqft_min: 1600
          neighborhoods:
            - Noe Valley
        soft_caps:
          price_soft: 3000000
        weights:
          natural_light: 10
          outdoor_space: 9
          character_soul: 8
          kitchen_quality: 7
          location_quiet: 6
          office_space: 4
        nlp_signals:
          positive:
            light:
              keywords:
                - natural light
                - sunny
                - bright
              weight: 1.0
            outdoor:
              keywords:
                - deck
                - garden
              weight: 1.0
            character:
              keywords:
                - victorian
                - charm
              weight: 1.0
            quality:
              keywords:
                - restored
                - original
              weight: 1.0
            kitchen:
              keywords:
                - "chef's kitchen"
                - gas range
              weight: 1.0
          negative:
            dark:
              keywords:
                - dark
                - dim
                - cozy
              weight: 0.6
            location_noise:
              keywords:
                - busy street
              weight: 0.6
            weak_outdoor:
              keywords:
                - juliet balcony
              weight: 0.8
            flipper:
              keywords:
                - flip
                - flipper
              weight: 0.7
            condition:
              keywords:
                - needs work
              weight: 0.6
        alerts:
          new_listing:
            score_threshold: 76
          price_drop:
            percent_threshold: 5
          dom_stale:
            days: 45
        """
    ).strip()

    path = tmp_path / "criteria.yaml"
    path.write_text(criteria, encoding="utf-8")
    return path


def _configure_criteria(tmp_path):
    path = _write_test_criteria(tmp_path)
    original_path = settings.BUYER_CRITERIA_PATH
    settings.BUYER_CRITERIA_PATH = str(path)
    load_buyer_criteria.cache_clear()
    return original_path


def _restore_criteria(original_path):
    settings.BUYER_CRITERIA_PATH = original_path
    load_buyer_criteria.cache_clear()


def test_score_listing_rejects_hard_filters(db_session, tmp_path):
    original_path = _configure_criteria(tmp_path)
    try:
        listing = PropertyListing(
            listing_id="Z999",
            address="999 Demo St, San Francisco, CA",
            price=4000000,
            beds=3,
            baths=2.0,
            sqft=1700,
            neighborhood="Noe Valley",
            property_type="condo",
            url="https://example.com/listing/Z999",
            description="Sunny home with deck and chef's kitchen.",
        )
        db_session.add(listing)
        db_session.commit()
        db_session.refresh(listing)

        matcher = PropertyMatcher(criteria=None, db=db_session)
        assert matcher.score_listing(listing) is False
    finally:
        _restore_criteria(original_path)


def test_score_listing_sets_explainability(db_session, tmp_path):
    original_path = _configure_criteria(tmp_path)
    try:
        listing = PropertyListing(
            listing_id="Z1000",
            address="1000 Charm St, San Francisco, CA",
            price=2200000,
            beds=3,
            baths=2.0,
            sqft=1800,
            neighborhood="Noe Valley",
            property_type="single_family",
            url="https://example.com/listing/Z1000",
            description=(
                "Sunny Victorian with natural light, restored details, and a garden deck. "
                "Chef's kitchen with gas range and bright living room."
            ),
        )
        db_session.add(listing)
        db_session.commit()
        db_session.refresh(listing)

        matcher = PropertyMatcher(criteria=None, db=db_session)
        assert matcher.score_listing(listing) is True
        assert listing.score_points is not None
        assert isinstance(listing.score_percent, str) and listing.score_percent.endswith("%")
        assert listing.score_tier in {"Exceptional", "Strong", "Interesting", "Pass"}
        assert listing.top_positives
        assert "Natural light" in listing.top_positives
        assert isinstance(listing.signals, dict)
    finally:
        _restore_criteria(original_path)


def test_score_listing_blocks_dark_without_light(db_session, tmp_path):
    original_path = _configure_criteria(tmp_path)
    try:
        listing = PropertyListing(
            listing_id="Z2000",
            address="2000 Shadow Ln, San Francisco, CA",
            price=2100000,
            beds=3,
            baths=2.0,
            sqft=1700,
            neighborhood="Noe Valley",
            property_type="condo",
            url="https://example.com/listing/Z2000",
            description="Cozy and dark interior with dim lighting.",
        )
        db_session.add(listing)
        db_session.commit()
        db_session.refresh(listing)

        matcher = PropertyMatcher(criteria=None, db=db_session)
        assert matcher.score_listing(listing) is False
    finally:
        _restore_criteria(original_path)
