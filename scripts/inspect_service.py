"""Inspect the MN DNR bathymetry service and locate Lake Harriet.

Run from the project root (venv active):  python scripts/inspect_service.py
Prints the real schemas and any Harriet records, and saves them to
data/raw/service_inspection.json so later steps only use verified names.
"""
import json
from pathlib import Path

import httpx

BASE = ("https://enterprise.gisdata.mn.gov/aghost/rest/services/"
        "us_mn_state_dnr/water_lake_bathymetry/MapServer")
OUT = Path("data/raw")
OUT.mkdir(parents=True, exist_ok=True)

# 0-2 are vector layers, 4 is the mapdates table. 3 is a raster (no fields).
TARGETS = {0: "contours", 1: "outline", 2: "metadata", 4: "mapdates"}


def get(url, **params):
    params["f"] = "json"
    r = httpx.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"{url}: {data['error']}")
    return data


def name_fields(fields):
    return [f["name"] for f in fields
            if f["type"] == "esriFieldTypeString" and "name" in f["name"].lower()]


report = {}
for lid, role in TARGETS.items():
    meta = get(f"{BASE}/{lid}")
    fields = meta.get("fields", [])
    entry = {"role": role, "name": meta["name"],
             "geometryType": meta.get("geometryType"),
             "fields": [(f["name"], f["type"]) for f in fields]}
    print(f"\n=== Layer {lid}: {meta['name']} ({entry['geometryType']}) ===")
    for n, t in entry["fields"]:
        print(f"  {n:28s} {t}")

    nf = name_fields(fields)
    entry["name_fields"] = nf
    if not nf:
        print("  (no obvious lake-name field; match Harriet by its DOW number instead)")
    else:
        where = " OR ".join(f"UPPER({c}) LIKE '%HARRIET%'" for c in nf)
        res = get(f"{BASE}/{lid}/query", where=where, outFields="*", returnGeometry="false")
        rows = [f["attributes"] for f in res.get("features", [])]
        entry["harriet_rows"] = rows
        print(f"  Harriet matches: {len(rows)}")
        for row in rows[:10]:
            print("   ", row)
    report[lid] = entry

(OUT / "service_inspection.json").write_text(json.dumps(report, indent=2, default=str))
print("\nSaved data/raw/service_inspection.json")
