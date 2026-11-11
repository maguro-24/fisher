"""Lake search: name -> outline polygon (GeoJSON) via OpenStreetMap Nominatim.

Pure Python (no shapely/geopandas) so it installs on any recent Python.
Heavy geometry work arrives later, in its own step.
"""
import math
import time

import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "fisher-app/0.1 (personal project)"  # Nominatim requires one
WATER_TYPES = {"water", "lake", "reservoir", "pond", "river", "riverbank", "bay"}
CACHE_TTL_S = 3600
_cache: dict[str, tuple[float, list[dict]]] = {}


def _rings_area(rings, kx, ky, lon0, lat0) -> float:
    """Shoelace area (km^2) of one polygon: outer ring minus holes."""
    def ring_area(ring):
        pts = [((x - lon0) * kx, (y - lat0) * ky) for x, y in ring]
        s = 0.0
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            s += x1 * y2 - x2 * y1
        return abs(s) / 2

    outer, *holes = rings
    return ring_area(outer) - sum(ring_area(h) for h in holes)


def _polygons(geometry: dict) -> list:
    return [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]


def bounds(geometry: dict) -> list[float]:
    xs, ys = [], []
    for poly in _polygons(geometry):
        for x, y in poly[0]:
            xs.append(x)
            ys.append(y)
    return [min(xs), min(ys), max(xs), max(ys)]


def area_km2(geometry: dict) -> float:
    minx, miny, maxx, maxy = bounds(geometry)
    lon0, lat0 = (minx + maxx) / 2, (miny + maxy) / 2
    kx = 111.320 * math.cos(math.radians(lat0))  # km per degree of longitude
    ky = 110.574                                  # km per degree of latitude
    return sum(_rings_area(p, kx, ky, lon0, lat0) for p in _polygons(geometry))


def parse_results(results: list[dict]) -> list[dict]:
    """Keep polygon water bodies, add area/bbox, largest first."""
    lakes = []
    for r in results:
        gj = r.get("geojson")
        if not gj or gj.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        category = r.get("category") or r.get("class")  # jsonv2 vs json
        if r.get("type") not in WATER_TYPES and category != "water":
            continue
        km2 = area_km2(gj)
        lakes.append({
            "name": r.get("name") or (r.get("display_name") or "").split(",")[0],
            "display_name": r.get("display_name"),
            "osm_id": r.get("osm_id"),
            "center": {"lat": float(r["lat"]), "lon": float(r["lon"])},
            "bbox": bounds(gj),
            "area_km2": round(km2, 3),
            "geometry": gj,
        })
    return sorted(lakes, key=lambda l: -l["area_km2"])


async def search_lakes(query: str, limit: int = 8) -> list[dict]:
    key = query.strip().lower()
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_S:
        return hit[1]
    params = {"q": query, "format": "jsonv2", "polygon_geojson": 1,
              "limit": limit, "polygon_threshold": 0.00005}
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": USER_AGENT}) as c:
        resp = await c.get(NOMINATIM_URL, params=params)
        resp.raise_for_status()
        lakes = parse_results(resp.json())
    _cache[key] = (time.time(), lakes)
    return lakes
