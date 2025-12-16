from app.models.listing import PropertyListing


def test_ping(client):
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_listings_list_and_detail(client, db_session):
    # Seed a listing
    l = PropertyListing(
        listing_id="Z123",
        address="123 Demo St, San Francisco, CA",
        price=1500000,
        beds=3,
        baths=2.0,
        sqft=1400,
        property_type="condo",
        url="https://example.com/listing/Z123",
        photos=["https://example.com/p1.jpg"],
    )
    db_session.add(l)
    db_session.commit()
    db_session.refresh(l)

    # GET /listings returns our record
    r = client.get("/listings")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert any(item["id"] == l.id for item in items)

    # GET /listings/{id} returns the record
    r2 = client.get(f"/listings/{l.id}")
    assert r2.status_code == 200
    detail = r2.json()
    assert detail["id"] == l.id
    assert detail["address"].startswith("123 Demo St")
