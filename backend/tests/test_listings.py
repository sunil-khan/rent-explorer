def test_get_all_listings(client):
    resp = client.get("/listings")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert all("listing_id" in item for item in data)


def test_bbox_filter(client):
    # Bbox covering only Test-East area (24.8-25.0, 60.15-60.25)
    resp = client.get("/listings?min_lng=24.8&min_lat=60.15&max_lng=25.0&max_lat=60.25")
    assert resp.status_code == 200
    data = resp.json()
    ids = {item["listing_id"] for item in data}
    # T001, T002, T004, T005 are in this bbox; T003 is at 24.70 (outside)
    assert "T003" not in ids
    assert "T001" in ids


def test_rent_filter(client):
    resp = client.get("/listings?rent_min=900&rent_max=1500")
    assert resp.status_code == 200
    data = resp.json()
    for item in data:
        assert item["rent_eur"] is not None
        assert 900 <= item["rent_eur"] <= 1500


def test_rooms_filter(client):
    resp = client.get("/listings?rooms=2")
    assert resp.status_code == 200
    data = resp.json()
    for item in data:
        assert item["rooms"] == 2


def test_property_type_filter(client):
    resp = client.get("/listings?property_type=studio")
    assert resp.status_code == 200
    data = resp.json()
    for item in data:
        assert item["property_type"] == "studio"


def test_eur_per_m2_computed(client):
    resp = client.get("/listings")
    data = resp.json()
    t001 = next(item for item in data if item["listing_id"] == "T001")
    assert t001["eur_per_m2"] == 20.0  # 1000 / 50.0


def test_null_rent_has_null_eur_per_m2(client):
    resp = client.get("/listings")
    data = resp.json()
    t004 = next(item for item in data if item["listing_id"] == "T004")
    assert t004["rent_eur"] is None
    assert t004["eur_per_m2"] is None


def test_null_size_has_null_eur_per_m2(client):
    resp = client.get("/listings")
    data = resp.json()
    t005 = next(item for item in data if item["listing_id"] == "T005")
    assert t005["size_m2"] is None
    assert t005["eur_per_m2"] is None


def test_listings_near(client):
    # Search near T001 (24.94, 60.17), 2km radius
    resp = client.get("/listings/near?lat=60.17&lng=24.94&radius_m=2000")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    # Should be sorted by distance
    distances = [item["distance_m"] for item in data]
    assert distances == sorted(distances)
    # First result should be very close to search point
    assert data[0]["distance_m"] < 100


def test_listings_near_no_results(client):
    # Search in empty area far from any test listing
    resp = client.get("/listings/near?lat=61.0&lng=25.0&radius_m=100")
    assert resp.status_code == 200
    assert resp.json() == []
