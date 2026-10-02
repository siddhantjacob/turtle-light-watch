"""
04_extract_controls.py — monthly light for CONTROL areas (the "freezer" test).

If our beaches brighten, is it real, or would ANY place look brighter because of the sensor or
processing? Controls answer that. Two kinds:

  1. Far-offshore boxes (OFF_S, OFF_C, OFF_N), ~100 km out in the Bay of Bengal, 22 x 22 km each.
     There should be (almost) no light there; ships add a little noise.
     -> Their trend = sensor drift + noise. Any beach trend smaller than this is not real.

  2. DARK_LAND: land in our Odisha box that the satellite product itself classed as UNLIT in 2013
     (VIIRS annual V2.1, median_masked = 0), excluding the 10 km circles around our beaches.
     -> Its trend = general rural brightening (e.g. village electrification) + sensor effects.
     We pick these pixels using 2013, a year OUTSIDE our 2014-2026 trend period, to avoid
     "regression to the mean" (pixels chosen for being unusually dark tend to look brighter later
     even if nothing changed).

Output: data/processed/controls_monthly.csv  (same columns as monthly_light.csv)
"""
import json
import os
from pathlib import Path

import ee
import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
ee.Initialize(project=os.getenv("EE_PROJECT"))

SCALE_M = 463.83
BBOX = [84.60, 19.05, 87.60, 21.70]
OFFSHORE = {"OFF_S": (85.75, 18.75),   # ~100 km off Rushikulya
            "OFF_C": (87.05, 19.30),   # ~100 km off Devi
            "OFF_N": (87.70, 20.05)}   # ~100 km off Gahirmatha
HALF_DEG = 0.1                          # box half-width (~11 km)

viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
water = (ee.ImageCollection("MODIS/006/MOD44W")
         .sort("system:time_start", False).first().select("water_mask"))
land = water.eq(0)

# Pixels the 2013 annual product called unlit (background set to 0 in median_masked)
# V2.1 annual composites definitely cover 2013 (the V2.2 collection returned nothing for 2013)
v2013 = (ee.ImageCollection("NOAA/VIIRS/DNB/ANNUAL_V21")
         .filterDate("2013-01-01", "2014-01-01").first())

# Pre-flight check: make sure every input image exists BEFORE the long loop (fail fast, clear message)
for name, img in [("MOD44W water mask", water), ("VIIRS annual 2013", v2013)]:
    info = ee.Algorithms.If(img, ee.Image(img).bandNames(), None).getInfo()
    if info is None:
        raise SystemExit(f"Pre-flight failed: {name} returned no image.")
    print(f"Pre-flight OK: {name} bands = {info}")

dark_land = land.And(v2013.select("median_masked").eq(0))

# Region for DARK_LAND = our box minus the 10 km beach circles
buf = gpd.read_file(ROOT / "data" / "sites" / "site_buffers.geojson")
circles = json.loads(buf[buf.radius_km == 10].dissolve().to_json())["features"][0]["geometry"]
box = ee.Geometry.Rectangle(BBOX, proj="EPSG:4326", geodesic=False)
dark_region = box.difference(ee.Geometry(circles), maxError=100)

features = [ee.Feature(ee.Geometry.Rectangle([x - HALF_DEG, y - HALF_DEG, x + HALF_DEG, y + HALF_DEG],
                                             proj="EPSG:4326", geodesic=False),
                       {"kind": "control", "region_id": k, "radius_km": 0, "use": "all"})
            for k, (x, y) in OFFSHORE.items()]
features.append(ee.Feature(dark_region, {"kind": "control", "region_id": "DARK_LAND",
                                         "radius_km": 0, "use": "dark"}))
regions = ee.FeatureCollection(features)
reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)


def month_stats(img):
    rad = img.select("avg_rad")
    stack = (rad.rename("all")
             .addBands(rad.updateMask(dark_land).rename("dark"))
             .addBands(img.select("cf_cvg").rename("cvg")))
    stats = stack.reduceRegions(collection=regions, reducer=reducer, scale=SCALE_M, tileScale=4)
    month = img.date().format("YYYY-MM")
    return stats.map(lambda f: ee.Feature(None, f.toDictionary().set("month", month)))


rows = []
for year in range(2014, 2027):
    fc = ee.FeatureCollection(viirs.filterDate(f"{year}-01-01", f"{year + 1}-01-01")
                              .map(month_stats)).flatten()
    feats = fc.getInfo()["features"]
    rows += [f["properties"] for f in feats]
    print(f"{year}: {len(feats)} rows")

df = pd.DataFrame(rows)
# Offshore boxes use every pixel; DARK_LAND uses only the 2013-unlit land pixels
is_dark = df.region_id == "DARK_LAND"
df["rad_all"] = df["all_mean"].where(~is_dark, df["dark_mean"])
df["n_px_all"] = df["all_count"].where(~is_dark, df["dark_count"])
df = df.rename(columns={"cvg_mean": "cloudfree_nights"})
df = df[["month", "kind", "region_id", "radius_km", "rad_all", "cloudfree_nights", "n_px_all"]]
df = df.sort_values(["region_id", "month"])

out = ROOT / "data" / "processed" / "controls_monthly.csv"
df.to_csv(out, index=False)
print(f"\nSaved {len(df)} rows to {out.relative_to(ROOT)}")
print("\nPixels per control region (median over months):")
print(df.groupby("region_id").n_px_all.median().to_string())
