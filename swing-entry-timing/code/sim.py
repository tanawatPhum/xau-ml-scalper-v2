"""Simulate entry policies on every signal of rules A and B, 2010-2019 (see ../PLAN.md).
Writes out/SIGNALS.private.pkl: one row per signal with the base and every policy's net $/oz (NaN = no trade)."""
import importlib.util
import json
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SB = ROOT.parent
sys.path.insert(0, str(SB / "swing-adaptive-bounce" / "code"))
from adaptive import load_series, sigma60  # noqa: E402

_spec = importlib.util.spec_from_file_location("factors_build", SB / "swing-factors-b1" / "code" / "build.py")
_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fb)
sigma_long, zigzag_x = _fb.sigma_long, _fb.zigzag_x
EDGE = SB / "microstructure-edge-map" / "cache"
LOCK = json.load(open(SB / "swing-cost-ratio" / "out" / "LOCK.json"))
RULES = {"A": (1.0, "eff"), "B": (1.5, "s60")}
SPREAD, MARGIN, BIG = 0.168, 0.05, 10 ** 9
CELLS = ([("base", 0, 0.0, 0, 0.0)] + [(f"L_y{y}_W{'inf' if W == BIG else W}", 1, y, W, 0.0) for y in (0.1, 0.25, 0.5) for W in (10, 30, BIG)]
         + [(f"LF_y{y}_W{W}", 2, y, W, 0.0) for y in (0.1, 0.25, 0.5) for W in (10, 30)]
         + [(f"D_z{z}", 3, 0.0, 0, z) for z in (0.1, 0.25, 0.5)])


def bid_path(yr):
    p = SB / "swing-bzone" / "cache" / f"BID_{yr}.private.npz"
    return np.load(p if p.exists() else ROOT / "cache" / f"BID_{yr}.private.npz")


@nb.njit(cache=True)
def sim(kind, yf, W, z, C, H, L, ent, ex, sgn, th, net, stp, fi, ext):
    for k in range(len(ent)):
        e = ent[k]
        x = ex[k]
        s = sgn[k]
        E0 = C[e]
        tu = th[k] * E0 / 1e4
        f = -1
        px = 0.0
        if kind == 0:
            f = e
            px = E0
        elif kind == 1 or kind == 2:
            lim = E0 - s * yf * tu
            last = min(e + W, x - 2)
            for t in range(e + 1, last + 1):
                if s < 0:
                    if H[t] >= lim + MARGIN:
                        f = t
                        px = lim
                        break
                else:
                    if L[t] <= lim - MARGIN:
                        f = t
                        px = lim
                        break
            if f < 0 and kind == 2:
                t = e + W
                if t < x - 1:
                    f = t
                    px = C[t]
        else:
            m = E0
            for t in range(e + 1, x - 1):
                if s < 0:
                    if C[t] > m:
                        m = C[t]
                    elif C[t] <= m - z * tu:
                        f = t + 1
                        break
                else:
                    if C[t] < m:
                        m = C[t]
                    elif C[t] >= m + z * tu:
                        f = t + 1
                        break
            if f >= 0:
                px = C[f]
        if kind == 0:
            # bounce extension after E0 (closes, until the exit), in theta units
            m = E0
            for t in range(e + 1, x):
                if -s * (C[t] - m) > 0:
                    m = C[t]
            ext[k] = -s * (m - E0) / tu
        if f < 0:
            net[k] = np.nan
            continue
        yp = 1e4 * np.log(px)
        o = x
        st = 0
        for t in range(f + 1, x + 1):
            if s * (1e4 * np.log(C[t]) - yp) <= -3.0 * th[k]:
                o = t
                st = 1
                break
        net[k] = s * (C[o] - px) - SPREAD
        stp[k] = st
        fi[k] = f - e


def run_year(yr, rule):
    k, kind = RULES[rule]
    y, mins, blk = load_series(yr)
    n = len(y)
    s60 = sigma60(y, blk)
    sl = sigma_long(y, blk)
    seff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    T = k * (seff if kind == "eff" else s60)
    idx, d, ext, exi, th = zigzag_x(y, blk, T)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(len(idx), np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (B / th >= 2.5)
    ex_ = np.minimum(exit_i + 1, n - 1)
    ex_ = np.where(blk[ex_] == eb, ex_, exit_i)
    ok &= ex_ > ent
    zp = np.load(EDGE / f"M1_{yr}.private.npz")
    base = int(zp["base"])
    pos = (mins - base).astype(np.int64)
    bid, ask = zp["bid"][pos], zp["ask"][pos]
    C = (bid + ask) / 2
    bz = bid_path(yr)
    assert int(bz["base"]) == base
    hs = (ask - bid) / 2
    H = bz["high"][pos] + hs
    L = bz["low"][pos] + hs
    H = np.where(np.isfinite(H), np.fmax(H, C), C)
    L = np.where(np.isfinite(L), np.fmin(L, C), C)
    e, x, sg, tq = ent[ok], ex_[ok], -d[ok].astype(np.float64), th[ok]
    te = mins[e].astype(np.int64)
    R = pd.DataFrame(dict(rule=rule, yr=yr, t_ent=te, t_exit_base=mins[x].astype(np.int64), day=(te * 60 + 3 * 3600) // 86400,
                          hour=(te // 60) % 24, side=np.where(sg < 0, "sell", "buy"), price=C[e], theta_usd=tq * C[e] / 1e4,
                          leg_ratio=B[ok] / tq))
    R["R"] = R["theta_usd"] / SPREAD
    c = LOCK[rule]
    R["keep"] = (R["R"] >= c["R_min"]) & (R["leg_ratio"] >= c["leg"])
    for name, kd, yf, W, z in CELLS:
        net = np.full(len(e), np.nan)
        stp = np.zeros(len(e), np.int8)
        fi = np.full(len(e), -1, np.int64)
        ext_ = np.full(len(e), np.nan)
        sim(kd, yf, W, z, C, H, L, e, x, sg, tq, net, stp, fi, ext_)
        R[name] = net
        R[name + "_stop"] = stp
        R[name + "_wait"] = fi
        if kd == 0:
            R["ext_theta"] = ext_
    return R


S = pd.concat([run_year(yr, r) for r in RULES for yr in range(2010, 2020)], ignore_index=True)
S.to_pickle(ROOT / "out" / "SIGNALS.private.pkl")
old = pd.read_pickle(SB / "swing-cost-ratio" / "out" / "TRADES.private.pkl")
for r in RULES:
    a, b = S[S.rule == r], old[old.rule == r]
    print(f"reproduction rule {r}: n {len(a)} vs {len(b)}; base net sum {a['base'].sum():.3f} vs {b['net'].sum():.3f}; "
          f"kept {int(a['keep'].sum())}", flush=True)
cols = [c[0] for c in CELLS]
print("fill rate on kept signals 2010-16:")
dev = S[S["keep"] & (S["yr"] <= 2016)]
print(dev.groupby("rule")[cols].apply(lambda g: g.notna().mean()).round(3).T.to_string())
