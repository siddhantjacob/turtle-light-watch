"""
03_extract_monthly_light.py — monthly night-light for every beach circle and coast stretch, 2014-2026.

What it does
  For every month of VIIRS (Jan 2014 onwards) it averages the radiance (nW/cm2/sr) inside:
    * each beach circle (4 sites x 1/5/10 km), measured three ways:
        all  = every pixel (land + sea)
        land = land pixels only
        sea  = sea pixels only  (boat-light check)
    * each of the 99 coast stretches (already land-only polygons from script 02)
  It also records cf_cvg = how many cloud-free nights went into that month (data quality).

Land vs sea comes from the MODIS 250 m water mask (MOD44W, 2015), which, unlike our
coastline outline, includes islands such as Abdul Kalam Island.

Output: data/processed/monthly_light.csv   (one row per region per month)
        figures/m3_monthly_sites.png       (first look at the three beaches)

Run time: a few minutes (one Earth Engine request per year).
"""
import json
import os
from pathlib import Path

import ee
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
ee.Initialize(project=os.getenv("EE_PROJECT"))

VIIRS_ID = "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"
SCALE_M = 463.83          # native VIIRS pixel size
FIRST_YEAR, LAST_YEAR = 2014, 2026

# ---------------------------------------------------------------- 1. land / sea mask
# NB: the MOD44W ID is "MODIS/006/MOD44W" (there is no 061 version); its newest image is dated 2015-01-01
water = (ee.ImageCollection("MODIS/006/MOD44W")
         .sort("system:time_start", False).first()     # newest available year
         .select("water_mask"))            # 1 = water (incl. sea), 0 = land
land_mask = water.eq(0)
sea_mask = water.eq(1)

# ---------------------------------------------------------------- 2. regions -> Earth Engine
def to_ee_features(path, kind, id_col, radius_col=None):
    """Read a GeoJSON and turn each row into an ee.Feature with a few simple properties."""
    gdf = gpd.read_file(path)
    feats = []
    for f in json.loads(gdf.to_json())["features"]:
        p = f["properties"]
        props = {"kind": kind,
                 "region_id": p[id_col],
                 "radius_km": p[radius_col] if radius_col else 0}
        feats.append(ee.Feature(ee.Geometry(f["geometry"]), props))
    return feats

sites_dir = ROOT / "data" / "sites"
regions = ee.FeatureCollection(
    to_ee_features(sites_dir / "site_buffers.geojson", "site", "site_id", "radius_km")
    + to_ee_features(sites_dir / "coast_segments.geojson", "segment", "seg_id"))

# ---------------------------------------------------------------- 3. per-month statistics
viirs = ee.ImageCollection(VIIRS_ID)
reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)  # mean + pixel count

def month_stats(img):
    rad = img.select("avg_rad")
    stack = (rad.rename("all")
             .addBands(rad.updateMask(land_mask).rename("land"))
             .addBands(rad.updateMask(sea_mask).rename("sea"))
             .addBands(img.select("cf_cvg").rename("cvg")))
    stats = stack.reduceRegions(collection=regions, reducer=reducer, scale=SCALE_M, tileScale=2)
    month = img.date().format("YYYY-MM")
    # drop the geometry (we only need the numbers) and stamp the month
    return stats.map(lambda f: ee.Feature(None, f.toDictionary().set("month", month)))

rows = []
for year in range(FIRST_YEAR, LAST_YEAR + 1):
    year_imgs = viirs.filterDate(f"{year}-01-01", f"{year + 1}-01-01")
    fc = ee.FeatureCollection(year_imgs.map(month_stats)).flatten()
    feats = fc.getInfo()["features"]                  # one request per year keeps each under limits
    rows += [f["properties"] for f in feats]
    print(f"{year}: {len(feats)} rows")

df = pd.DataFrame(rows)
# Columns from Earth Engine: all_mean, all_count, land_mean, ..., cvg_mean. Empty regions come back blank.
keep = ["month", "kind", "region_id", "radius_km",
        "all_mean", "land_mean", "sea_mean", "cvg_mean",
        "all_count", "land_count", "sea_count"]
df = df.reindex(columns=keep).sort_values(["kind", "region_id", "radius_km", "month"])
df = df.rename(columns={"all_mean": "rad_all", "land_mean": "rad_land", "sea_mean": "rad_sea",
                        "cvg_mean": "cloudfree_nights", "all_count": "n_px_all",
                        "land_count": "n_px_land", "sea_count": "n_px_sea"})

out = ROOT / "data" / "processed" / "monthly_light.csv"
out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out, index=False)
print(f"\nSaved {len(df)} rows to {out.relative_to(ROOT)}")

# ---------------------------------------------------------------- 4. quick checks
print("\nMonths per region (expect the same number for all):",
      df.groupby(["kind", "region_id", "radius_km"]).size().unique())

seg = df[df.kind == "segment"].copy()
seg["cal_month"] = seg.month.str[5:7]
print("\nAverage cloud-free nights by calendar month (coast stretches):")
print(seg.groupby("cal_month").cloudfree_nights.mean().round(1).to_string())

s5 = df[(df.kind == "site") & (df.radius_km == 5)]
print("\nPixels in each 5 km circle (all / land / sea):")
print(s5.groupby("region_id")[["n_px_all", "n_px_land", "n_px_sea"]].median().to_string())

# ---------------------------------------------------------------- 5. first-look figure
fig_dir = ROOT / "figures"
fig_dir.mkdir(exist_ok=True)
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
for ax, sid in zip(axes, ["RUS", "DEV", "GAH_ISL"]):
    d = s5[s5.region_id == sid].copy()
    d["date"] = pd.to_datetime(d.month)
    for col, colour in [("rad_land", "tab:orange"), ("rad_sea", "tab:blue")]:
        ax.plot(d.date, d[col], color=colour, lw=1, label=col.replace("rad_", ""))
    low = d[d.cloudfree_nights < 3]                  # months built from very few clear nights
    ax.scatter(low.date, low.rad_land, s=12, color="black", zorder=3, label="< 3 cloud-free nights")
    ax.set_title(f"{sid} - 5 km circle", loc="left", fontsize=10)
    ax.set_ylabel("nW/cm²/sr")
axes[0].legend(ncol=3, fontsize=8)
fig.tight_layout()
fig.savefig(fig_dir / "m3_monthly_sites.png", dpi=200)
print("Saved figures/m3_monthly_sites.png")
