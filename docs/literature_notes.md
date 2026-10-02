# Literature notes (M0) — read 2026-10-02

Hedged summaries from the PDFs in `papers/`. Behera et al. (2016) is from its abstract only.

## What each paper did

| Paper | Where | Satellite / data | Snapshot or change over time? | How "real" was tested | LED / blue light handled? |
|---|---|---|---|---|---|
| Hu et al. 2018 (Env. Pollution) | Florida, 3 species | VIIRS annual composite V1 (`vcm-orm-ntl`; only 2015-2016 exist in V1) vs nest density 2012-2016 | **Snapshot** (space, not time) | GLM + spatial models; light-pollution threshold from Kamrowski 2012 | Not discussed |
| Weishampel et al. 2016 (RSEC) | Florida, 368 x ~1 km beach segments | DMSP 1992-2012 | Both; ~2/3 of beaches got *darker* in DMSP | Spatial autoregressive models | Notes coarse data; suggests ground checks |
| Kamrowski et al. 2012 (ESR) | Australia | DMSP | Snapshot; risk ranking | GIS overlay | — |
| Kamrowski et al. 2014 (GCB) | Australia, 19 management units | DMSP 1993-2010 | **Change over time** | Linear mixed models | **Yes**: OLS misses LEDs, so light may have kept rising unseen |
| Mazor et al. 2013 (Biol. Cons.) | Israel coast | SAC-C + ISS photos | Snapshot | GLMs | Briefly |
| Leader et al. 2024 (Turk. J. Zool.) | 13 green-turtle beaches, Türkiye & Cyprus | **VIIRS 2012-2020**, annual means (Radiance Light Trends app) | **Change over time**: 4 beaches rising; 2020 radiance 1.9-2.6x 2012 | Pearson r vs year; **no control area / noise floor** | Mentioned as a concern only |
| Simantiris et al. 2025 (JMSE) | Kyparissia Bay, Greece | VIIRS/DMSP from lightpollutionmap.info + drone + light meter | Mostly snapshot; decade of radiance used for context | Kruskal-Wallis by segment | — |
| Karnad et al. 2009 (Biol. Cons.) | **Rushikulya** | Field arena trials | — | Experiments | Hatchlings prefer short (blue) wavelengths; up to ~50% misorientation modelled; Casuarina belt ~50 m back acts as light barrier |
| Shanker et al. 2004* (Biol. Cons.) | **Odisha** | Population data 1976-1999 | — | — | — | 
| Behera et al. 2016 (IJMS) | **Gahirmatha** | Beach surveys 2008-2011 | — | — | — |
| Elvidge et al. 2017; 2021 | Global | VIIRS products | — | Annual V2 uses a 12-month median to drop fires/boats; background < ~1 nW/cm2/sr | — |
| Kyba et al. 2023 (Science) | Global, citizen science | Star visibility 2011-2022 | Change | — | **Key**: sky brightness up ~7-10%/yr, faster than satellites show; VIIRS can't see < 500 nm |
| Levin et al. 2020 (RSE) | Review | All night-light sensors | — | — | LED spectral bias discussed at length |
| Khanduri et al. 2025 (WIREs Water) | Review, Indian authors (WII) | — | — | — | Calls for monitoring "hotspots and safe zones"; cites Behera & Mohanta 2018 on nesting shifting away from light at Rushikulya |

*PDF dated 2003, issue 2004 (vol. 115). Cite as 2004 to match the DOI record.

## Site facts picked up
- Odisha has **three arribada beaches**: Gahirmatha, Devi river mouth, Rushikulya (Shanker 2004).
- Rushikulya: **nesting is on a ~4 km beach NORTH of the river mouth** (Shanker 2004) -> our point sits at the south end; centre the beach buffer ~2 km north, or use a 4 km beach line.
- Rushikulya light sources (Karnad 2009): nearby villages, the Chennai-Kolkata national highway, a chemical factory.
- Gahirmatha: nesting shifted onto islands; erosion and tetrapod armouring injured/killed turtles (Behera 2016).

## Gaps — confirmed vs revised
1. **CONFIRMED**: no satellite night-light study of Odisha's arribada beaches in this set or in searches (not exhaustive).
2. **REVISED**: VIIRS trends at nesting beaches HAVE been done once (Leader 2024, Mediterranean, 2012-2020). We cannot claim "first VIIRS trend study at turtle beaches". What is still missing there: robust trend tests, a noise floor from control areas, and context against the rest of the coastline.
3. **CONFIRMED**: Florida work (Hu 2018) is a snapshot linking light to nesting, not a trend.
4. **CONFIRMED**: harm is demonstrated in the field at Rushikulya (Karnad 2009) but never linked to a satellite record.
5. **CONFIRMED**: most satellite studies mention LEDs only in passing; Kamrowski 2014 and Kyba 2023 give us the evidence to treat it as a real limitation.

## What this changes in our method
- Use **robust trends (Theil-Sen + Mann-Kendall)** and a **noise floor from controls**: this is our methodological step up from Leader 2024.
- Coast-wide **segments** have precedent (Weishampel 2016 used ~1 km segments).
- Prefer the **annual V2.2 (12-month median)** as the cross-check because it filters boats and fires; monthly V1 does not.
- Report **seasonal (nesting/emergence months)** light, which no paper here did for arribada beaches.
