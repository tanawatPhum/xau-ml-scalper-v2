"""Shared helpers: cached arrays, S60, New York time."""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
OUT = ROOT / "out"
YEARS = list(range(2010, 2023))
OWNER_BPS = 0.168 / 4083.276 * 1e4  # owner's broker spread in bps of price


def load(yr):
    z = np.load(CACHE / f"M1_{yr}.private.npz")
    bid, ask = z["bid"], z["ask"]
    return int(z["base"]), bid, ask, (bid + ask) / 2


def s60(bid):
    """60-min realized vol of BID closes ending before each minute (NaN if < 50 pairs)."""
    d = np.diff(bid)
    ok = np.isfinite(d)
    d2 = np.r_[0.0, np.where(ok, d * d, 0.0)]
    pc = np.r_[0, ok.astype(np.int64)]
    c2, cp = np.cumsum(d2), np.cumsum(pc)
    n = len(bid)
    out = np.full(n, np.nan)
    i = np.arange(61, n)
    # pairs (k-1, k) with k in [i-59, i-1]
    ssum = c2[i - 1] - c2[i - 60]
    psum = cp[i - 1] - cp[i - 60]
    v = np.sqrt(ssum)
    out[i] = np.where(psum >= 50, v, np.nan)
    return out


def ny_time(base, n):
    t = pd.to_datetime((base + np.arange(n)) * 60, unit="s", utc=True).tz_convert(
        "America/New_York")
    return t.hour.to_numpy(), (t.hour.to_numpy() * 2 + t.minute.to_numpy() // 30), \
        t.weekday.to_numpy()
