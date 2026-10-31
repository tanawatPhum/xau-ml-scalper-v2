"""Trades of frozen rules A and B, 2010-2019, at the time's price, with theta$ and leg ratio at entry."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SB = ROOT.parent
sys.path.insert(0, str(SB / "swing-adaptive-bounce" / "code"))
from adaptive import apply_stop, load_series, sigma60  # noqa: E402

_spec = importlib.util.spec_from_file_location("factors_build", SB / "swing-factors-b1" / "code" / "build.py")
_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fb)
sigma_long, zigzag_x = _fb.sigma_long, _fb.zigzag_x
EDGE = SB / "microstructure-edge-map" / "cache"
RULES = {"A": (1.0, "eff"), "B": (1.5, "s60")}
SPREAD = 0.168


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
    sgn = -d[ok].astype(np.float64)
    e = ent[ok]
    out_i, stopped = apply_stop(y, e, ex_[ok], sgn, 3.0 * th[ok])
    zp = np.load(EDGE / f"M1_{yr}.private.npz")
    pos = (mins - int(zp["base"])).astype(np.int64)
    bid, ask = zp["bid"][pos], zp["ask"][pos]
    mid = (bid + ask) / 2
    gross = sgn * (mid[out_i] - mid[e])
    te = mins[e].astype(np.int64)
    return pd.DataFrame(dict(rule=rule, yr=yr, t_ent=te, t_exit=mins[out_i].astype(np.int64), day=(te * 60 + 3 * 3600) // 86400,
                             price=mid[e], theta_usd=th[ok] * mid[e] / 1e4, leg_ratio=B[ok] / th[ok], gross=gross,
                             net=gross - SPREAD, duka=gross - ((ask - bid)[e] + (ask - bid)[out_i]) / 2, stop=stopped == 1))


D = pd.concat([run_year(yr, r) for r in RULES for yr in range(2010, 2020)], ignore_index=True)
D["R"] = D["theta_usd"] / SPREAD
D.to_pickle(ROOT / "out" / "TRADES.private.pkl")
for r, g in D.groupby("rule"):
    print(r, "n", len(g), "17-19 n", int((g.yr >= 2017).sum()), "net 17-19", round(g[g.yr >= 2017]["net"].mean(), 3),
          "theta$ p10/p50/p90", np.round(np.quantile(g["theta_usd"], [0.1, 0.5, 0.9]), 2))
print(D.groupby(["rule", "yr"])["theta_usd"].median().unstack(0).round(2).to_string())
