# Dark Skies for Hatchlings (turtle-light-watch)

*Work in progress.* Are the olive ridley mass-nesting beaches of Odisha, India getting brighter
at night? A satellite night-light (VIIRS) analysis, 2014-2026.

## Question
See [docs/questions.md](docs/questions.md).

## Why it matters
TODO

## Data
- VIIRS DNB monthly composites (`NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`), Earth Observation Group, Colorado School of Mines, via Google Earth Engine.
- VIIRS annual composites V2.2 (`NOAA/VIIRS/DNB/ANNUAL_V22`), as a cross-check.
- Nesting beaches: hand-compiled list of the three well-known mass-nesting sites
  ([data/sites/nesting_sites.csv](data/sites/nesting_sites.csv)) at ~1 km precision, each with a source.
  These locations are already widely published; no new or finer nest locations are added.

## Method
TODO

## Findings
TODO (hedged)

## Limitations
TODO. Includes: VIIRS cannot see light below ~500 nm (blue-rich LEDs), 464 m pixels vs narrow beaches,
one overpass per night (~01:30), no light direction or shielding, no hatchling outcome data.

## How to run
1. `py -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
2. `pip install -r requirements.txt`
3. `earthengine authenticate`
4. Copy `.env.example` to `.env` and set `EE_PROJECT`.
5. `python scripts/00_check_setup.py`

## Credits
Code written with the help of an AI assistant; questions, decisions and interpretation are mine.
