"""
01_site_buffers.py — draw 1, 5 and 10 km circles around each nesting beach.

Why we change projection first:
  Latitude/longitude are ANGLES, not distances. One degree of longitude is ~111 km at the
  equator but shrinks towards the poles, so a "circle" drawn in degrees is a squashed oval
  of the wrong size. We therefore convert to UTM zone 45N (EPSG:32645), where x/y are in
  METRES, draw the circles there, then convert back to lat/lon for Earth Engine.

Output: data/sites/site_buffers.geojson  (one row per site per radius)
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.affinity import translate

ROOT = Path(__file__).resolve().parents[1]
WGS84 = "EPSG:4326"     # lat/lon in degrees (what GPS and Earth Engine use)
UTM45N = "EPSG:32645"   # metres; covers 84-90 E, i.e. the whole Odisha coast
RADII_KM = [1, 5, 10]

# Rushikulya: nesting happens on a ~4 km beach NORTH of the river mouth (Shanker et al. 2004).
# Our point is the river mouth, so we move the centre ~2 km along the coast, which runs roughly
# south-west to north-east here (ASSUMPTION ~45 degrees; check on the map).
# Values are (metres east, metres north).
SHIFT_M = {"RUS": (1400, 1400)}

# 1. Read the hand-made site list and turn lat/lon columns into points
sites = pd.read_csv(ROOT / "data" / "sites" / "nesting_sites.csv")
pts = gpd.GeoDataFrame(sites, geometry=gpd.points_from_xy(sites.lon, sites.lat), crs=WGS84)

# 2. Reproject to metres and apply the Rushikulya shift
pts = pts.to_crs(UTM45N)
pts["geometry"] = [translate(g, *SHIFT_M.get(sid, (0, 0))) for g, sid in zip(pts.geometry, pts.site_id)]

# 3. One circle per site per radius
rings = []
for r in RADII_KM:
    b = pts[["site_id", "site_name", "role"]].copy()
    b["radius_km"] = r
    b = gpd.GeoDataFrame(b, geometry=pts.geometry.buffer(r * 1000), crs=UTM45N)
    rings.append(b)
buffers = gpd.GeoDataFrame(pd.concat(rings, ignore_index=True), crs=UTM45N)

# 4. Sanity check: a circle of radius r km should have area pi * r^2 km^2
buffers["area_km2"] = (buffers.area / 1e6).round(2)
print(buffers[["site_id", "radius_km", "area_km2"]].to_string(index=False))

# 5. Do any circles overlap? (overlap = the same light counted for two sites)
big = buffers[buffers.radius_km == 10].set_index("site_id")
for a in big.index:
    for b in big.index:
        if a < b and big.geometry[a].intersects(big.geometry[b]):
            print(f"Overlap at 10 km: {a} and {b}")

# 6. Back to lat/lon and save
out = ROOT / "data" / "sites" / "site_buffers.geojson"
buffers.to_crs(WGS84).to_file(out, driver="GeoJSON")
print(f"\nSaved {len(buffers)} buffers to {out.relative_to(ROOT)}")
