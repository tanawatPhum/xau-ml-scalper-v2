"""Trades of 20 cells x 4 timeframes, 2010-2019 (see ../PLAN.md). Uses the frozen swing_v1.py functions unchanged."""
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-v1" / "code"))
import swing_v1 as v1  # noqa: E402

TFS = (5, 15, 30, 60)
KS = (0.5, 0.75, 1.0, 1.5, 2.0)
LEGS = (2.5, 3.5)
TH_MIN = v1.RULES["A"]["theta_min_usd"]


@nb.njit(cache=True)
def stop_tf(ytf, lastm, y, e, x, kb, sgn, stop):
    out = x.copy()
    st = np.zeros(len(e), np.int8)
    for i in range(len(e)):
        k = kb[i]
        while k < len(lastm) and lastm[k] <= x[i]:
            if lastm[k] > e[i] and sgn[i] * (ytf[k] - y[e[i]]) <= -stop[i]:
                out[i] = lastm[k]
                st[i] = 1
                break
            k += 1
    return out, st


def cell_trades(y, mins, blk, mid, lastm, th_m, leg_min):
    n = len(y)
    ytf, btf, thtf = y[lastm], blk[lastm], th_m[lastm]
    idx, d, ext, exi, th = v1.zigzag(ytf, btf, thtf)
    eb = btf[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    leg = np.full(len(idx), np.nan)
    leg[1:] = d[1:] * (ext[:-1] - ext[1:])
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    conf_m = lastm[idx]
    nxt = np.where(same_next, np.r_[conf_m[1:], -1], last_of_blk[eb])
    ent = np.minimum(conf_m + 1, n - 1)
    ex = np.minimum(nxt + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, nxt)
    ok = (blk[ent] == eb) & same_prev & (leg / th >= 2.5) & (leg / th >= leg_min) & (ex > ent)
    ok &= th * mid[ent] / 1e4 >= TH_MIN
    sgn = -d[ok].astype(np.float64)
    e, x = ent[ok], ex[ok]
    out_i, st = stop_tf(ytf, lastm, y, e, x, idx[ok] + 1, sgn, 3.0 * th[ok])
    gross = sgn * (mid[out_i] - mid[e])
    return e, out_i, sgn, st, gross


parts = []
for yr in range(2010, 2020):
    y, mins, blk, mid = v1.load_series(yr)
    n = len(y)
    s60 = v1.sigma60(y, blk)
    sd = v1.sigma1440(y, blk)
    base = {"A": np.where(np.isfinite(sd), np.fmax(s60, sd), s60), "B": s60}
    for N in TFS:
        key = blk * 10 ** 9 + mins // N
        lastm = np.r_[np.flatnonzero(np.diff(key) != 0), n - 1]
        for typ, sig in base.items():
            for k in KS:
                for leg in LEGS:
                    e, o, s, st, gross = cell_trades(y, mins, blk, mid, lastm, k * sig, leg)
                    te = mins[e]
                    parts.append(pd.DataFrame(dict(tf=N, typ=typ, k=k, leg=leg, yr=yr, t_entry=te, t_exit=mins[o],
                                                   day=(te * 60 + 3 * 3600) // 86400, stopped=st == 1, net_usd_oz=gross - v1.SPREAD_USD,
                                                   net_thb=(gross - v1.SPREAD_USD) * v1.OZ * v1.FX)))
    print(yr, "done", flush=True)
D = pd.concat(parts, ignore_index=True)
D["cell"] = D["typ"] + "_k" + D["k"].astype(str) + "_leg" + D["leg"].astype(str)
D.to_pickle(ROOT / "out" / "TF_TRADES.private.pkl")
print(D.groupby(["tf"]).size())
