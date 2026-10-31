"""Rule C candidates for swing v2 (see ../PLAN.md): trades of 16 cells, 2010-2019. Uses the frozen swing_v1.py unchanged.
Writes out/C_TRADES.private.pkl (all cells, all years) - selection reads <= 2016 only."""
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SB = ROOT.parent
sys.path.insert(0, str(SB / "swing-v1" / "code"))
import swing_v1 as v1  # noqa: E402

TH_MIN = v1.RULES["A"]["theta_min_usd"]
SP = v1.SPREAD_USD


def theta(kind, k, s60, sd):
    if kind == "s60":
        return k * s60
    if kind == "eff":
        return k * np.where(np.isfinite(sd), np.fmax(s60, sd), s60)
    return k * sd


def swing_frame(y, blk, th):
    idx, d, ext, exi, thc = v1.zigzag(y, blk, th)
    n = len(y)
    eb = blk[idx]
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    nxt = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ex = np.minimum(nxt + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, nxt)
    return idx, d, ext, thc, eb, nxt, ex


def fade(y, blk, mid, th, leg_min, theta_min):
    """v1 mechanics (same code path as swing_v1.trades_year)."""
    n = len(y)
    idx, d, ext, thc, eb, nxt, ex = swing_frame(y, blk, th)
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    leg = np.full(len(idx), np.nan)
    leg[1:] = d[1:] * (ext[:-1] - ext[1:])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (leg / thc >= 2.5) & (ex > ent)
    ok &= (thc * mid[ent] / 1e4 >= theta_min) & (leg / thc >= leg_min)
    sgn = -d[ok].astype(np.float64)
    e, x = ent[ok], ex[ok]
    out_i, st = v1.apply_stop(y, e, x, sgn, 3.0 * thc[ok])
    return e, out_i, sgn, thc[ok], st


@nb.njit(cache=True)
def leg_ride(y, idx, d, ext, nxt, ex, th, m, e_o, x_o, s_o, t_o):
    k = 0
    for j in range(len(idx)):
        trig = -1
        for t in range(idx[j] + 1, nxt[j]):
            tt = th[t]
            if tt == tt and tt > 0 and d[j] * (y[t] - ext[j]) >= m * tt:
                trig = t
                break
        if trig < 0 or trig + 1 >= ex[j]:
            continue
        e_o[k] = trig + 1
        x_o[k] = ex[j]
        s_o[k] = d[j]
        t_o[k] = th[trig]
        k += 1
    return k


@nb.njit(cache=True)
def follow_fail(y, last_of, e_src, x_src, s_src, th_src, xf, e_o, x_o, s_o, t_o, st_o):
    k = 0
    busy = -1
    for i in range(len(e_src)):
        e0 = e_src[i]
        s = s_src[i]
        th = th_src[i]
        trig = -1
        for t in range(e0 + 1, x_src[i] + 1):
            if s * (y[t] - y[e0]) <= -xf * th:
                trig = t
                break
        if trig < 0:
            continue
        e = trig + 1
        last = last_of[e0]
        if e <= busy or e > last:
            continue
        g = -s
        best = y[e]
        xo = last
        st = 0
        for t in range(e + 1, last + 1):
            if g * (y[t] - y[e0]) <= 0.0:
                xo = t
                st = 1
                break
            if g * y[t] > g * best:
                best = y[t]
            elif g * (best - y[t]) >= th:
                xo = min(t + 1, last)
                break
        e_o[k] = e
        x_o[k] = xo
        s_o[k] = g
        t_o[k] = th
        st_o[k] = st
        k += 1
        busy = xo
    return k


@nb.njit(cache=True)
def breakout(y, blk, th, f, L, e_o, x_o, s_o, t_o, st_o):
    n = len(y)
    k = 0
    bs = 0
    i = 0
    while i < n:
        if i > 0 and blk[i] != blk[i - 1]:
            bs = i
        tt = th[i]
        if i - bs >= L and tt == tt and tt > 0:
            mx = -1e18
            mn = 1e18
            for j in range(i - L, i):
                if y[j] > mx:
                    mx = y[j]
                if y[j] < mn:
                    mn = y[j]
            g = 0.0
            if y[i] > mx:
                g = 1.0
            elif y[i] < mn:
                g = -1.0
            e = i + 1
            if g != 0.0 and e < n and blk[e] == blk[i]:
                best = y[e]
                xo = -1
                st = 0
                j = e + 1
                while j < n and blk[j] == blk[e]:
                    if g * (y[j] - y[e]) <= -3.0 * tt:
                        xo = j
                        st = 1
                        break
                    if g * y[j] > g * best:
                        best = y[j]
                    elif g * (best - y[j]) >= f * tt:
                        xo = j + 1 if (j + 1 < n and blk[j + 1] == blk[e]) else j
                        break
                    j += 1
                if xo < 0:
                    xo = j - 1
                e_o[k] = e
                x_o[k] = xo
                s_o[k] = g
                t_o[k] = tt
                st_o[k] = st
                k += 1
                i = xo
        i += 1
    return k


def frame(cell, yr, e, x, s, th, st, mid, mins, theta_min=TH_MIN):
    tu = th * mid[e] / 1e4
    keep = tu >= theta_min
    e, x, s, th, st, tu = e[keep], x[keep], s[keep], th[keep], st[keep], tu[keep]
    gross = s * (mid[x] - mid[e])
    te = mins[e]
    return pd.DataFrame(dict(cell=cell, yr=yr, t_entry=te, t_exit=mins[x], day=(te * 60 + 3 * 3600) // 86400,
                             side=np.where(s > 0, "BUY", "SELL"), theta_usd=tu, stopped=np.asarray(st) == 1, gross=gross,
                             net_usd_oz=gross - SP, net_thb=(gross - SP) * v1.OZ * v1.FX))


def year(yr):
    y, mins, blk, mid = v1.load_series(yr)
    n = len(y)
    s60 = v1.sigma60(y, blk)
    sd = v1.sigma1440(y, blk)
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    last_of = last_of_blk[blk]
    parts = []
    # v1 sources (reproduction + CF sources)
    src = {}
    for r, (kind, kk) in {"A": ("eff", 1.0), "B": ("s60", 1.5)}.items():
        p = v1.RULES[r]
        e, o, s, th, st = fade(y, blk, mid, theta(kind, kk, s60, sd), p["leg_min"], p["theta_min_usd"])
        src[r] = (e, o, s, th)
        parts.append(frame(f"v1_{r}", yr, e, o, s, th, st, mid, mins, theta_min=p["theta_min_usd"]))
    # CS: slower-scale fade
    for name, kind, kk in (("CS_2eff", "eff", 2.0), ("CS_3eff", "eff", 3.0), ("CS_1.5d", "d", 1.5), ("CS_2d", "d", 2.0)):
        e, o, s, th, st = fade(y, blk, mid, theta(kind, kk, s60, sd), 2.5, TH_MIN)
        parts.append(frame(name, yr, e, o, s, th, st, mid, mins))
    # CL: ride the big leg
    for tname, kind, kk in (("A", "eff", 1.0), ("B", "s60", 1.5)):
        th_s = theta(kind, kk, s60, sd)
        idx, d, ext, thc, eb, nxt, ex = swing_frame(y, blk, th_s)
        for m in (2.0, 2.5, 3.5):
            E, X, S, T = (np.zeros(len(idx), np.int64), np.zeros(len(idx), np.int64), np.zeros(len(idx)), np.zeros(len(idx)))
            kq = leg_ride(y, idx, d.astype(np.float64), ext, nxt, ex, th_s, m, E, X, S, T)
            E, X, S, T = E[:kq], X[:kq], S[:kq], T[:kq]
            o, st = v1.apply_stop(y, E, X, S, 3.0 * T)
            parts.append(frame(f"CL_{tname}_m{m}", yr, E, o, S, T, st, mid, mins))
    # CF: follow a failing v1 fade
    for r in ("A", "B"):
        e0, o0, s0, th0 = src[r]
        for xf in (1.0, 1.5):
            m_ = len(e0)
            E, X, S, T, ST = (np.zeros(m_, np.int64), np.zeros(m_, np.int64), np.zeros(m_), np.zeros(m_), np.zeros(m_, np.int8))
            kq = follow_fail(y, last_of, e0, o0, s0, th0, xf, E, X, S, T, ST)
            parts.append(frame(f"CF_{r}_x{xf}", yr, E[:kq], X[:kq], S[:kq], T[:kq], ST[:kq], mid, mins))
    # CP: 240-minute breakout
    th_a = theta("eff", 1.0, s60, sd)
    for f in (1.0, 2.0):
        E, X, S, T, ST = (np.zeros(n // 10, np.int64), np.zeros(n // 10, np.int64), np.zeros(n // 10), np.zeros(n // 10), np.zeros(n // 10, np.int8))
        kq = breakout(y, blk, th_a, f, 240, E, X, S, T, ST)
        parts.append(frame(f"CP_f{f}", yr, E[:kq], X[:kq], S[:kq], T[:kq], ST[:kq], mid, mins))
    print(yr, "done", flush=True)
    return pd.concat(parts, ignore_index=True)


D = pd.concat([year(yr) for yr in range(2010, 2020)], ignore_index=True)
D.to_pickle(ROOT / "out" / "C_TRADES.private.pkl")
ref = pd.read_pickle(SB / "swing-v1" / "out" / "V1_TRADES_2010_2019.private.pkl")
for r in ("A", "B"):
    a, b = D[D["cell"] == f"v1_{r}"], ref[ref["rule"] == r]
    print(f"reproduction v1 {r}: n {len(a)} vs {len(b)}; net THB {a['net_thb'].sum():,.1f} vs {b['net_thb'].sum():,.1f}")
dev = D[D["yr"] <= 2016]
print(dev.groupby("cell").agg(n=("net_usd_oz", "size"), net=("net_usd_oz", "mean"), gross=("gross", "mean"), win=("net_usd_oz", lambda v: (v > 0).mean()),
                              stop=("stopped", "mean"), theta=("theta_usd", "median"), thb=("net_thb", "sum")).round(3).to_string())
