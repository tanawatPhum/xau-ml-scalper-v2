"""Dense per-year minute arrays of BID/ASK closes (both sides traded), 2010-2022 only."""

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(r"D:\xau-ml-scalper\data\raw\dukascopy\xauusd\m1\csv")
OUT = Path(__file__).resolve().parents[1] / "cache"
YEARS = range(2010, 2023)


def read_side(side, yr):
    files = sorted((RAW / side / f"year={yr}").glob(f"xauusd_{side}_m1_{yr}_*.csv"))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    t = pd.to_datetime(df["timestamp_utc"], utc=True).astype("int64") // 60_000_000_000
    active = (df["volume"].to_numpy() > 0) | (df["high"].to_numpy() > df["low"].to_numpy())
    return t.to_numpy()[active], df[["open", "high", "low", "close"]].to_numpy()[active]


def main():
    assert max(YEARS) <= 2022
    OUT.mkdir(exist_ok=True)
    for yr in YEARS:
        base = int(pd.Timestamp(f"{yr}-01-01", tz="UTC").value // 60_000_000_000)
        end = int(pd.Timestamp(f"{yr + 1}-01-01", tz="UTC").value // 60_000_000_000)
        n = end - base
        out = {}
        for side in ("bid", "ask"):
            t, v = read_side(side, yr)
            k = (t >= base) & (t < end)
            arr = np.full(n, np.nan)
            arr[t[k] - base] = v[k, 3]
            out[side] = arr
        both = np.isfinite(out["bid"]) & np.isfinite(out["ask"])
        bid = np.where(both, out["bid"], np.nan)
        ask = np.where(both, out["ask"], np.nan)
        np.savez_compressed(OUT / f"M1_{yr}.private.npz", base=base, bid=bid, ask=ask)
        sp = (ask - bid)[both]
        print(yr, "minutes both traded", int(both.sum()), "spread median",
              round(float(np.median(sp)), 4), "neg spreads", int((sp < 0).sum()), flush=True)


if __name__ == "__main__":
    main()
