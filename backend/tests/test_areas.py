def test_areas_stats_structure(client):
    resp = client.get("/areas/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 2  # T01 and T02

    for feature in data["features"]:
        assert feature["type"] == "Feature"
        assert "geometry" in feature
        props = feature["properties"]
        assert "area_code" in props
        assert "area_name" in props
        assert "listing_count" in props
        assert "median_rent" in props
        assert "median_eur_per_m2" in props


def test_areas_stats_values(client):
    resp = client.get("/areas/stats")
    data = resp.json()
    features = {f["properties"]["area_code"]: f["properties"] for f in data["features"]}

    # Test-West (T01): only T003 (rent=600, size=30, eur_m2=20.0)
    assert features["T01"]["listing_count"] == 1
    assert features["T01"]["median_rent"] == 600

    # Test-East (T02): T001(1000/50=20), T002(2000/80=25), T004(NULL rent), T005(NULL size)
    # listing_count = 4 (all points in area)
    assert features["T02"]["listing_count"] == 4
    # median_rent from T001=1000, T002=2000, T005=800 (T004 excluded, NULL rent)
    # sorted non-null rents: 800, 1000, 2000 → median = 1000
    assert features["T02"]["median_rent"] == 1000
