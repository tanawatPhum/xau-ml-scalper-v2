"""ML dataset: all rule A and B trades 2010-2019 with entry-time features and outcomes at the time."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-adaptive-bounce" / "code"))
from adaptive import apply_stop, load_series, sigma60  # noqa: E402

_spec = importlib.util.spec_from_file_location("factors_build", ROOT.parent / "swing-factors-b1" / "code" / "build.py")
_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fb)
sigma_long, zigzag_x = _fb.sigma_long, _fb.zigzag_x
EDGE = ROOT.parent / "microstructure-edge-map" / "cache"
VOLC = ROOT.parent / "swing-improve-v2" / "cache"
OUT = ROOT / "cache"
YEARS = list(range(2010, 2020))
RULES = {"A": (1.0, "eff"), "B": (1.5, "s60")}
SPREAD = 0.168


def wmean(cs, a, b):
    a = np.maximum(a, 0)
    tot = cs[b] - np.where(a > 0, cs[np.maximum(a - 1, 0)], 0.0)
    return tot / np.maximum(b - a + 1, 1)


def build_year(yr, rule):
    k, kind = RULES[rule]
    y, mins, blk = load_series(yr)
    n = len(y)
    zp = np.load(EDGE / f"M1_{yr}.private.npz")
    base = int(zp["base"])
    pos = (mins - base).astype(np.int64)
    bid, ask = zp["bid"][pos], zp["ask"][pos]
    mid = (bid + ask) / 2
    sp = (ask - bid) / mid * 1e4
    vol = np.load(VOLC / f"VOL_{yr}.private.npz")["vol"][pos].astype(np.float64)
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
    # structure family
    fam = np.full(m, -1)
    if m >= 4:
        kk = np.arange(3, m)
        kk = kk[eb[kk - 3] == eb[kk]]
        dd = d[kk]
        Ak, Bk, Ck = dd * (ext[kk - 1] - ext[kk - 2]), dd * (ext[kk - 1] - ext[kk]), dd * (ext[kk - 3] - ext[kk - 2])
        a, b = Ak / Ck, Bk / Ak
        fam[kk] = np.where(a > 1, np.where(b < 1, 0, 3), np.where(b < 1, 1, 2))
    # k = 3 trend (3 x sigma60 for both rules, as in swing-factors-b1)
    i3, d3, _, _, _ = zigzag_x(y, blk, 3.0 * s60)
    j = np.searchsorted(i3, idx, side="right") - 1
    jj = np.maximum(j, 0)
    htf = np.where((j >= 0) & (blk[i3[jj]] == eb), d3[jj], 0) if len(i3) else np.zeros(m, int)
    htf_with = np.where(htf == 0, -1, (htf == -d).astype(int))
    s = pd.Series(y)
    rmax = s.rolling(1440, min_periods=720).max().to_numpy()[idx]
    rmin = s.rolling(1440, min_periods=720).min().to_numpy()[idx]
    pos_up = (y[idx] - rmin) / (rmax - rmin)
    sp_med = pd.Series(sp).rolling(1440, min_periods=720).median().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        feats = dict(theta_bps=th, legsize=brel, legtime=np.r_[np.nan, (mins[exi[1:]] - mins[exi[:-1]]).astype(float)],
                     bouncetime=(mins[idx] - mins[exi]).astype(float), volratio=s60[idx] / sl[idx],
                     htf=htf_with, rangepos=np.where(d == 1, pos_up, 1 - pos_up), structure=fam,
                     vol_bounce_leg=wmean(cv, exi + 1, idx) / wmean(cv, prev_exi, exi),
                     vol_bounce_day=np.where(idx >= 1439, wmean(cv, exi + 1, idx) / wmean(cv, idx - 1439, idx), np.nan),
                     vol_climax=wmean(cv, exi - 4, exi) / wmean(cv, prev_exi, exi), spread_rel=sp[idx] / sp_med[idx])
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
    gross_bps = sgn * (y[out_i] - y[ent])
    price = mid[ent]
    cost_bps = SPREAD / price * 1e4
    te = mins[ent].astype(np.int64)
    r = dict(feats)
    r.update(cost_bps=cost_bps, theta_over_cost=th / cost_bps, hour=((te % 1440) // 60).astype(int),
             dow=(((te // 1440) + 3) % 7).astype(int), net_bps=gross_bps - cost_bps,
             net_usd=sgn * (mid[out_i] - mid[ent]) - SPREAD, price=price, t_ent=te,
             t_exit=mins[out_i].astype(np.int64), stop=stopped.astype(int))
    r = {f: np.asarray(v)[ok] for f, v in r.items()}
    r["yr"] = np.full(int(ok.sum()), yr)
    r["rule"] = np.full(int(ok.sum()), rule)
    return pd.DataFrame(r)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    df = pd.concat([build_year(yr, r) for r in RULES for yr in YEARS], ignore_index=True)
    df.to_pickle(OUT / "DATASET.private.pkl")
    g = df.groupby(["rule", "yr"]).agg(n=("net_usd", "size"), net_usd=("net_usd", "mean"))
    print(g.unstack(0).round(3).to_string())
    print("rows", len(df), "NaN share per feature:", df.isna().mean().round(3)[df.isna().mean() > 0].to_dict())
