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
