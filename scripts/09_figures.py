"""
09_figures.py — M6: the three main figures for the README, brief and LinkedIn.

  fig1_coast_map.png       every 5 km stretch coloured by how fast it brightened (darker = faster)
  fig2_where_beaches_sit.png  all 99 stretches ranked; the nesting beaches highlighted
  fig3_sensor_drift.png    the "empty sea got brighter" check: raw vs background-corrected

Style: one sequential hue (blue) for magnitude, orange only for the nesting beaches, grey for
"not robust". Text stays dark grey. No dual axes. Values come only from earlier scripts.
Inputs: data/processed/trends.csv, data/processed/period_light.csv, data/sites/*.geojson
"""
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, LogNorm

ROOT = Path(__file__).resolve().parents[1]
PROC, SITES, FIGS = ROOT / "data" / "processed", ROOT / "data" / "sites", ROOT / "figures"
FIGS.mkdir(exist_ok=True)

# ---------------------------------------------------------------- shared style
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#a3a29b"
NOT_ROBUST = "#dddcd7"
ORANGE = "#eb6834"                           # nesting beaches only
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
BLUES = LinearSegmentedColormap.from_list("blues", BLUE_RAMP)
plt.rcParams.update({"font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})
NESTING = {"S011": "Rushikulya", "S041": "Devi", "S068": "Gahirmatha (mainland)"}
PLACES = {"S028": "Puri", "S049": "Paradip port area", "S070": "Dhamra port area"}   # located by coordinates
CREDIT = "Data: VIIRS DNB monthly (NOAA/EOG, Colorado School of Mines) via Google Earth Engine. Analysis: S. Jacob."

tr = pd.read_csv(PROC / "trends.csv")
seg_tr = tr[(tr.kind == "segment") & (tr.period == "annual") & (tr.measure == "rad_all_corr")]
segs = gpd.read_file(SITES / "coast_segments.geojson").merge(
    seg_tr[["region_id", "slope", "verdict"]], left_on="seg_id", right_on="region_id")
segs["robust"] = segs.verdict.str.startswith("robust increase")
land = gpd.read_file(SITES / "odisha_land.geojson")

# ---------------------------------------------------------------- fig 1: map
utm = "EPSG:32645"
segs_u, land_u = segs.to_crs(utm), land.to_crs(utm)
norm = LogNorm(vmin=0.005, vmax=1.5)          # log scale: trends span 0.005 to 1.4
fig, ax = plt.subplots(figsize=(7.5, 8.5))
land_u.plot(ax=ax, color="#f3f2ef", edgecolor="#f3f2ef", linewidth=0)
segs_u[~segs_u.robust].plot(ax=ax, color=NOT_ROBUST, edgecolor="white", linewidth=0.3)
segs_u[segs_u.robust].plot(ax=ax, column="slope", cmap=BLUES, norm=norm, edgecolor="white", linewidth=0.3)
for sid, name in {**NESTING, **PLACES}.items():
    row = segs_u[segs_u.seg_id == sid]
    if row.empty:
        continue
    c = row.geometry.iloc[0].centroid
    nesting = sid in NESTING
    if nesting:
        row.plot(ax=ax, facecolor="none", edgecolor=ORANGE, linewidth=2)
    offset = {"S070": (-14, 12), "S068": (-14, -8)}.get(sid, (-12, 0))   # keep Dhamra / Gahirmatha apart
    ax.annotate(name, (c.x, c.y), xytext=offset, textcoords="offset points", ha="right", va="center",
                fontsize=9, color=ORANGE if nesting else INK2, fontweight="bold" if nesting else "normal")
sm = plt.cm.ScalarMappable(cmap=BLUES, norm=norm)
cb = fig.colorbar(sm, ax=ax, shrink=0.45, pad=0.01)
cb.set_label("brightening, nW/cm²/sr per year (log scale)")
ax.set_axis_off()
ax.set_title("How fast each 5 km stretch of the Odisha coast got brighter at night, 2014–2025",
             loc="left", fontsize=11)
ax.text(0, -0.02, "Orange outline = olive ridley mass-nesting beach. Grey = no robust trend. "
        "Satellite background drift removed.\n" + CREDIT, transform=ax.transAxes, fontsize=7, color=INK2, va="top")
fig.savefig(FIGS / "fig1_coast_map.png", dpi=250, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------- fig 2: ranked stretches
r = segs.sort_values("slope", ascending=False).reset_index(drop=True)
r["rank"] = np.arange(1, len(r) + 1)
colours = [ORANGE if s in NESTING else ("#6da7ec" if rb else NOT_ROBUST) for s, rb in zip(r.seg_id, r.robust)]
fig, ax = plt.subplots(figsize=(11, 4.6))
ax.bar(r["rank"], r.slope.clip(lower=0.003), width=0.75, color=colours)
ax.set_yscale("log")
ax.set_xlim(0, len(r) + 1)
ax.set_xlabel("99 coast stretches, ranked from fastest to slowest brightening")
ax.set_ylabel("nW/cm²/sr per year (log)")
med = r.slope.median()
ax.axhline(med, color=INK2, lw=0.8, ls="--")
ax.text(len(r) + 0.5, med, " median stretch", va="bottom", ha="right", fontsize=8, color=INK2)
for sid, name in NESTING.items():
    row = r[r.seg_id == sid].iloc[0]
    dx, dy = {"S011": (-28, 42), "S068": (34, 16)}.get(sid, (0, 18))
    ax.annotate(f"{name}\nrank {row['rank']} of 99", (row["rank"], row.slope), xytext=(dx, dy),
                textcoords="offset points", ha="center", fontsize=8.5, color=ORANGE, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.8))
for sid, name in PLACES.items():
    row = r[r.seg_id == sid].iloc[0]
    dy = {"S028": 9, "S070": -9}.get(sid, 0)
    ax.annotate(name, (row["rank"], row.slope), xytext=(6, dy), textcoords="offset points",
                fontsize=8, color=INK2, va="center")
ax.set_title("Where the turtle beaches sit among all 99 stretches of the Odisha coast", loc="left", fontsize=11)
fig.text(0.01, -0.04, "Light grey = no robust trend. Gahirmatha's island beach is not shown (its land zone is too "
         "small to measure; nearby light barely changed).\n" + CREDIT, fontsize=7, color=INK2)
fig.savefig(FIGS / "fig2_where_beaches_sit.png", dpi=250, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------- fig 3: the empty sea got brighter
pl = pd.read_csv(PROC / "period_light.csv")
ann = pl[(pl.period == "annual")]
off = ann[ann.region_id.isin(["OFF_S", "OFF_C", "OFF_N"])].groupby("season_year")[["rad_all", "rad_all_corr"]].mean()
lines = {"Rushikulya beach (5 km)": ("RUS", "#2a78d6", "-"),
         "Devi beach (5 km)": ("DEV", "#4a3aa7", "-")}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
for ax, col, title in [(axes[0], "rad_all", "A. As measured"),
                       (axes[1], "rad_all_corr", "B. After removing the empty-sea level")]:
    ax.plot(off.index, off[col], color=INK2, ls="--", lw=2, marker="o", ms=4,
            label="Empty sea, ~100 km offshore")
    for label, (sid, colour, ls) in lines.items():
        d = ann[(ann.region_id == sid) & (ann.radius_km == 5)].sort_values("season_year")
        ax.plot(d.season_year, d[col], color=colour, ls=ls, lw=2, marker="o", ms=4, label=label)
    ax.axhline(0, color=MUTED, lw=0.6)
    ax.set_title(title, loc="left", fontsize=10.5)
    ax.set_xlabel("year")
axes[0].set_ylabel("yearly median night light, nW/cm²/sr")
axes[0].legend(fontsize=8, frameon=False, loc="upper left")
fig.suptitle("Even the empty sea 'got brighter': part of the trend was the satellite, not the coast",
             x=0.01, ha="left", fontsize=11.5)
fig.text(0.01, -0.03, "Panel A: the sea, with nothing lit, rises in step with the beaches. Panel B: subtracting it "
         "each month leaves the real change.\n" + CREDIT, fontsize=7, color=INK2)
fig.tight_layout()
fig.savefig(FIGS / "fig3_sensor_drift.png", dpi=250, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Saved figures/fig1_coast_map.png, fig2_where_beaches_sit.png, fig3_sensor_drift.png")
