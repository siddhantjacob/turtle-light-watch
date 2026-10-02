"""
07_trends.py — M4: is each beach / coast stretch really getting brighter?

For every region we take its yearly (or seasonal) background-corrected median light and ask TWO
questions, because they test different things (decided 2026-10-03: use both):

  1. Mann-Kendall test: do the years go up (or down) CONSISTENTLY, more than a random order would?
     -> p-value. p < 0.05 = a consistent direction.
  2. Noise floor: is the Theil-Sen slope BIGGER than the slopes we see in ~30 empty sea boxes,
     where the true trend is zero? floor = 95th percentile of |slope| in those boxes.

Theil-Sen slope = the median of the slopes between every pair of years (robust: one odd year,
e.g. a cyclone blackout, cannot drag it). Units: nW/cm2/sr per year.

Verdicts:
  "robust increase/decrease"      p < 0.05 AND |slope| > noise floor
  "consistent but within noise"   p < 0.05 but |slope| <= noise floor
  "no clear trend"                p >= 0.05

Season question: for each region we also test the trend in (nesting Feb-May minus off-season Oct-Jan).
A robust trend there means the nesting months changed differently from the rest of the year.

Input : data/processed/period_light.csv (script 05, run AFTER script 06)
Output: data/processed/trends.csv, figures/m4_stretch_trends.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymannkendall as mk
from scipy.stats import theilslopes

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MIN_YEARS = 8
EDGE_STRETCHES = {"S000", "S001", "S097", "S098"}   # may lie in Andhra Pradesh / West Bengal

pl = pd.read_csv(PROC / "period_light.csv")
if not (pl.kind == "noise").any():
    raise SystemExit("No noise boxes found: run scripts 06 and then 05 first.")


def trend(years, values):
    """Theil-Sen slope (+95% CI) and Mann-Kendall p-value for one yearly series."""
    if len(values) < MIN_YEARS:
        return dict(slope=np.nan, slope_lo=np.nan, slope_hi=np.nan, p=np.nan, n_years=len(values))
    ts = theilslopes(values, years)
    return dict(slope=ts[0], slope_lo=ts[2], slope_hi=ts[3],
                p=mk.original_test(values).p, n_years=len(values))


# ---------------------------------------------------------------- 1. build every series we test
series = []   # (kind, region_id, radius_km, period, measure, DataFrame[season_year, value])
measures = {"site": ["rad_all_corr", "rad_land_corr", "rad_sea_corr"]}
for (kind, rid, rad), g in pl.groupby(["kind", "region_id", "radius_km"]):
    for measure in measures.get(kind, ["rad_all_corr"]):
        by_period = {p: g[g.period == p].set_index("season_year")[measure].dropna()
                     for p in ["annual", "nesting", "off"]}
        for p, s in by_period.items():
            series.append((kind, rid, rad, p, measure, s))
        diff = (by_period["nesting"] - by_period["off"]).dropna()   # years with both seasons
        series.append((kind, rid, rad, "nest_minus_off", measure, diff))

rows = []
for kind, rid, rad, period, measure, s in series:
    s = s[s.index <= 2025] if period == "annual" else s
    r = trend(s.index.values.astype(float), s.values)
    rows.append(dict(kind=kind, region_id=rid, radius_km=rad, period=period, measure=measure, **r))
tr = pd.DataFrame(rows)

# ---------------------------------------------------------------- 2. noise floor from the empty sea boxes
# Small regions are noisier than big ones, so each region gets the floor of same-sized sea circles:
#   beach circles -> sea circles of the same radius; coast stretches (~25 km2) -> 2.8 km circles;
#   DARK_LAND (huge) -> 10 km circles (the least noisy we have; approximate).
noise = tr[(tr.kind == "noise") & tr.slope.notna()]
floor = (noise.groupby(["period", "radius_km"]).slope
         .apply(lambda s: s.abs().quantile(0.95)).rename("noise_floor").reset_index())
tr["floor_radius"] = np.select([tr.kind == "segment", tr.kind == "control"], [2.8, 10.0], tr.radius_km)
tr = tr.merge(floor.rename(columns={"radius_km": "floor_radius"}), on=["period", "floor_radius"], how="left")
print("Noise floor = 95th percentile of |slope| in empty sea circles (nW/cm2/sr per year):")
print(floor.pivot(index="radius_km", columns="period", values="noise_floor").round(4).to_string(),
      f"\n(from {noise.region_id.nunique()} sea locations)\n")


def verdict(r):
    if pd.isna(r.p):
        return "too few years"
    if r.p >= 0.05:
        return "no clear trend"
    direction = "increase" if r.slope > 0 else "decrease"
    return f"robust {direction}" if abs(r.slope) > r.noise_floor else "consistent but within noise"


tr["verdict"] = tr.apply(verdict, axis=1)
tr["edge_stretch"] = tr.region_id.isin(EDGE_STRETCHES)
tr.to_csv(PROC / "trends.csv", index=False)

# ---------------------------------------------------------------- 3. what we care about
pd.set_option("display.width", 140)
cols = ["region_id", "radius_km", "measure", "slope", "slope_lo", "slope_hi", "p", "verdict"]
fmt = lambda d: d[cols].round({"slope": 3, "slope_lo": 3, "slope_hi": 3, "p": 3}).to_string(index=False)

sites = tr[(tr.kind == "site") & (tr.period == "annual")]
print("BEACH CIRCLES, annual (land only is unreliable for GAH_ISL: ~5 land pixels)")
print(fmt(sites[sites.measure.isin(["rad_all_corr", "rad_land_corr"])]
          .sort_values(["region_id", "measure", "radius_km"])))

segs = tr[(tr.kind == "segment") & (tr.period == "annual")].copy()
segs["rank"] = segs.slope.rank(ascending=False).astype(int)   # 1 = fastest brightening
nesting_ids = {"S011": "Rushikulya", "S041": "Devi", "S066": "Gahirmatha island", "S068": "Gahirmatha mainland"}
print(f"\nCOAST STRETCHES, annual: {len(segs)} stretches")
print(segs.verdict.value_counts().to_string())
nest = segs[segs.region_id.isin(nesting_ids)].assign(beach=lambda d: d.region_id.map(nesting_ids))
print("\nNesting stretches (rank 1 = fastest brightening of 99):")
print(nest[["region_id", "beach", "slope", "p", "verdict", "rank"]].round(3).to_string(index=False))

dark = tr[(tr.region_id == "DARK_LAND") & (tr.period == "annual")]
print("\nDARK_LAND (rural background):")
print(fmt(dark))

season = tr[(tr.period == "nest_minus_off") & tr.region_id.isin(list(nesting_ids) + ["RUS", "DEV", "GAH_ISL", "GAH_MAIN", "DARK_LAND"])
            & tr.measure.eq("rad_all_corr") & tr.radius_km.isin([0, 5])]
print("\nSEASON: trend in (nesting Feb-May minus off-season Oct-Jan)")
print(fmt(season.sort_values("region_id")))

# ---------------------------------------------------------------- 4. figure: every stretch along the coast
segs = segs.sort_values("region_id")
km = segs.region_id.str[1:].astype(int) * 5
robust = segs.verdict.str.startswith("robust")
f_annual = floor[(floor.period == "annual") & (floor.radius_km == 2.8)].noise_floor.iloc[0]
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.axhspan(-f_annual, f_annual, color="lightgrey", alpha=0.6, label="noise floor (empty sea, same size)")
ax.bar(km[~robust], segs.slope[~robust], width=4, color="#c9c9c9", label="not robust")
ax.bar(km[robust], segs.slope[robust], width=4, color="#3b6fb6", label="robust trend")
for sid, name in nesting_ids.items():
    r = segs[segs.region_id == sid]
    if len(r):
        x, y = int(sid[1:]) * 5, r.slope.iloc[0]
        ax.bar([x], [y], width=4, color="tab:orange", edgecolor="black")
        ax.annotate(name, (x, y), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
ax.axhline(0, color="black", lw=0.6)
ax.set_xlabel("km along the coast, south (Andhra Pradesh border) to north (West Bengal border)")
ax.set_ylabel("trend, nW/cm²/sr per year")
ax.set_title("Night-light trend 2014-2025 for every 5 km stretch of the Odisha coast (background removed)",
             loc="left")
ax.legend(fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(ROOT / "figures" / "m4_stretch_trends.png", dpi=200)
print("\nSaved data/processed/trends.csv and figures/m4_stretch_trends.png")
