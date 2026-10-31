"""Batch-1 factor rows for the two base cells (see ../PLAN.md). 2010-2019 only."""

import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-adaptive-bounce" / "code"))
from adaptive import COST_BPS, U, YEARS, apply_stop, load_series, sigma60  # noqa: E402

CACHE = ROOT / "cache"
RUN_YEARS = [y for y in YEARS if y <= 2019]
KS = (1.0, 1.5)
LARGE = 2.5


@nb.njit(cache=True)
def zigzag_x(y, blk, th):
    n = len(y)
    o_idx = np.empty(n, np.int64)
    o_dir = np.empty(n, np.int64)
    o_ext = np.empty(n)
    o_exi = np.empty(n, np.int64)
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
                o_idx[k], o_dir[k], o_ext[k], o_exi[k], o_th[k] = i, 1, lo, lo_i, t
                k += 1
                mode = 1
                hi = v
                hi_i = i
            elif live and hi - v >= t and hi_i < i:
                o_idx[k], o_dir[k], o_ext[k], o_exi[k], o_th[k] = i, -1, hi, hi_i, t
                k += 1
                mode = -1
                lo = v
                lo_i = i
        elif mode == 1:
            if v > hi:
                hi = v
                hi_i = i
            elif live and hi - v >= t:
                o_idx[k], o_dir[k], o_ext[k], o_exi[k], o_th[k] = i, -1, hi, hi_i, t
                k += 1
                mode = -1
                lo = v
                lo_i = i
        else:
            if v < lo:
                lo = v
                lo_i = i
            elif live and v - lo >= t:
                o_idx[k], o_dir[k], o_ext[k], o_exi[k], o_th[k] = i, 1, lo, lo_i, t
                k += 1
                mode = 1
                hi = v
                hi_i = i
    return o_idx[:k], o_dir[:k], o_ext[:k], o_exi[:k], o_th[:k]


def sigma_long(y, blk, win=1440, minn=720):
    n = len(y)
    r = np.r_[0.0, np.diff(y)]
    same = np.r_[False, blk[1:] == blk[:-1]]
    cs = np.cumsum(np.where(same, r * r, 0.0))
    cv = np.cumsum(same.astype(np.float64))
    i = np.arange(n)
    hi = i - 1
    lo = np.maximum(i - win, 1)
    hi_c, lo_c = np.maximum(hi, 0), np.maximum(lo - 1, 0)
    cnt = np.where(hi >= lo, cv[hi_c] - cv[lo_c], 0.0)
    s = np.where(hi >= lo, cs[hi_c] - cs[lo_c], 0.0)
    ok = (cnt >= minn) & (s > 1e-12)
    return np.where(ok, np.sqrt(s / np.maximum(cnt, 1) * 60), np.nan)


def build_year(y, mins, blk, k):
    n = len(y)
    sig = sigma60(y, blk)
    idx, d, ext, exi, th = zigzag_x(y, blk, k * sig)
    m = len(idx)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(m, np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    brel = B / th
    # structure from the last three legs (needs events k-3..k in the block)
    fam = np.full(m, -1)
    if m >= 4:
        kk = np.arange(3, m)
        okk = eb[kk - 3] == eb[kk]
        kk = kk[okk]
        dd = d[kk]
        Bk = dd * (ext[kk - 1] - ext[kk])
        Ak = dd * (ext[kk - 1] - ext[kk - 2])
        Ck = dd * (ext[kk - 3] - ext[kk - 2])
        a, b = Ak / Ck, Bk / Ak
        fam[kk] = np.where(a > 1, np.where(b < 1, 0, 3), np.where(b < 1, 1, 2))
    # leg and bounce durations
    legtime = np.full(m, np.nan)
    legtime[1:] = (mins[exi[1:]] - mins[exi[:-1]]).astype(np.float64)
    legtime[~same_prev] = np.nan
    bouncetime = (mins[idx] - mins[exi]).astype(np.float64)
    # volatility ratio, 24h range position, k = 3 trend
    sl = sigma_long(y, blk)
    volratio = sig[idx] / sl[idx]
    s = pd.Series(y)
    rmax = s.rolling(1440, min_periods=720).max().to_numpy()
    rmin = s.rolling(1440, min_periods=720).min().to_numpy()
    rng = rmax[idx] - rmin[idx]
    pos_up = (y[idx] - rmin[idx]) / rng
    rangepos = np.where(d == 1, pos_up, 1 - pos_up)
    i3, d3, _, _, _ = zigzag_x(y, blk, 3.0 * sig)
    j = np.searchsorted(i3, idx, side="right") - 1
    htf = np.zeros(m, np.int64)
    okj = j >= 0
    jj = np.where(okj, j, 0)
    htf = np.where(okj & (blk[i3[jj]] == eb) if len(i3) else False, d3[jj] if len(i3) else 0, 0)
    side = -d  # fade
    htf_with = np.where(htf == 0, -1, (htf == side).astype(np.int64))
    # trades: main (fade, delay 1, stop 3 theta) and extension to the following confirmation
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    nxt = np.r_[idx[1:], -1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, nxt, last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev
    ex = np.minimum(exit_i + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    sgn = side.astype(np.float64)
    out_i, stopped = apply_stop(y, ent, ex, sgn, 3.0 * th)
    gross = sgn * (y[out_i] - y[ent])
    net = (gross - COST_BPS) * U
    nxt2 = np.r_[idx[2:], -1, -1]
    same2 = np.r_[eb[2:] == eb[:-2], False, False]
    exit2 = np.where(same2, nxt2, last_of_blk[eb])
    ex2 = np.minimum(exit2 + 1, n - 1)
    ex2 = np.where(blk[ex2] == eb, ex2, exit2)
    ext_ok = (stopped == 0) & same_next & (ex2 > ex)
    extension = np.where(ext_ok, sgn * (y[ex2] - y[ex]) * U, 0.0)
    base = ok & (brel >= LARGE)
    tm = mins[ent].astype(np.int64)
    return dict(net=net[base], ext=extension[base], stop=stopped[base].astype(np.int8),
                legsize=brel[base], legtime=legtime[base], bouncetime=bouncetime[base],
                volratio=volratio[base], hour=((tm % 1440) // 60)[base].astype(np.int8),
                htf=htf_with[base].astype(np.int8), rangepos=rangepos[base], structure=fam[base].astype(np.int8),
                day=((tm * 60 + 3 * 3600) // 86400)[base].astype(np.int32), th_usd=(th * U)[base])


if __name__ == "__main__":
    CACHE.mkdir(exist_ok=True)
    data = {yr: load_series(yr) for yr in RUN_YEARS}
    for k in KS:
        parts = []
        for yr in RUN_YEARS:
            r = build_year(*data[yr], k)
            r["yr"] = np.full(len(r["net"]), yr, np.int16)
            parts.append(r)
        z = {f: np.concatenate([p[f] for p in parts]) for f in parts[0]}
        np.savez(CACHE / f"ROWS_k{k:g}.private.npz", **z)
        for per, lo, hi in (("2010-16", 2010, 2016), ("2017-19", 2017, 2019)):
            m = (z["yr"] >= lo) & (z["yr"] <= hi)
            print(f"k {k:g} {per}: n {m.sum()}, O1 net {z['net'][m].mean():+.3f}, O1+O2 "
                  f"{(z['net'][m] + z['ext'][m]).mean():+.3f}, stop {z['stop'][m].mean() * 100:.1f}%", flush=True)
