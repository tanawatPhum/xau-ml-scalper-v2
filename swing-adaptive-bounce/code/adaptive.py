"""Volatility-scaled swing bounce (see ../PLAN.md). Reuses the swing-structure loader read-only."""

import sys
from pathlib import Path

import numba as nb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-structure" / "code"))
from swing import COST_BPS, USD_PER_BPS, YEARS, load_series, signflip  # noqa: E402

CACHE = ROOT / "cache"
OUT = ROOT / "out"
U = USD_PER_BPS
KS = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)
WIN, MINN = 60, 30
BIN_EDGES = (1.5, 2.5)
BIN_NAMES = ("small", "mid", "large")
DELAYS = (1, 2)
STOPS = (0.0, 3.0, 2.0)
SIDES = ("fade", "follow")
DISC, VAL = range(2010, 2017), range(2017, 2020)


def sigma60(y, blk, win=WIN, minn=MINN):
    n = len(y)
    r = np.r_[0.0, np.diff(y)]
    same = np.r_[False, blk[1:] == blk[:-1]]
    cs = np.cumsum(np.where(same, r * r, 0.0))
    first = np.r_[0, np.flatnonzero(np.diff(blk)) + 1]
    bs = first[blk]
    i = np.arange(n)
    lo = np.maximum(i - win, bs + 1)
    hi = i - 1
    cnt = hi - lo + 1
    s = cs[np.maximum(hi, 0)] - cs[np.maximum(lo - 1, 0)]
    ok = (cnt >= minn) & (s > 1e-12)  # a flat hour (zero returns) gives no threshold, no signal
    return np.where(ok, np.sqrt(np.maximum(s, 0.0) / np.maximum(cnt, 1) * win), np.nan)


@nb.njit(cache=True)
def zigzag_ad(y, blk, th):
    n = len(y)
    o_idx = np.empty(n, np.int64)
    o_dir = np.empty(n, np.int64)
    o_ext = np.empty(n)
    o_th = np.empty(n)
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
        t = th[i]
        live = (t == t) and (t > 0)
        if mode == 0:
            if v > hi:
                hi = v
                hi_i = i
            if v < lo:
                lo = v
                lo_i = i
            if live and v - lo >= t and lo_i < i:
                o_idx[k] = i
                o_dir[k] = 1
                o_ext[k] = lo
                o_th[k] = t
                k += 1
                mode = 1
                hi = v
                hi_i = i
            elif live and hi - v >= t and hi_i < i:
                o_idx[k] = i
                o_dir[k] = -1
                o_ext[k] = hi
                o_th[k] = t
                k += 1
                mode = -1
                lo = v
                lo_i = i
        elif mode == 1:
            if v > hi:
                hi = v
                hi_i = i
            elif live and hi - v >= t:
                o_idx[k] = i
                o_dir[k] = -1
                o_ext[k] = hi
                o_th[k] = t
                k += 1
                mode = -1
                lo = v
                lo_i = i
        else:
            if v < lo:
                lo = v
                lo_i = i
            elif live and v - lo >= t:
                o_idx[k] = i
                o_dir[k] = 1
                o_ext[k] = lo
                o_th[k] = t
                k += 1
                mode = 1
                hi = v
                hi_i = i
    return o_idx[:k], o_dir[:k], o_ext[:k], o_th[:k]


def events(y, blk, th):
    idx, d, ext, t = zigzag_ad(y, blk, th)
    eb = blk[idx]
    has_b = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(len(idx), np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    brel = B / t
    b = np.where(brel < BIN_EDGES[0], 0, np.where(brel < BIN_EDGES[1], 1, 2)).astype(np.int8)
    return dict(idx=idx, dir=d, th=t, has_b=has_b, bin=b, B=B)


@nb.njit(cache=True)
def apply_stop(y, ent, ex, sgn, stop):
    m = len(ent)
    out_i = ex.copy()
    stopped = np.zeros(m, np.int8)
    for k in range(m):
        if stop[k] <= 0:
            continue
        e = ent[k]
        for t in range(e + 1, ex[k] + 1):
            if sgn[k] * (y[t] - y[e]) <= -stop[k]:
                out_i[k] = t
                stopped[k] = 1
                break
    return out_i, stopped


def trades(ev, y, mins, blk, delay, k_stop, side):
    idx = ev["idx"]
    eb = blk[idx]
    n = len(y)
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    nxt = np.r_[idx[1:], -1]
    same = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same, nxt, last_of_blk[eb])
    ent = np.minimum(idx + delay, n - 1)
    ok = (blk[ent] == eb) & ev["has_b"]
    ex = np.minimum(exit_i + delay, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    sgn = (-1.0 if side == "fade" else 1.0) * ev["dir"][ok].astype(np.float64)
    ent, ex = ent[ok], ex[ok]
    stop = (k_stop * ev["th"][ok]) if k_stop > 0 else np.full(len(ent), -1.0)
    out_i, stopped = apply_stop(y, ent, ex, sgn, stop)
    gross = sgn * (y[out_i] - y[ent])
    tm = mins[ent].astype(np.int64)
    return dict(net=((gross - COST_BPS) * U).astype(np.float32), bin=ev["bin"][ok],
                day=((tm * 60 + 3 * 3600) // 86400).astype(np.int32), t_ent=tm.astype(np.int32),
                stopped=stopped, th_usd=(ev["th"][ok] * U).astype(np.float32),
                hold=(mins[out_i] - mins[ent]).astype(np.int32), b_usd=(ev["B"][ok] * U).astype(np.float32))
