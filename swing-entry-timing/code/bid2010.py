"""BID high/low/close per minute (full-year grid) for 2010, same format as swing-bzone/cache (2011-2019)."""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(r"D:\xau-ml-scalper\data\raw\dukascopy\xauusd\m1\csv")
OUT = Path(__file__).resolve().parents[1] / "cache"
yr = 2010
base = int(pd.Timestamp(f"{yr}-01-01", tz="UTC").value // 60_000_000_000)
end = int(pd.Timestamp(f"{yr + 1}-01-01", tz="UTC").value // 60_000_000_000)
files = sorted((RAW / "bid" / f"year={yr}").glob(f"xauusd_bid_m1_{yr}_*.csv"))
df = pd.concat([pd.read_csv(f, usecols=["timestamp_utc", "high", "low", "close"]) for f in files], ignore_index=True)
t = pd.to_datetime(df["timestamp_utc"], utc=True).astype("int64").to_numpy() // 60_000_000_000
k = (t >= base) & (t < end)
arr = {c: np.full(end - base, np.nan) for c in ("high", "low", "close")}
for c in arr:
    arr[c][t[k] - base] = df[c].to_numpy()[k]
np.savez_compressed(OUT / f"BID_{yr}.private.npz", base=base, **arr)
print(yr, "ok", len(files), "files", int(np.isfinite(arr["close"]).sum()), "minutes")
