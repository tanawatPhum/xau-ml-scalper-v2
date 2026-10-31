"""Per-signal P&L of rules A and B (locked filters) with stop s x theta from the entry, 2010-2019 (see ../PLAN.md).
Writes out/SIGNALS.private.pkl. Close-based stops for the selection; intrabar stops kept for the sensitivity only."""
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
SPREAD = 0.168
SS = (1.0, 1.25, 1.5, 2.0, 2.5, 3.0)


def bid_path(yr):
    p = SB / "swing-bzone" / "cache" / f"BID_{yr}.private.npz"
    return np.load(p if p.exists() else SB / "swing-entry-timing" / "cache" / f"BID_{yr}.private.npz")


@nb.njit(cache=True)
def run(C, H, L, ent, ex, sgn, th, s, intrabar, net, stp, hold):
    for k in range(len(ent)):
        e = ent[k]
        x = ex[k]
        g = sgn[k]
        y0 = 1e4 * np.log(C[e])
        o = x
        px = C[x]
        st = 0
        for t in range(e + 1, x + 1):
            if intrabar:
                adv = H[t] if g < 0 else L[t]
                if g * (1e4 * np.log(adv) - y0) <= -s * th[k]:
                    o = t
                    px = C[e] * np.exp(-g * s * th[k] / 1e4)
                    st = 1
                    break
            if g * (1e4 * np.log(C[t]) - y0) <= -s * th[k]:
                o = t
                px = C[t]
                st = 1
                break
        net[k] = g * (px - C[e]) - SPREAD
        stp[k] = st
        hold[k] = o - e


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
    H = np.where(np.isfinite(bz["high"][pos]), np.fmax(bz["high"][pos] + hs, C), C)
    L = np.where(np.isfinite(bz["low"][pos]), np.fmin(bz["low"][pos] + hs, C), C)
    e, x, sg, tq = ent[ok], ex_[ok], -d[ok].astype(np.float64), th[ok]
    te = mins[e].astype(np.int64)
    R = pd.DataFrame(dict(rule=rule, yr=yr, t_ent=te, day=(te * 60 + 3 * 3600) // 86400, theta_usd=tq * C[e] / 1e4, leg_ratio=B[ok] / tq))
    R["R"] = R["theta_usd"] / SPREAD
    c = LOCK[rule]
    R["keep"] = (R["R"] >= c["R_min"]) & (R["leg_ratio"] >= c["leg"])
    for s in SS:
        for ib in (False, True):
            net = np.zeros(len(e))
            stp = np.zeros(len(e), np.int8)
            hold = np.zeros(len(e), np.int64)
            run(C, H, L, e, x, sg, tq, s, ib, net, stp, hold)
            tag = f"s{s}" + ("_ib" if ib else "")
            R[tag], R[tag + "_stop"], R[tag + "_hold"] = net, stp, hold
            if not ib:
                R[tag + "_t_exit"] = mins[np.minimum(e + hold, len(mins) - 1)].astype(np.int64)
    return R


S = pd.concat([run_year(yr, r) for r in RULES for yr in range(2010, 2020)], ignore_index=True)
S.to_pickle(ROOT / "out" / "SIGNALS.private.pkl")
old = pd.read_pickle(SB / "swing-cost-ratio" / "out" / "TRADES.private.pkl")
for r in RULES:
    a, b = S[S.rule == r], old[old.rule == r]
    print(f"reproduction rule {r}: n {len(a)} vs {len(b)}; s3.0 net sum {a['s3.0'].sum():.3f} vs {b['net'].sum():.3f}; kept {int(a['keep'].sum())}")
