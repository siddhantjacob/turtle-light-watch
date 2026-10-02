"""
06_extract_noise_boxes.py — monthly light for ~30 EMPTY places at sea, to measure the noise floor.

Idea: after removing the background, a box of open sea should show NO trend. In practice each box
will show a small random slope (sensor noise, the odd ship). The spread of those slopes tells us how
big a trend has to be before we believe it. That spread is the "noise floor".

How the boxes are chosen (reproducible):
  * candidate centres on a 0.5-degree grid over the north-west Bay of Bengal
  * keep only boxes with NO land within 50 km (MODIS water mask), so coastal light can't leak in
  * pick up to 30 of them at random with a fixed seed (same boxes every run)

Output: data/processed/noise_boxes_monthly.csv  (same columns as controls_monthly.csv, kind = "noise")
"""
import os
import random
from pathlib import Path

import ee
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
ee.Initialize(project=os.getenv("EE_PROJECT"))

SCALE_M = 463.83
HALF_DEG = 0.1                       # same 22 x 22 km size as the background boxes
CLEAR_KM = 50                        # no land within this distance
N_BOXES, SEED = 30, 42

viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
water = (ee.ImageCollection("MODIS/006/MOD44W")
         .sort("system:time_start", False).first().select("water_mask"))
land = water.eq(0)

# ---------------------------------------------------------------- 1. candidate boxes
def rect(x, y):
    return ee.Geometry.Rectangle([x - HALF_DEG, y - HALF_DEG, x + HALF_DEG, y + HALF_DEG],
                                 proj="EPSG:4326", geodesic=False)

cands = [(round(85.5 + 0.5 * i, 2), round(17.0 + 0.5 * j, 2)) for i in range(8) for j in range(8)]
fc = ee.FeatureCollection([ee.Feature(rect(x, y).buffer(CLEAR_KM * 1000), {"x": x, "y": y})
                           for x, y in cands])
land_near = land.reduceRegions(collection=fc, reducer=ee.Reducer.max(), scale=1000).getInfo()
open_sea = [(f["properties"]["x"], f["properties"]["y"]) for f in land_near["features"]
            if f["properties"].get("max") == 0]
random.Random(SEED).shuffle(open_sea)
chosen = sorted(open_sea[:N_BOXES])
print(f"{len(open_sea)} of {len(cands)} candidates have no land within {CLEAR_KM} km; using {len(chosen)}.")

# Noise shrinks when you average more pixels, so a fair floor must come from regions the SAME SIZE as
# the ones we test. Around each sea point we draw circles matching our beach circles (1, 5, 10 km)
# and one of 2.8 km radius (~25 km2, the size of a typical coast-stretch zone).
NOISE_RADII_KM = [1, 2.8, 5, 10]
regions = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point([x, y]).buffer(r * 1000),
               {"kind": "noise", "region_id": f"N{i:02d}", "radius_km": r, "x": x, "y": y})
    for i, (x, y) in enumerate(chosen) for r in NOISE_RADII_KM])
reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)


# ---------------------------------------------------------------- 2. monthly statistics
def month_stats(img):
    stack = img.select("avg_rad").rename("all").addBands(img.select("cf_cvg").rename("cvg"))
    stats = stack.reduceRegions(collection=regions, reducer=reducer, scale=SCALE_M, tileScale=2)
    month = img.date().format("YYYY-MM")
    return stats.map(lambda f: ee.Feature(None, f.toDictionary().set("month", month)))


rows = []
for year in range(2014, 2027):
    out = ee.FeatureCollection(viirs.filterDate(f"{year}-01-01", f"{year + 1}-01-01")
                               .map(month_stats)).flatten().getInfo()["features"]
    rows += [f["properties"] for f in out]
    print(f"{year}: {len(out)} rows")

df = pd.DataFrame(rows).rename(columns={"all_mean": "rad_all", "cvg_mean": "cloudfree_nights",
                                        "all_count": "n_px_all"})
df = df[["month", "kind", "region_id", "radius_km", "rad_all", "cloudfree_nights", "n_px_all", "x", "y"]]
out_path = ROOT / "data" / "processed" / "noise_boxes_monthly.csv"
df.sort_values(["region_id", "month"]).to_csv(out_path, index=False)
print(f"\nSaved {len(df)} rows to {out_path.relative_to(ROOT)}")
