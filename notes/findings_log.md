# Findings log (hedged; local notes, feeds the README and brief)

## 2026-10-01
- DECISION: site = Odisha, India. Design = split the coast into ~5 km segments and compare
  the nesting segments against the coast-wide distribution of trends (only a handful of
  nesting sites, so ranking sites alone would be thin).
- DATA CHECK: GEE `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` returns 152 images, Jan 2014 to
  Aug 2026 (12 x 12 + 8 = 152), so no whole months are missing from the collection.
  Pixel-level cloud gaps (cf_cvg) not yet checked; expect them in the Jun-Sep monsoon.
- DATA CHECK: OBIS-SEAMAP SWOT (dataset 545), logged out, region drawn around the
  north-east Bay of Bengal: 13 olive ridley records, years 1994-2003, "group size"
  2 to 175,000. Coordinates hidden while logged out. Region may include Bangladesh;
  to confirm after logging in.
  -> Implication: counts are 11+ years older than the VIIRS record, so use them only as
     a rough "importance" label (mass vs sporadic), not as current nest density.
- DATA ACCESS: SWOT download refused: "This dataset is downloadable only if you got a
  permission from the provider." Coordinates hidden in the viewer too. Read as a deliberate
  protection of nesting locations (consistent with poaching sensitivity), not a bug.
  -> DECISION: 30-min timebox hit. Fall back to a hand-made list of the three well-known
     mass-nesting sites (Gahirmatha, Devi, Rushikulya) located at ~1 km precision with a
     source column. Enough for 464 m pixels and 1-10 km buffers. No new precise nest
     locations will be published. Optional later: request permission from SWOT
     (swotdata@gmail.com); not on the critical path.
- SITES: data/raw/nesting_sites.csv created (4 rows; public locations, ~1 km precision).
- KEY CONTEXT (literature, to verify in M0 scan): Behera et al. (2016) report that Gahirmatha
  arribadas moved from a ~10 km mainland beach to the Nasi islands and, since ~2009, to a
  ~900 m beach on the SW of Abdul Kalam (Wheeler) Island, which hosts a DRDO missile test
  facility. DRDO states lights are dimmed/masked in nesting season (Wikipedia).
  -> The main Gahirmatha nesting beach shares its pixels with a lit military facility.
  -> Testable later (hedged): is island radiance lower in nesting months than off-season?
- DISTANCES (great-circle): Jacob's Google Maps point is ~8 km from the island centre;
  Dhamra port (operating since 2011) is ~10 km from that point and ~14.5 km from the island.

## 2026-10-02
- LITERATURE: 14 of 15 papers read (Behera 2016 from abstract). Notes in docs/literature_notes.md.
- NOVELTY (hedged): no satellite night-light study of Odisha's arribada beaches found. VIIRS trends at
  nesting beaches were done once before (Leader et al. 2024, eastern Mediterranean, 2012-2020, Pearson r,
  no control areas), so our step up = robust trends + noise floor + coast-wide context + 2014-2026 + season.
- SITE: Rushikulya nesting is on a ~4 km beach north of the river mouth (Shanker et al. 2004).
- DECISION: core question locked, WITH the nesting/hatching-season (Feb-May) comparison (+~2 h).
- HOUSEKEEPING: sites file moved to data/sites/nesting_sites.csv (tracked in git; data/raw is not).
- SETUP (M1): scripts/00_check_setup.py passed on Jacob's PC: Earth Engine project
  "turtle-light-watch", 152 monthly images, latest 2026-08, 4 sites loaded.
- GIT: first local commit ef3e391 (12 files; .env, papers/, .venv/ correctly excluded).
- BUFFERS (M2): scripts/01_site_buffers.py OK. Areas 3.14 / 78.41 / 313.65 km2 vs pi*r^2 =
  3.14 / 78.54 / 314.16: ~0.2% short because a "circle" is drawn as a 64-sided polygon, not a
  projection error. GAH_ISL and GAH_MAIN overlap at 10 km (and at 5 km, since they are 8.1 km
  apart): expected, they are two versions of the same site, never analysed side by side as
  independent sites. geojson.io check: Rushikulya centre lands on the coast NE of the river mouth.
- DESIGN ISSUE: about half of every beach circle is SEA. Monthly VIIRS V1 keeps boat lights, and
  boats are banned near rookeries in season, so sea pixels could fake a seasonal signal.
  Coast segments (script 02) therefore use LAND ONLY within 5 km of each 5 km stretch.
- COAST SEGMENTS (M2): scripts/02_coast_segments.py OK. LSIB 2017 land outline (public domain).
  Coastline traced = 497 km -> 99 stretches of 5 km; land zone per stretch median 26 km2
  (min 1, max 39). Longer than my 430-480 km guess (Jacob predicted longer): the 50 m outline
  keeps small wiggles that 3 km "closing" does not seal, and the box ends reach slightly past
  Odisha (first stretch starts 19.05 N, last ends ~21.68 N near Digha, West Bengal).
  -> 1-2 stretches at each end may lie in Andhra Pradesh / West Bengal: flag them in M4.
- Nesting stretches: RUS -> S011 (0.1 km away), DEV -> S041 (0.3 km), GAH_MAIN -> S068 (0.1 km),
  GAH_ISL -> S066 (4.2 km away; zone only 0.6 km2 of land on a thin spit).
- IMPORTANT: the LSIB outline is a single polygon, so Abdul Kalam Island is NOT in our land mask.
  A land-only rule would delete the main Gahirmatha nesting beach. Land-only must not use LSIB
  for the site circles.
- DECISION: beach circles measured three ways (all / land / sea) using the MODIS 250 m water
  mask (MOD44W 2015, includes islands); coast stretches stay land-only (LSIB). Script 03 written.

## 2026-10-03 — first light data (M3)
- RUN: scripts/03 -> data/processed/monthly_light.csv, 16,872 rows = 111 regions x 152 months (no gaps).
  Fix on the way: water-mask ID is MODIS/006/MOD44W (061 does not exist).
- CLOUD: mean cloud-free nights by month on the coast: Jan 14.8 ... May 7.5, Jun 3.3, Jul 1.6,
  Aug 2.8, Sep 3.7, Oct 10.7. 24 months (all Jun-Sep) have ~0 nights somewhere.
- ZERO != DARK: all 14 exact-zero values at the 5 km circles have 0 cloud-free nights. They are
  missing data and must be dropped, never averaged in.
- NOISE HINT: 92 negative radiance values (min -0.14 nW/cm2/sr): background noise is roughly
  +/-0.1-0.15. Baselines near 0.1 are AT the noise level, so % change from them is meaningless;
  report absolute change (nW/cm2/sr) first.
- PIXELS (5 km circle): ~430 total. GAH_ISL has only ~5 LAND pixels (tiny island at 250 m) ->
  its "land" series is too thin to trust; use "all" for GAH_ISL.
- FIRST LOOK, medians of months with >=3 cloud-free nights, 5 km circle, "all" (NOT yet tested):
    RUS 0.42 (2014-16) -> 1.15 (2023-25); DEV 0.09 -> 0.50; GAH_ISL 0.11 -> 0.48; GAH_MAIN 0.14 -> 0.66.
  Sea pixels rise almost as much as land (e.g. DEV sea 0.08 -> 0.47), consistent with light
  spilling from land into nearby "sea" pixels (sensor blur) rather than boats. Sea is a weak boat check
  within 5 km.
- CAUTION: everything rises together (land, sea, all sites). Could be real regional growth OR a
  product/sensor-level change. Cannot tell without CONTROL areas -> do controls before trends.
- SEASONAL CYCLE (coast stretches, median by calendar month): high Apr 0.82 / Oct 0.77, low Jan 0.55 /
  Jul 0.42. A +/-20-30% seasonal swing: the Feb-May vs rest comparison must account for it.
  Candidate causes (untested): spring fires (V1 not fire-filtered), winter haze, monsoon cloud residue.
- DECISIONS (Jacob, 2026-10-03): (1) drop months with < 3 cloud-free nights; (2) season comparison =
  nesting Feb-May vs off-season Oct-Jan (Oct-Dec counted towards the next year's season); (3) build
  controls before trend tests.
- CONTROLS designed (script 04): three 22 x 22 km boxes ~100 km offshore (OFF_S/C/N) = sensor drift +
  noise; DARK_LAND = land the VIIRS 2013 annual product classed as unlit (median_masked = 0), outside
  the 10 km beach circles = rural background. Chosen with 2013 (outside the trend period) to avoid
  regression to the mean. Script 05 cleans + makes annual / nesting / off-season medians.
- DATA CHECK: NOAA/VIIRS/DNB/ANNUAL_V22 returned NO image for 2013 (despite the catalogue range
  2012-2024). Switched the 2013 dark-land selection to ANNUAL_V21. Added pre-flight checks.
  -> Before the M5 annual cross-check, list which years V22 actually contains. [verify]
- CONTROLS RUN (script 04): DARK_LAND ~126k pixels; offshore boxes 2,401 pixels each.
- **KEY FINDING (method)**: the three OFFSHORE boxes, ~100 km out at sea and ~300 km apart, rose from
  ~0.03 (2014-16) to ~0.33 nW/cm2/sr (2023-25), and share the SAME year-to-year wiggles as every
  beach and DARK_LAND (dip 2016, jump 2017, dip 2019, jump 2020, jump 2023) and the same seasonal
  cycle (high Apr, low Dec/Jan). Three boxes agree within ~0.02. Consistent with a background level
  in the monthly VIIRS product (cause not identified; candidates: airglow, processing/calibration
  changes) rather than real lights. [verify cause in literature]
  -> Raw trends at dim beaches are mostly this background: raw change DEV +0.40 vs offshore +0.30.
  -> FIX: subtract the monthly offshore mean from every region (columns *_corr in period_light.csv).
- After correction (2014-16 -> 2023-25, 5 km, all pixels; still NOT trend-tested):
  RUS +0.43, GAH_MAIN +0.22, DEV +0.12, GAH_ISL +0.05, DARK_LAND +0.11;
  coast stretches median +0.31 (10th pct +0.10, 90th pct +2.32).
  First impression (hedged): Rushikulya brightened somewhat more than a typical stretch; Devi and the
  Gahirmatha island are among the dimmest, slowest-changing parts of the coast.
- LESSON for README/LinkedIn: without the offshore control we would have reported "all three nesting
  beaches got 3-5x brighter". Most of that was the sensor background.
- RANKS (corrected, 2014-16 -> 2023-25). Fair comparison = nesting STRETCH vs other stretches (both land-only;
  the 5 km circles are ~half sea, so their values are diluted and not comparable to stretches):
    Rushikulya S011: change +0.46, larger than 68/99 stretches; baseline 0.56
    Devi S041:       change +0.14, larger than 23/99; baseline 0.10
    Gahirmatha main S068: change +0.40, larger than 60/99; baseline 0.17
    Gahirmatha island S066: +0.05 (2/99) but zone is only 0.6 km2 of land -> unreliable
  Hedged reading: Rushikulya and the Gahirmatha mainland brightened a bit more than the typical stretch;
  Devi stayed among the darker, slower-changing parts of the coast. Not yet tested against noise.
- DECISION (Jacob): use BOTH tests. A trend is "robust" only if Mann-Kendall p < 0.05 AND the Theil-Sen
  slope exceeds the noise floor = 95th pct of |slope| in ~30 empty-sea locations (no land within 50 km).
  Noise floors are SIZE-MATCHED (sea circles of 1, 2.8, 5, 10 km), because averaging more pixels
  lowers noise: beach circles use same-radius sea circles, coast stretches (~25 km2) use 2.8 km circles.
  Scripts: 06 (extract sea circles), 05 (re-run, now includes them), 07 (trends + season difference).

## 2026-10-03 — M4 trend results (background-corrected annual medians, 2014-2025)
- NOISE FLOOR (95th pct |slope|, 30 empty-sea locations, size-matched): 0.001-0.0017 nW/cm2/sr/yr (annual).
  Very small: after background removal the open sea is quiet. CAVEAT: sea is a LOWER bound on noise; land
  has extra non-light variability (fires, geolocation jitter at bright edges), so the floor is lenient.
- COAST: 94/99 stretches robust increase, 5 no clear trend. Stretch slope median 0.032/yr (10th 0.010,
  90th 0.257). Brightening is COAST-WIDE, not specific to nesting beaches.
- FASTEST stretches (by location, to verify with Sentinel-2): S049/S050/S051 (~20.27 N, 86.62-86.70 E) =
  Paradip port/industrial area (1.40, 1.28, 0.42/yr); S028 (19.81 N, 85.80 E) = Puri town (0.56/yr);
  S070 (20.82 N, 86.95 E) = Dhamra port area (0.54/yr), ~9 km north of the Gahirmatha mainland stretch.
  S048 (next to Paradip) slope -0.74/yr but "no clear trend": erratic, check (flares? construction?).
- NESTING STRETCHES (rank of 99, 1 = fastest):
    Rushikulya S011  0.054/yr  rank 26  robust   (~1.7x the coast median; ~4x DARK_LAND)
    Gahirmatha main S068 0.045/yr rank 34 robust
    Devi S041        0.014/yr  rank 78  robust   (similar to rural background DARK_LAND 0.012/yr)
    Gahirmatha island S066 0.005/yr rank 97 (zone unreliable; island 5 km circle also slow, 0.006/yr)
- BUFFER SENSITIVITY (all pixels, slope at 1/5/10 km): RUS .028/.047/.036 > GAH_MAIN .023/.024/.029 >
  DEV .009/.011/.015 ~ GAH_ISL .010/.006/.008. Ordering holds except DEV vs GAH_ISL at 1 km (tie, noisy).
- SEASON (nesting Feb-May minus off Oct-Jan): robust increase at GAH_MAIN circle (0.018/yr) and S068 (0.034/yr)
  [S068: nesting 0.13-0.18 in 2014-19 -> 0.51-1.03 in 2023-26; off-season 0.19-0.29 -> 0.32-0.57].
  BUT 57/99 stretches show the same pattern -> mostly COAST-WIDE, not beach-specific. Candidates: changing
  seasonal background not fully removed by subtraction, spring fires (V1 not fire-filtered), winter haze.
  Multiple testing: ~100 tests at p<0.05 expect ~5 false positives; borderline p (S041 0.047) = weak.
- HEADLINE (hedged, pre-validation): "Night light rose almost everywhere on the Odisha coast 2014-2025.
  Rushikulya and the Gahirmatha mainland coast near Dhamra port brightened faster than most of the coast;
  Devi changed about as slowly as the dark countryside."
