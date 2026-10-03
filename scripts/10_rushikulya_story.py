"""
10_rushikulya_story.py — the "story site" figure for Rushikulya.

Three panels over the same ~25 km area, same scale:
  A. night light, median of 2014-2016          (VIIRS monthly, months with >= 3 cloud-free nights)
  B. night light, median of 2023-2025          (same colour scale as A, so brighter = really brighter)
  C. daytime Sentinel-2 photo, Jan-Mar 2025     (what is on the ground)
Markers: the nesting beach (approximate centre) and the industrial site with the largest local
increase in night light (identified in M5; named neutrally in the README, not on the figure).

Output: figures/fig4_rushikulya_story.png
"""
import io
import os
from pathlib import Path

import ee
import matplotlib.pyplot as plt
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
ee.Initialize(project=os.getenv("EE_PROJECT"))

LON0, LAT0, HALF_LON, HALF_LAT = 85.07, 19.40, 0.12, 0.11          # ~25 x 24 km window
EXTENT = [LON0 - HALF_LON, LON0 + HALF_LON, LAT0 - HALF_LAT, LAT0 + HALF_LAT]
region = ee.Geometry.Rectangle([EXTENT[0], EXTENT[2], EXTENT[1], EXTENT[3]], proj="EPSG:4326", geodesic=False)
BEACH = (85.102, 19.407)          # centre of the ~4 km nesting beach north of the river mouth (approx.)
SITE = (85.0539, 19.3841)         # largest local light increase (M5)


def thumb(img, vis):
    """Download a small PNG of an Earth Engine image for our window."""
    url = img.getThumbURL({**vis, "region": region, "dimensions": 700, "crs": "EPSG:4326", "format": "png"})
    return plt.imread(io.BytesIO(requests.get(url, timeout=120).content), format="png")


viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
clear = viirs.map(lambda i: i.select("avg_rad").updateMask(i.select("cf_cvg").gte(3)))
# square root stretch: shows dim villages and bright sites on one scale; identical for both periods
night_vis = {"min": 0, "max": 4, "palette": ["000000", "3b1f0a", "b5541c", "f2a541", "fff3c4"]}
before = clear.filterDate("2014-01-01", "2017-01-01").median().max(0).sqrt()
after = clear.filterDate("2023-01-01", "2026-01-01").median().max(0).sqrt()
day = (ee.ImageCollection("COPERNICUS/S2_HARMONIZED").filterBounds(region)
       .filterDate("2025-01-01", "2025-03-31").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10)).median())

panels = [("A. Night light, 2014–2016", thumb(before, night_vis), "white"),
          ("B. Night light, 2023–2025", thumb(after, night_vis), "white"),
          ("C. Daytime, early 2025 (Sentinel-2)", thumb(day, {"bands": ["B4", "B3", "B2"], "min": 0, "max": 3000}), "black")]

fig, axes = plt.subplots(1, 3, figsize=(15, 5.6))
for ax, (title, img, ink) in zip(axes, panels):
    ax.imshow(img, extent=EXTENT)
    ax.plot(*BEACH, marker="o", ms=11, mfc="none", mec="#1baf7a", mew=2.5)
    ax.plot(*SITE, marker="^", ms=10, mfc="none", mec="#e87ba4", mew=2.5)
    ax.annotate("nesting beach", BEACH, xytext=(10, 10), textcoords="offset points", color=ink, fontsize=9)
    ax.annotate("industrial site", SITE, xytext=(10, -14), textcoords="offset points", color=ink, fontsize=9)
    ax.set_title(title, loc="left", fontsize=11)
    ax.set_xticks([]); ax.set_yticks([])
fig.suptitle("Rushikulya: new light is growing inland and to the south-west, led by an industrial site ~4 km from the nesting beach",
             x=0.01, ha="left", fontsize=12.5)
fig.text(0.01, 0.01, "Panels A and B share one colour scale (square-root stretch). Night light: VIIRS DNB monthly "
         "(NOAA/EOG, Colorado School of Mines). Daytime: Copernicus Sentinel-2. Via Google Earth Engine. "
         "Analysis: S. Jacob.", fontsize=7.5, color="#52514e")
fig.tight_layout(rect=[0, 0.03, 1, 0.95])
out = ROOT / "figures" / "fig4_rushikulya_story.png"
fig.savefig(out, dpi=220, facecolor="white")
print(f"Saved {out.relative_to(ROOT)}")
