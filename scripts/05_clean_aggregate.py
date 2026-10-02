"""
05_clean_aggregate.py — clean the monthly data, remove the satellite's background, and summarise
it per year and per season.

Cleaning rule (decided 2026-10-03):
  * drop any month with fewer than 3 cloud-free nights (nearly all of the Jun-Sep monsoon)
  * this also drops the fake "0.0" months, which are missing data, not darkness

Background correction (added 2026-10-03, after the first control run):
  The three offshore boxes (~100 km out at sea, where almost nothing is lit) rose from ~0.03 to
  ~0.33 nW/cm2/sr and share the SAME year-to-year wiggles and seasonal cycle as every beach.
  That looks like a background level in the monthly product, not lights. So for every month we
  subtract the mean of the three offshore boxes from every region:
        corrected = raw - offshore background (same month)
  Columns ending in _corr are corrected; the raw columns are kept for comparison.

Periods (decided 2026-10-03), each labelled with a "season year":
  annual   : all clean months of that calendar year (2026 excluded: incomplete year)
  nesting  : Feb-May of that year (arribadas + hatchling emergence)
  off      : Oct-Dec of the PREVIOUS year + Jan of that year (the months just before nesting)

For each region and period we take the MEDIAN of the clean months, keeping a period only if
enough months survive: annual >= 6 months, nesting >= 2, off >= 2.

Inputs : data/processed/monthly_light.csv, data/processed/controls_monthly.csv,
         data/processed/noise_boxes_monthly.csv (if present; from script 06)
Outputs: data/processed/period_light.csv
         figures/m3_annual_vs_controls.png   (raw vs background-corrected, side by side)
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MIN_NIGHTS = 3
MIN_MONTHS = {"annual": 6, "nesting": 2, "off": 2}
OFFSHORE = ["OFF_S", "OFF_C", "OFF_N"]
RAW_COLS = ["rad_all", "rad_land", "rad_sea"]
CORR_COLS = [c + "_corr" for c in RAW_COLS]

# ---------------------------------------------------------------- 1. load + combine
light = pd.read_csv(PROC / "monthly_light.csv")
ctrl = pd.read_csv(PROC / "controls_monthly.csv")
parts = [light, ctrl]
noise_file = PROC / "noise_boxes_monthly.csv"           # from script 06 (optional)
if noise_file.exists():
    parts.append(pd.read_csv(noise_file).drop(columns=["x", "y"], errors="ignore"))
df = pd.concat(parts, ignore_index=True)
df["year"] = df.month.str[:4].astype(int)
df["cal"] = df.month.str[5:7].astype(int)

# ---------------------------------------------------------------- 2. clean
ok = (df.cloudfree_nights >= MIN_NIGHTS) & df.rad_all.notna()
dropped = df[~ok]
print(f"Dropped {len(dropped)} of {len(df)} region-months ({len(dropped) / len(df):.0%}) "
      f"with < {MIN_NIGHTS} cloud-free nights or no value.")
clean = df[ok].copy()

# ---------------------------------------------------------------- 3. background correction
bg = (clean[clean.region_id.isin(OFFSHORE)]
      .groupby("month").rad_all.mean().rename("background"))
clean = clean.merge(bg, on="month", how="inner")      # months without a clean offshore value are dropped
for raw, corr in zip(RAW_COLS, CORR_COLS):
    clean[corr] = clean[raw] - clean["background"]
print(f"Background (offshore mean) available for {bg.size} months; "
      f"range {bg.min():.2f} to {bg.max():.2f} nW/cm2/sr")

# ---------------------------------------------------------------- 4. assign periods
annual = clean[clean.year < 2026].assign(period="annual", season_year=lambda d: d.year)
nesting = clean[clean.cal.between(2, 5)].assign(period="nesting", season_year=lambda d: d.year)
off = clean[clean.cal.isin([10, 11, 12, 1])].copy()
off["season_year"] = off.year + (off.cal >= 10).astype(int)   # Oct-Dec count towards NEXT year's season
off["period"] = "off"
periods = pd.concat([annual, nesting, off[off.season_year <= 2026]], ignore_index=True)

# ---------------------------------------------------------------- 5. median per region + period + year
keys = ["kind", "region_id", "radius_km", "period", "season_year"]
value_cols = RAW_COLS + CORR_COLS + ["background"]
agg = periods.groupby(keys).agg(**{c: (c, "median") for c in value_cols},
                                n_months=("rad_all", "size")).reset_index()
agg = agg[agg.n_months >= agg.period.map(MIN_MONTHS)]
agg.to_csv(PROC / "period_light.csv", index=False)
print(f"Saved {len(agg)} rows to data/processed/period_light.csv")

# ---------------------------------------------------------------- 6. first comparison (NOT a trend test yet)
ann = agg[agg.period == "annual"]
sites5 = ann[(ann.kind == "site") & (ann.radius_km == 5)]
segs = ann[ann.kind == "segment"]
ctrls = ann[ann.kind == "control"]


def change(d, col):
    early = d[d.season_year.between(2014, 2016)].groupby("region_id")[col].mean()
    late = d[d.season_year.between(2023, 2025)].groupby("region_id")[col].mean()
    return late - early


both = pd.concat([sites5, ctrls[ctrls.region_id == "DARK_LAND"]])
summary = pd.DataFrame({"raw change": change(both, "rad_all"),
                        "corrected change": change(both, "rad_all_corr")})
print("\nChange in annual median radiance, 2014-16 -> 2023-25 (nW/cm2/sr). Sites = 5 km circle, all pixels.")
print(summary.round(2).to_string())
for col, label in [("rad_all", "raw"), ("rad_all_corr", "corrected")]:
    c = change(segs, col)
    print(f"Coast stretches ({label}, n={c.notna().sum()}): median {c.median():.2f}, "
          f"10th pct {c.quantile(.1):.2f}, 90th pct {c.quantile(.9):.2f}")

# ---------------------------------------------------------------- 7. figure: raw vs corrected, by year
fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)
for ax, col, title in [(axes[0], "rad_all", "Raw"), (axes[1], "rad_all_corr", "Offshore background removed")]:
    band = segs.groupby("season_year")[col].quantile([.1, .5, .9]).unstack()
    ax.fill_between(band.index, band[0.1], band[0.9], color="lightgrey", label="coast stretches (10-90%)")
    ax.plot(band.index, band[0.5], color="grey", lw=1.5, label="coast stretches (median)")
    for sid, colour in [("RUS", "tab:red"), ("DEV", "tab:purple"), ("GAH_ISL", "tab:orange")]:
        d = sites5[sites5.region_id == sid]
        ax.plot(d.season_year, d[col], color=colour, lw=2, marker="o", ms=3, label=f"{sid} (5 km)")
    d = ctrls[ctrls.region_id == "DARK_LAND"]
    ax.plot(d.season_year, d[col], color="black", ls="--", lw=1, label="control DARK_LAND")
    if col == "rad_all":
        for cid in OFFSHORE:
            d = ctrls[ctrls.region_id == cid]
            ax.plot(d.season_year, d[col], color="black", ls=":", lw=1,
                    label="offshore controls" if cid == "OFF_S" else None)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_title(title, loc="left")
    ax.set_ylabel("annual median radiance (nW/cm²/sr)")
axes[0].legend(fontsize=8)
fig.suptitle("Night light at Odisha's mass-nesting beaches vs the coast and controls", x=0.01, ha="left")
fig.tight_layout()
(ROOT / "figures").mkdir(exist_ok=True)
fig.savefig(ROOT / "figures" / "m3_annual_vs_controls.png", dpi=200)
print("\nSaved figures/m3_annual_vs_controls.png")
