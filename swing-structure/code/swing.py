"""Swing (directional-change) library, see PLAN.md. Units: bps of price (1e4 * ln mid)."""

from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EDGE_CACHE = ROOT.parent / "microstructure-edge-map" / "cache"  # read-only reuse
CACHE = ROOT / "cache"
OUT = ROOT / "out"
YEARS = list(range(2010, 2023))
P_REF = 4083.276
USD_PER_BPS = P_REF / 1e4  # today's dollars per bp
COST_BPS = 0.168 / USD_PER_BPS
THETA_USD = (1, 2, 3, 5, 10)
THETA_BPS = tuple(u / USD_PER_BPS for u in THETA_USD)
NAMES = ["TREND shallow", "TREND deep", "CONTRACT shallow", "CONTRACT deep",
         "COUNTER mild", "COUNTER deep", "EXPAND mild", "EXPAND deep"]
FAMILY = np.array([0, 0, 1, 1, 2, 2, 3, 3])
FAMILY_NAMES = ["TREND", "CONTRACT", "COUNTER", "EXPAND"]
RW_FAMILY = np.array([1 / 3, 1 / 6, 1 / 3, 1 / 6])


def load_series(yr):
    z = np.load(EDGE_CACHE / f"M1_{yr}.private.npz")
    base = int(z["base"])
    mid = (z["bid"] + z["ask"]) / 2
    pos = np.flatnonzero(np.isfinite(mid))
    y = 1e4 * np.log(mid[pos])
    mins = (base + pos).astype(np.int64)
    blk = np.r_[0, np.cumsum(np.diff(pos) > 30)].astype(np.int64)
    return y, mins, blk


def ny_clock(mins):
    t = pd.to_datetime(mins * 60, unit="s", utc=True).tz_convert("America/New_York")
    return t.hour.to_numpy(), (t.hour * 60 + t.minute).to_numpy()


@nb.njit(cache=True)
def zigzag(y, blk, theta):
    n = len(y)
    o_idx = np.empty(n, np.int64)
    o_dir = np.empty(n, np.int64)
    o_ext = np.empty(n)
    k = 0
    mode = 0
    hi = y[0]
    hi_i = 0
    lo = y[0]
    lo_i = 0
    for i in range(n):
        if i > 0 and blk[i] != blk[i - 1]:
            mode = 0
            hi = y[i]
            hi_i = i
            lo = y[i]
            lo_i = i
            continue
        v = y[i]
        if mode == 0:
            if v > hi:
                hi = v
                hi_i = i
            if v < lo:
                lo = v
                lo_i = i
            if v - lo >= theta and lo_i < i:
                o_idx[k] = i
                o_dir[k] = 1
                o_ext[k] = lo
                k += 1
                mode = 1
                hi = v
                hi_i = i
            elif hi - v >= theta and hi_i < i:
                o_idx[k] = i
                o_dir[k] = -1
                o_ext[k] = hi
                k += 1
                mode = -1
                lo = v
                lo_i = i
        elif mode == 1:
            if v > hi:
                hi = v
                hi_i = i
            elif hi - v >= theta:
                o_idx[k] = i
                o_dir[k] = -1
                o_ext[k] = hi
                k += 1
                mode = -1
                lo = v
                lo_i = i
        else:
            if v < lo:
                lo = v
                lo_i = i
            elif v - lo >= theta:
                o_idx[k] = i
                o_dir[k] = 1
                o_ext[k] = lo
                k += 1
                mode = 1
                hi = v
                hi_i = i
    return o_idx[:k], o_dir[:k], o_ext[:k]


@nb.njit(cache=True)
def bracket(y, blk, mins, idx, d, theta, tmax):
    m = len(idx)
    pnl = np.empty(m)
    hit = np.zeros(m, np.int64)
    dur = np.empty(m)
    n = len(y)
    for k in range(m):
        i0 = idx[k]
        p0 = y[i0]
        j = i0
        res = 0.0
        h = 0
        while True:
            j += 1
            if j >= n or blk[j] != blk[i0] or mins[j] - mins[i0] > tmax:
                j -= 1
                res = d[k] * (y[j] - p0)
                break
            mv = d[k] * (y[j] - p0)
            if mv >= theta:
                res = mv
                h = 1
                break
            if mv <= -theta:
                res = mv
                h = -1
                break
        pnl[k] = res
        hit[k] = h
        dur[k] = mins[j] - mins[i0]
    return pnl, hit, dur


def process(y, mins, blk, theta, tmax=240):
    idx, d, ext = zigzag(y, blk, theta)
    m = len(idx)
    eb = blk[idx]
    # patterns from the last four swing points
    code = np.full(m, -1)
    A = np.full(m, np.nan)
    B = np.full(m, np.nan)
    C = np.full(m, np.nan)
    if m >= 4:
        k = np.arange(3, m)
        ok = eb[k - 3] == eb[k]
        k = k[ok]
        dd = d[k]
        B[k] = dd * (ext[k - 1] - ext[k])
        A[k] = dd * (ext[k - 1] - ext[k - 2])
        C[k] = dd * (ext[k - 3] - ext[k - 2])
        a, b = A[k] / C[k], B[k] / A[k]
        fam = np.where(a > 1, np.where(b < 1, 0, 3), np.where(b < 1, 1, 2))
        deep = np.where(b < 1, b >= 0.5, b >= 1.5).astype(int)
        code[k] = fam * 2 + deep
    # R1: follow until the next event in the block (trailing stop theta)
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), len(y) - 1]
    nxt = np.r_[idx[1:], -1]
    same = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same, nxt, last_of_blk[eb])
    r1 = d * (y[exit_i] - y[idx])
    r1dur = mins[exit_i] - mins[idx]
    r3, r3hit, r3dur = bracket(y, blk, mins, idx, d.astype(np.float64), theta, tmax)
    return dict(idx=idx, mins=mins[idx], dir=d, code=code, A=A, B=B, C=C, r1=r1,
                r1dur=r1dur, r3=r3, r3hit=r3hit, r3dur=r3dur)


def signflip(y, blk, rng):
    r = np.diff(y)
    same = blk[1:] == blk[:-1]
    rr = np.where(same, r * rng.choice([-1.0, 1.0], len(r)), 0.0)
    cs = np.r_[0.0, np.cumsum(rr)]
    first = np.r_[0, np.flatnonzero(np.diff(blk)) + 1]
    start = first[blk]
    return y[start] + cs - cs[start]
