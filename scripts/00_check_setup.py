"""
00_check_setup.py — confirm the environment works before any real analysis.

What it checks:
  1. Python can read the Earth Engine project ID from .env
  2. Earth Engine accepts our login
  3. The VIIRS monthly collection is reachable (count + latest month)
  4. Our nesting-site list loads
"""
import os
from pathlib import Path

import ee                      # Google Earth Engine
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]          # repo folder
load_dotenv(ROOT / ".env")                          # read EE_PROJECT from .env

project = os.getenv("EE_PROJECT")
if not project or project.startswith("your-"):
    raise SystemExit("Set EE_PROJECT in .env first (copy .env.example to .env).")

# 1-2. Connect to Earth Engine using the cloud project
ee.Initialize(project=project)
print(f"Earth Engine OK (project: {project})")

# 3. The monthly night-light collection
viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
n_months = viirs.size().getInfo()
latest = ee.Date(viirs.aggregate_max("system:time_start")).format("YYYY-MM").getInfo()
print(f"VIIRS monthly images: {n_months}, latest month: {latest}")

# 4. Our sites
sites = pd.read_csv(ROOT / "data" / "sites" / "nesting_sites.csv")
print(f"\nNesting sites loaded: {len(sites)}")
print(sites[["site_id", "site_name", "lat", "lon", "role"]].to_string(index=False))
