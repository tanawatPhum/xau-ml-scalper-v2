"""Owner 21:54: fact-check the ChatGPT audit (swing-causal-execution) of swing v1.
Re-runs v1 (frozen code, unchanged) with each audit correction switched on alone, then all together, 2010-2019.
Money: 0.1 lot per rule, $0.168 fixed spread, 33.77 THB/USD; drawdown from closed trades (as v1 reports)."""
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "swing-v1" / "code"))
import swing_v1 as v1  # noqa: E402


def vol_adjacent(y, mins, blk):
    """sigma60 / sigma1440 counting only returns between adjacent minutes (audit item 6)."""
    n = len(y)
    r = np.r_[0.0, np.diff(y)]
    adj = np.r_[False, (np.diff(mins) == 1) & (blk[1:] == blk[:-1])]
    cs = np.r_[0.0, np.cumsum(np.where(adj, r * r, 0.0))]
    cc = np.r_[0, np.cumsum(adj)]
    first = np.r_[0, np.flatnonzero(np.diff(blk)) + 1][blk]
    i = np.arange(n)
    out = []
    for win, mn, inblock in ((60, 30, True), (1440, 720, False)):
        lo = np.maximum(i - win, first + 1) if inblock else np.maximum(i - win, 1)
        lo = np.minimum(lo, i)
        cnt = cc[i] - cc[lo]
        ss = np.maximum(cs[i] - cs[lo], 0.0)
        ok = (cnt >= mn) & (ss > 1e-12)
        out.append(np.where(ok, np.sqrt(ss / np.maximum(cnt, 1) * 60), np.nan))
    return out


@nb.njit(cache=True)
def stop_next(y, ent, ex, sgn, stop, blk):
    """Stop seen at a close, filled at the next minute's close (audit item 3)."""
    out_i = ex.copy()
    st = np.zeros(len(ent), np.int8)
    for k in range(len(ent)):
        e = ent[k]
        for t in range(e + 1, ex[k] + 1):
            if sgn[k] * (y[t] - y[e]) <= -stop[k]:
                o = t + 1
                if o >= len(y) or blk[o] != blk[t]:
                    o = t + 1 if (o < len(y)) else t
                out_i[k] = min(o, ex[k]) if o > ex[k] else o
                st[k] = 1
                break
    return out_i, st


def trades_year(yr, rule, filt_conf=False, stop_delay=False, cancel_gap_entry=False, adj_vol=False, exit_after_gap=False):
    p = v1.RULES[rule]
    y, mins, blk, mid = v1.load_series(yr)
    n = len(y)
    if adj_vol:
        s60, sl = vol_adjacent(y, mins, blk)
    else:
        s60, sl = v1.sigma60(y, blk), v1.sigma1440(y, blk)
    th_s = p["k"] * (s60 if p["theta"] == "sigma60" else np.where(np.isfinite(sl), np.fmax(s60, sl), s60))
    idx, d, ext, exi, th = v1.zigzag(y, blk, th_s)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    leg = np.full(len(idx), np.nan)
    leg[1:] = d[1:] * (ext[:-1] - ext[1:])
    first_of_blk = np.r_[0, np.flatnonzero(np.diff(blk)) + 1]
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    nxt = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ex = np.minimum(nxt + 1, n - 1)
    if exit_after_gap:
        # audit item 4: no knowledge of an unscheduled gap; close at the first quote after it (same year only)
        nb_ = np.where(eb + 1 < len(first_of_blk), first_of_blk[np.minimum(eb + 1, len(first_of_blk) - 1)], n - 1)
        ex = np.where(blk[ex] == eb, ex, nb_)
    else:
        ex = np.where(blk[ex] == eb, ex, nxt)
    ok = (blk[ent] == eb) & same_prev & (leg / th >= v1.LEG_SIGNAL) & (ex > ent)
    price_for_filter = mid[idx] if filt_conf else mid[ent]
    ok &= (th * price_for_filter / 1e4 >= p["theta_min_usd"]) & (leg / th >= p["leg_min"])
    if cancel_gap_entry:
        ok &= (mins[ent] - mins[idx]) == 1
    sgn = -d[ok].astype(np.float64)
    e, x = ent[ok], ex[ok]
    if stop_delay:
        out_i, st = stop_next(y, e, x, sgn, v1.STOP_THETA * th[ok], blk)
    else:
        out_i, st = v1.apply_stop(y, e, x, sgn, v1.STOP_THETA * th[ok])
    gross = sgn * (mid[out_i] - mid[e])
    return pd.DataFrame(dict(rule=rule, yr=yr, t_entry=mins[e], t_exit=mins[out_i],
                             net_usd_oz=gross - v1.SPREAD_USD, net_thb=(gross - v1.SPREAD_USD) * v1.OZ * v1.FX))


CASES = {"v1 as frozen": {},
         "1 theta$ filter at the confirmation price": dict(filt_conf=True),
         "2 cancel entry if the next minute is missing": dict(cancel_gap_entry=True),
         "3 stop filled at the next minute": dict(stop_delay=True),
         "4 gap: close after the gap, not before": dict(exit_after_gap=True),
         "5 volatility from adjacent minutes only": dict(adj_vol=True),
         "all five together": dict(filt_conf=True, cancel_gap_entry=True, stop_delay=True, exit_after_gap=True, adj_vol=True)}
rows = []
for name, kw in CASES.items():
    T = pd.concat([trades_year(yr, r, **kw) for r in v1.RULES for yr in range(2010, 2020)], ignore_index=True)
    M = v1.money_table(T)
    rows.append(dict(case=name, trades=len(T), thb=T["net_thb"].sum(), end=M["end"], max_dd=M["max_dd"],
                     A=T.loc[T.rule == "A", "net_thb"].sum(), B=T.loc[T.rule == "B", "net_thb"].sum()))
    print(name, "done", flush=True)
R = pd.DataFrame(rows)
R["change_vs_v1"] = R["thb"] - R["thb"].iloc[0]
R.to_csv(ROOT / "out" / "ATTRIBUTION_2010_2019.csv", index=False)
pd.set_option("display.width", 250)
print(R.round(0).to_string(index=False))
print("audit engine (swing-causal-execution, fixed spread, 2010-19): +359,209 THB, 7,305 trades, closed-trade DD 67,084")
