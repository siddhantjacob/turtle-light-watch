"""
08_annual_crosscheck.py — M5 check: do we get the same answer from NOAA's ANNUAL product?

Why: our main result uses MONTHLY data with our own background correction (minus the offshore boxes).
If that correction were wrong, our trends would be wrong. The annual composites (V2.1 / V2.2) are made
differently by NOAA/EOG: 12-month median, fires and boats removed, and background set to ZERO
("average_masked"). If both routes rank the coast stretches similarly, our correction didn't invent the
result.

Steps
  1. Pre-flight: list which years each annual collection really contains (lesson from script 04).
  2. For each year 2014-2025 take the annual image (V2.2 if present, else V2.1).
  3. Mean "average_masked" radiance per coast stretch and per 5 km beach circle.
  4. Theil-Sen slope + Mann-Kendall per region, as in script 07.
  5. Compare with script 07's monthly-based slopes: Spearman rank correlation (1 = identical order).

Output: data/processed/annual_crosscheck.csv
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import ee
import geopandas as gpd
import pandas as pd
import pymannkendall as mk
from dotenv import load_dotenv
from scipy.stats import spearmanr, theilslopes

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
load_dotenv(ROOT / ".env")
ee.Initialize(project=os.getenv("EE_PROJECT"))

COLLECTIONS = ["NOAA/VIIRS/DNB/ANNUAL_V22", "NOAA/VIIRS/DNB/ANNUAL_V21"]   # first = preferred
BAND = "average_masked"
SCALE_M = 463.83
NESTING = {"S011": "Rushikulya", "S041": "Devi", "S066": "Gahirmatha island", "S068": "Gahirmatha mainland"}

# ---------------------------------------------------------------- 1. pre-flight: which years exist?
source = {}
for cid in reversed(COLLECTIONS):            # V21 first, then V22 overwrites where both exist
    stamps = ee.ImageCollection(cid).aggregate_array("system:time_start").getInfo()
    years = sorted({datetime.fromtimestamp(t / 1000, tz=timezone.utc).year for t in stamps})
    print(f"{cid}: years {years}")
    for y in years:
        source[y] = cid
use_years = [y for y in range(2014, 2026) if y in source]
print(f"\nUsing {len(use_years)} years: " + ", ".join(f"{y} ({source[y][-3:]})" for y in use_years))
missing = [y for y in range(2014, 2026) if y not in source]
if missing:
    print(f"Missing years (no annual product): {missing}")

# ---------------------------------------------------------------- 2. regions
def to_ee(path, kind, id_col, keep=None):
    gdf = gpd.read_file(path)
    if keep is not None:
        gdf = gdf[keep(gdf)]
    return [ee.Feature(ee.Geometry(f["geometry"]), {"kind": kind, "region_id": f["properties"][id_col]})
            for f in json.loads(gdf.to_json())["features"]]

sites_dir = ROOT / "data" / "sites"
regions = ee.FeatureCollection(
    to_ee(sites_dir / "site_buffers.geojson", "site", "site_id", keep=lambda g: g.radius_km == 5)
    + to_ee(sites_dir / "coast_segments.geojson", "segment", "seg_id"))

# ---------------------------------------------------------------- 3. mean radiance per region per year
rows = []
for y in use_years:
    img = (ee.ImageCollection(source[y]).filterDate(f"{y}-01-01", f"{y + 1}-01-01")
           .first().select(BAND))
    fc = img.reduceRegions(collection=regions, reducer=ee.Reducer.mean(), scale=SCALE_M)
    for f in fc.getInfo()["features"]:
        p = f["properties"]
        rows.append({"year": y, "source": source[y][-3:], "kind": p["kind"],
                     "region_id": p["region_id"], "rad_annual": p.get("mean")})
    print(f"{y}: done")
ann = pd.DataFrame(rows)
ann.to_csv(PROC / "annual_crosscheck_values.csv", index=False)

# A jump between product versions would show up here as a step in the coast-wide median
print("\nCoast-wide median radiance per year (watch for a step where the version changes):")
print(ann[ann.kind == "segment"].groupby(["year", "source"]).rad_annual.median().round(2).to_string())

# ---------------------------------------------------------------- 4. trends
out = []
for (kind, rid), g in ann.dropna(subset=["rad_annual"]).groupby(["kind", "region_id"]):
    g = g.sort_values("year")
    if len(g) < 8:
        continue
    ts = theilslopes(g.rad_annual.values, g.year.values)
    out.append({"kind": kind, "region_id": rid, "slope_annual_product": ts[0],
                "p_annual_product": mk.original_test(g.rad_annual.values).p})
cc = pd.DataFrame(out)

# ---------------------------------------------------------------- 5. compare with our monthly-based result
tr = pd.read_csv(PROC / "trends.csv")
ours = tr[(tr.period == "annual") & (tr.measure == "rad_all_corr")
          & (((tr.kind == "segment")) | ((tr.kind == "site") & (tr.radius_km == 5)))]
cc = cc.merge(ours[["kind", "region_id", "slope", "verdict"]].rename(
    columns={"slope": "slope_ours", "verdict": "verdict_ours"}), on=["kind", "region_id"], how="left")
cc.to_csv(PROC / "annual_crosscheck.csv", index=False)

seg = cc[cc.kind == "segment"].copy()
rho, p = spearmanr(seg.slope_ours, seg.slope_annual_product)
print(f"\nCOAST STRETCHES: rank agreement between the two routes (Spearman rho) = {rho:.2f} (p = {p:.3g}, n = {len(seg)})")
print("  1.0 = identical order, 0 = unrelated. Above ~0.7 = the two routes broadly agree.")

seg["rank_ours"] = seg.slope_ours.rank(ascending=False).astype(int)
seg["rank_annual"] = seg.slope_annual_product.rank(ascending=False).astype(int)
nest = seg[seg.region_id.isin(NESTING)].assign(beach=lambda d: d.region_id.map(NESTING))
print("\nNesting stretches: rank of 99 (1 = fastest brightening) by each route")
print(nest[["region_id", "beach", "rank_ours", "rank_annual", "slope_ours", "slope_annual_product"]]
      .round(3).to_string(index=False))

print("\nBeach circles (5 km): slope by each route (nW/cm2/sr per year)")
print(cc[cc.kind == "site"][["region_id", "slope_ours", "slope_annual_product", "p_annual_product"]]
      .round(3).to_string(index=False))
print("\nSaved data/processed/annual_crosscheck.csv")
