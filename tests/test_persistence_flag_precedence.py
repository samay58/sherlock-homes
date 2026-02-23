from sqlalchemy.orm import sessionmaker

from app.models.listing import PropertyListing
from app.services import persistence


def test_provider_fields_not_overwritten_by_flags(db_session, monkeypatch):
    """
    Providers can set boolean columns directly (e.g. `has_doorman_keywords=True` from a
    scraped amenities section). NLP-derived `flags` should not overwrite explicit fields
    with a default `False`.
    """

    test_session_local = sessionmaker(
        bind=db_session.get_bind(), autocommit=False, autoflush=False
    )
    monkeypatch.setattr(persistence, "SessionLocal", test_session_local)

    url = "https://streeteasy.com/building/138-frost-street-brooklyn/1/rental/123"
    persistence.upsert_listings(
        [
            {
                "source": "streeteasy",
                "source_listing_id": url,
                "url": url,
                "address": "138 Frost St #1, Brooklyn, NY 11211",
                "has_doorman_keywords": True,
                "flags": {"doorman_concierge": False},
            }
        ]
    )

    db_session.expire_all()
    listing = (
        db_session.query(PropertyListing)
        .filter_by(source="streeteasy", source_listing_id=url)
        .first()
    )
    assert listing is not None
    assert listing.has_doorman_keywords is True

