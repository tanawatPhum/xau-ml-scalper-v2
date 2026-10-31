"""Per-minute Dukascopy tick volume (bid + ask), full-year minute grid, 2010-2019 only."""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(r"D:\xau-ml-scalper\data\raw\dukascopy\xauusd\m1\csv")
OUT = Path(__file__).resolve().parents[1] / "cache"
YEARS = range(2010, 2020)

OUT.mkdir(exist_ok=True)
assert max(YEARS) <= 2019
for yr in YEARS:
    base = int(pd.Timestamp(f"{yr}-01-01", tz="UTC").value // 60_000_000_000)
    end = int(pd.Timestamp(f"{yr + 1}-01-01", tz="UTC").value // 60_000_000_000)
    vol = np.zeros(end - base, np.float32)
    for side in ("bid", "ask"):
        files = sorted((RAW / side / f"year={yr}").glob(f"xauusd_{side}_m1_{yr}_*.csv"))
        df = pd.concat([pd.read_csv(f, usecols=["timestamp_utc", "volume"]) for f in files], ignore_index=True)
        t = pd.to_datetime(df["timestamp_utc"], utc=True).astype("int64").to_numpy() // 60_000_000_000
        k = (t >= base) & (t < end)
        np.add.at(vol, t[k] - base, df["volume"].to_numpy()[k].astype(np.float32))
    np.savez_compressed(OUT / f"VOL_{yr}.private.npz", base=base, vol=vol)
    print(yr, "minutes with volume", int((vol > 0).sum()), "median volume (active)", float(np.median(vol[vol > 0])), flush=True)
