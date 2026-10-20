"""Add the US price level to data/wdi_africa_long.csv.

Pulls WDI FP.CPI.TOTL (consumer price index, 2010 = 100) for the United States
and merges it on `year` as a `us_cpi` column, so the notebooks can deflate the
dollar unit-revenue index X = P/S a second time into the real exchange rate
Q = X / P*.  Idempotent: rerunning overwrites the column in place.

Usage:  python source/fetch_wdi_us_cpi.py
"""

import io
import json
import urllib.request
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "wdi_africa_long.csv"
URL = ("https://api.worldbank.org/v2/country/USA/indicator/FP.CPI.TOTL"
       "?format=json&per_page=500")


def fetch_us_cpi():
    with urllib.request.urlopen(URL, timeout=60) as r:
        payload = json.load(io.TextIOWrapper(r, encoding="utf-8"))
    rows = [(int(d["date"]), d["value"]) for d in payload[1] if d["value"] is not None]
    return (pd.DataFrame(rows, columns=["year", "us_cpi"])
              .sort_values("year").reset_index(drop=True))


def main():
    us = fetch_us_cpi()
    df = pd.read_csv(DATA)
    df = df.drop(columns=[c for c in ("us_cpi",) if c in df.columns])
    df = df.merge(us, on="year", how="left")
    df.to_csv(DATA, index=False)
    print(f"{DATA}: merged us_cpi for {us['year'].min()}-{us['year'].max()} "
          f"({df['us_cpi'].notna().sum()} of {len(df)} rows matched)")


if __name__ == "__main__":
    main()
