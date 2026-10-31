"""Trade rows for rules A and B with batch-2 factors and times (see ../PLAN.md). 2010-2019 only."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-adaptive-bounce" / "code"))
from adaptive import COST_BPS, U, apply_stop, load_series, sigma60  # noqa: E402

_spec = importlib.util.spec_from_file_location("factors_build", ROOT.parent / "swing-factors-b1" / "code" / "build.py")
_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fb)
sigma_long, zigzag_x = _fb.sigma_long, _fb.zigzag_x
EDGE = ROOT.parent / "microstructure-edge-map" / "cache"
CACHE = ROOT / "cache"
YEARS = list(range(2010, 2020))
RULES = {"A": (1.0, "eff"), "B": (1.5, "s60")}


def wmean(cs, a, b):
    """mean of the series over positions a..b inclusive from its cumulative sum cs (cs[-1] style)."""
    a = np.maximum(a, 0)
    tot = cs[b] - np.where(a > 0, cs[np.maximum(a - 1, 0)], 0.0)
    return tot / np.maximum(b - a + 1, 1)


def build_year(yr, k, kind):
    y, mins, blk = load_series(yr)
    n = len(y)
    zp = np.load(EDGE / f"M1_{yr}.private.npz")
    base = int(zp["base"])
    pos = (mins - base).astype(np.int64)
    bid, ask = zp["bid"][pos], zp["ask"][pos]
    sp = (ask - bid) / ((ask + bid) / 2) * 1e4
    zv = np.load(CACHE / f"VOL_{yr}.private.npz")
    assert int(zv["base"]) == base
    vol = zv["vol"][pos].astype(np.float64)
    cv = np.cumsum(vol)
    s60 = sigma60(y, blk)
    sl = sigma_long(y, blk)
    seff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    T = k * (seff if kind == "eff" else s60)
    idx, d, ext, exi, th = zigzag_x(y, blk, T)
    m = len(idx)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(m, np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    brel = B / th
    prev_exi = np.r_[0, exi[:-1]]
    # batch-2 factors (windows end at the event minute)
    v_leg = wmean(cv, prev_exi, exi)
    v_bounce = wmean(cv, exi + 1, idx)
    v_day = wmean(cv, idx - 1439, idx)
    v_clim = wmean(cv, exi - 4, exi)
    sp_med = pd.Series(sp).rolling(1440, min_periods=720).median().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        f1 = v_bounce / v_leg
        f2 = np.where(idx >= 1439, v_bounce / v_day, np.nan)
        f3 = v_clim / v_leg
        f4 = sp[idx] / sp_med[idx]
    # trades
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (brel >= 2.5)
    ex = np.minimum(exit_i + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    sgn = -d.astype(np.float64)
    out_i, stopped = apply_stop(y, ent, ex, sgn, 3.0 * th)
    gross = sgn * (y[out_i] - y[ent])
    exit2 = np.where(np.r_[eb[2:] == eb[:-2], False, False], np.r_[idx[2:], -1, -1], last_of_blk[eb])
    ex2 = np.minimum(exit2 + 1, n - 1)
    ex2 = np.where(blk[ex2] == eb, ex2, exit2)
    ext_ok = (stopped == 0) & same_next & (ex2 > ex)
    extension = np.where(ext_ok, sgn * (y[ex2] - y[ex]) * U, 0.0)
    te = mins[ent].astype(np.int64)
    r = dict(net=(gross - COST_BPS) * U, ext=extension, stop=stopped.astype(np.int8), th_usd=th * U,
             t_ent=te, t_exit=mins[out_i].astype(np.int64), day=(te * 60 + 3 * 3600) // 86400,
             vol_bounce_leg=f1, vol_bounce_day=f2, vol_climax=f3, spread_rel=f4)
    r = {f: a[ok] for f, a in r.items()}
    r["yr"] = np.full(int(ok.sum()), yr, np.int16)
    return r


if __name__ == "__main__":
    for name, (k, kind) in RULES.items():
        parts = [build_year(yr, k, kind) for yr in YEARS]
        z = {f: np.concatenate([p[f] for p in parts]) for f in parts[0]}
        np.savez(CACHE / f"ROWS_{name}.private.npz", **z)
        for per, lo, hi in (("2010-16", 2010, 2016), ("2017-19", 2017, 2019)):
            mm = (z["yr"] >= lo) & (z["yr"] <= hi)
            print(f"rule {name} {per}: n {mm.sum()}, net {z['net'][mm].mean():+.3f}, stop {100 * z['stop'][mm].mean():.1f}%, "
                  f"factor NaN share {np.mean(~np.isfinite(z['vol_bounce_day'][mm])):.3f}/{np.mean(~np.isfinite(z['spread_rel'][mm])):.3f}",
                  flush=True)
