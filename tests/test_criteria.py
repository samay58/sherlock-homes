def test_get_and_update_criteria_for_test_user(client):
    # Initial GET should auto-create default criteria for test user
    r = client.get("/criteria/test-user")
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == 1
    assert data["is_active"] is True
    cid = data["id"]

    # Update some fields
    payload = {
        "name": "My Criteria",
        "price_min": 1000000,
        "price_max": 2000000,
        "beds_min": 3,
        "baths_min": 2.0,
        "sqft_min": 1200,
        "require_natural_light": True,
        "require_high_ceilings": False,
        "require_outdoor_space": True,
    }
    r2 = client.post("/criteria/test-user", json=payload)
    assert r2.status_code == 200
    updated = r2.json()
    assert updated["id"] == cid
    assert updated["price_min"] == 1000000
    assert updated["beds_min"] == 3
    assert updated["require_natural_light"] is True
