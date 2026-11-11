import pytest
from fastapi.testclient import TestClient

import lakes
from main import app

SQUARE = {"type": "Polygon", "coordinates": [[[-93.0, 45.0], [-92.99, 45.0],
          [-92.99, 45.01], [-93.0, 45.01], [-93.0, 45.0]]]}
# Same square with a hole in the middle (an island)
WITH_ISLAND = {"type": "Polygon", "coordinates": [
    SQUARE["coordinates"][0],
    [[-92.997, 45.003], [-92.993, 45.003], [-92.993, 45.007],
     [-92.997, 45.007], [-92.997, 45.003]]]}
MULTI = {"type": "MultiPolygon", "coordinates": [SQUARE["coordinates"], SQUARE["coordinates"]]}


def row(**kw):
    d = {"name": "Test Lake", "display_name": "Test Lake, MN", "osm_id": 1,
         "lat": "45.005", "lon": "-92.995", "category": "natural", "type": "water",
         "geojson": SQUARE}
    d.update(kw)
    return d


def test_square_area_is_about_0_87_km2():
    out = lakes.parse_results([row()])
    assert out[0]["area_km2"] == pytest.approx(0.87, rel=0.02)
    assert out[0]["bbox"] == [-93.0, 45.0, -92.99, 45.01]


def test_island_is_subtracted():
    full = lakes.area_km2(SQUARE)
    holed = lakes.area_km2(WITH_ISLAND)
    assert holed == pytest.approx(full * (1 - 0.004 * 0.004 / (0.01 * 0.01)), rel=0.01)


def test_multipolygon_sums_parts():
    assert lakes.area_km2(MULTI) == pytest.approx(2 * lakes.area_km2(SQUARE))


def test_drops_points_and_non_water():
    pt = row(geojson={"type": "Point", "coordinates": [0, 0]})
    road = row(type="residential", category="highway")
    assert lakes.parse_results([pt, road]) == []


def test_accepts_old_json_class_key():
    r = row(type="unknown")
    del r["category"]
    r["class"] = "water"
    assert len(lakes.parse_results([r])) == 1


def test_sorted_largest_first():
    big = {"type": "Polygon", "coordinates": [[[-93, 45], [-92.9, 45],
           [-92.9, 45.1], [-93, 45.1], [-93, 45]]]}
    out = lakes.parse_results([row(name="Small"), row(name="Big", geojson=big)])
    assert [l["name"] for l in out] == ["Big", "Small"]


def test_api_endpoint_and_validation(monkeypatch):
    async def fake(q):
        return lakes.parse_results([row(name=q)])
    monkeypatch.setattr(lakes, "search_lakes", fake)
    c = TestClient(app)
    assert c.get("/api/health").json() == {"ok": True}
    res = c.get("/api/lakes/search", params={"q": "Harriet"}).json()
    assert res["results"][0]["name"] == "Harriet"
    assert c.get("/api/lakes/search", params={"q": "x"}).status_code == 422
