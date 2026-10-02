"""
02_coast_segments.py — cut the Odisha coastline into ~5 km stretches.

Why: with only three mass-nesting beaches we can't rank "sites". Instead we measure light
along the WHOLE coast in equal stretches, then ask where the nesting stretches sit in that
coast-wide spread (Weishampel et al. 2016 did the same in Florida with ~1 km segments).

Steps
  1. Get India's land outline for the Odisha box from Earth Engine (US State Dept LSIB, public domain).
  2. Switch to metres (UTM 45N).
  3. "Close" narrow inlets (river mouths, the Chilika lagoon mouth) so the coastline is one clean line.
  4. Walk along the coast from south to north and cut it every 5 km.
  5. For each stretch, keep the LAND within 5 km of it (its "zone"). Sea is left out on purpose:
     the monthly VIIRS product is not filtered for boat lights.
  6. Tag the stretch nearest to each nesting beach.

Outputs (data/sites/):
  odisha_land.geojson      land inside the Odisha box (used later to mask out sea pixels)
  coast_segments.geojson   one zone polygon per 5 km stretch
  figures/m2_coast_segments.png   quick-look map
"""
import os
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Polygon, MultiPolygon, box, shape
from shapely.ops import linemerge, substring

ROOT = Path(__file__).resolve().parents[1]
WGS84, UTM45N = "EPSG:4326", "EPSG:32645"

BBOX = (84.60, 19.05, 87.60, 21.70)  # lon_min, lat_min, lon_max, lat_max: roughly Odisha's coast
SEG_KM = 5          # length of each coastal stretch
ZONE_KM = 5         # how far inland each stretch's zone reaches
CLOSE_M = 3000      # inlets narrower than ~2 x this are sealed when tracing the coastline
SITE_MAX_KM = 10    # a site is linked to its nearest stretch only if it is within this distance


def largest_polygon(geom):
    """Return the biggest single polygon (the mainland) from a Polygon/MultiPolygon."""
    if isinstance(geom, Polygon):
        return geom
    return max(geom.geoms, key=lambda g: g.area)


def build_segments(land_utm, bbox_utm, site_pts_utm):
    """Core geometry, kept separate so it can be tested without Earth Engine."""
    # 3. Seal narrow inlets: grow the land outward, then shrink it back by the same amount
    closed = land_utm.buffer(CLOSE_M).buffer(-CLOSE_M)
    mainland = largest_polygon(closed)

    # Coastline = mainland outline MINUS the artificial edges of our box
    coast = mainland.exterior.difference(bbox_utm.exterior.buffer(100))
    if coast.geom_type == "MultiLineString":
        coast = linemerge(coast)
    if coast.geom_type == "MultiLineString":           # still pieces? keep the longest
        coast = max(coast.geoms, key=lambda g: g.length)

    # 4. Orient south -> north, then cut every SEG_KM
    if coast.coords[0][1] > coast.coords[-1][1]:
        coast = LineString(list(coast.coords)[::-1])
    seg_m = SEG_KM * 1000
    n = int(coast.length // seg_m)
    rows = []
    for i in range(n):
        piece = substring(coast, i * seg_m, (i + 1) * seg_m)
        # 5. Land within ZONE_KM of this piece
        zone = piece.buffer(ZONE_KM * 1000, cap_style="flat").intersection(land_utm)  # flat ends: neighbours barely overlap
        rows.append({"seg_id": f"S{i:03d}", "km_from_south": i * SEG_KM,
                     "zone_km2": round(zone.area / 1e6, 1), "geometry": zone, "coast_line": piece})
    segs = gpd.GeoDataFrame(rows, geometry="geometry", crs=UTM45N)

    # 6. Link each nesting site to its nearest stretch (measured to the coastline piece)
    segs["site_id"] = ""
    for sid, pt in site_pts_utm.items():
        d = segs["coast_line"].apply(lambda ln: ln.distance(pt))
        j = d.idxmin()
        if d[j] <= SITE_MAX_KM * 1000:
            segs.loc[j, "site_id"] = (segs.loc[j, "site_id"] + " " + sid).strip()
        print(f"{sid}: nearest stretch {segs.loc[j, 'seg_id']} at {d[j] / 1000:.1f} km")
    return segs.drop(columns="coast_line"), coast


def main():
    import ee
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    ee.Initialize(project=os.getenv("EE_PROJECT"))

    # 1. Land outline from Earth Engine, clipped to our box on the server (keeps the download small)
    region = ee.Geometry.Rectangle(list(BBOX), proj="EPSG:4326", geodesic=False)
    land_fc = ee.FeatureCollection("USDOS/LSIB/2017").filterBounds(region)
    land_ee = land_fc.geometry(maxError=50).intersection(region, maxError=50)
    land_wgs = shape(land_ee.getInfo())
    print(f"Land outline downloaded ({land_wgs.geom_type})")

    # 2. To metres
    land = gpd.GeoSeries([land_wgs], crs=WGS84).to_crs(UTM45N).iloc[0]
    bbox_utm = gpd.GeoSeries([box(*BBOX)], crs=WGS84).to_crs(UTM45N).iloc[0]

    # Beach centres = centres of the 1 km circles from script 01 (includes the Rushikulya shift)
    buf = gpd.read_file(ROOT / "data" / "sites" / "site_buffers.geojson").to_crs(UTM45N)
    one_km = buf[buf.radius_km == 1]
    sites = dict(zip(one_km.site_id, one_km.geometry.centroid))

    segs, coast = build_segments(land, bbox_utm, sites)

    print(f"\nCoastline traced: {coast.length / 1000:.0f} km -> {len(segs)} stretches of {SEG_KM} km")
    print(f"Zone area per stretch: median {segs.zone_km2.median():.0f} km2 "
          f"(min {segs.zone_km2.min():.0f}, max {segs.zone_km2.max():.0f})")
    print(segs[segs.site_id != ""][["seg_id", "km_from_south", "site_id", "zone_km2"]].to_string(index=False))

    out_dir = ROOT / "data" / "sites"
    gpd.GeoDataFrame(geometry=[land], crs=UTM45N).to_crs(WGS84).to_file(out_dir / "odisha_land.geojson", driver="GeoJSON")
    segs.to_crs(WGS84).to_file(out_dir / "coast_segments.geojson", driver="GeoJSON")

    # Quick-look map
    fig_dir = ROOT / "figures"
    fig_dir.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 8))
    gpd.GeoSeries([land], crs=UTM45N).plot(ax=ax, color="#eeeeee", edgecolor="#bbbbbb", linewidth=0.3)
    segs.plot(ax=ax, column=segs.index % 2, cmap="Pastel1", edgecolor="grey", linewidth=0.2)
    segs[segs.site_id != ""].plot(ax=ax, color="tab:orange", edgecolor="black", linewidth=0.5)
    gpd.GeoSeries(list(sites.values()), crs=UTM45N).plot(ax=ax, color="red", markersize=12)
    for sid, pt in sites.items():
        ax.annotate(sid, (pt.x, pt.y), xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set_title(f"Odisha coast in {len(segs)} stretches of {SEG_KM} km (orange = nesting)")
    ax.set_axis_off()
    fig.savefig(fig_dir / "m2_coast_segments.png", dpi=200, bbox_inches="tight")
    print(f"\nSaved data/sites/coast_segments.geojson, data/sites/odisha_land.geojson, figures/m2_coast_segments.png")


if __name__ == "__main__":
    main()
