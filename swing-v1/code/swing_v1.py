"""Swing v1 - frozen reference implementation (see ../SPEC.md). Self-contained: no imports from other sandbox folders.

Usage:  python swing_v1.py            -> backtest 2010-2019, reproduction check, out/V1_BACKTEST_2010_2019.json
Library: trades_year(yr, rule) -> DataFrame of v1 trades for one year and rule ("A" or "B").
Data: 1-minute bid/ask close caches (full-year minute grid) in EDGE_CACHE. 2020+ is not run here."""
import json
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

EDGE_CACHE = Path(r"D:\xau-ml-scalper-claude\microstructure-edge-map\cache")  # M1_{yr}.private.npz: base, bid, ask
OUT = Path(__file__).resolve().parents[1] / "out"

# ---- frozen parameters (v1, 31 Oct 2026)
RULES = {"A": dict(k=1.0, theta="max(sigma60, sigma1440)", theta_min_usd=2.1626934441569983, leg_min=2.5),
         "B": dict(k=1.5, theta="sigma60", theta_min_usd=0.0, leg_min=3.5)}
LEG_SIGNAL = 2.5   # leg before the signal, in theta (signal condition for both rules)
STOP_THETA = 3.0   # stop distance from the entry, in theta, checked at minute closes
GAP_MIN = 30       # a gap > 30 minutes starts a new block (flat before the break)
SPREAD_USD = 0.168  # per round trip per oz
OZ = 10            # 0.1 lot per rule
FX = 33.77         # THB per USD


def load_series(yr):
    z = np.load(EDGE_CACHE / f"M1_{yr}.private.npz")
    base = int(z["base"])
    mid = (z["bid"] + z["ask"]) / 2
    pos = np.flatnonzero(np.isfinite(mid))
    y = 1e4 * np.log(mid[pos])
    mins = (base + pos).astype(np.int64)
    blk = np.r_[0, np.cumsum(np.diff(pos) > GAP_MIN)].astype(np.int64)
    return y, mins, blk, mid[pos]


def sigma60(y, blk, win=60, minn=30):
    """sqrt(60 x mean squared 1-minute log return) over the last <= 60 returns strictly before t, inside the block."""
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
    ok = (cnt >= minn) & (s > 1e-12)
    return np.where(ok, np.sqrt(np.maximum(s, 0.0) / np.maximum(cnt, 1) * win), np.nan)


def sigma1440(y, blk, win=1440, minn=720):
    """Same over the last 1440 traded minutes (>= 720 in-block returns), scaled to 60 minutes."""
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


@nb.njit(cache=True)
def zigzag(y, blk, th):
    """Adaptive zigzag on closes: a swing low is confirmed when close - running low >= theta(t), a swing high when
    running high - close >= theta(t). Resets at each block start. Returns confirm index, dir (+1 low, -1 high),
    extreme value, extreme index, theta at confirmation."""
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


@nb.njit(cache=True)
def apply_stop(y, ent, ex, sgn, stop):
    out_i = ex.copy()
    stopped = np.zeros(len(ent), np.int8)
    for k in range(len(ent)):
        e = ent[k]
        for t in range(e + 1, ex[k] + 1):
            if sgn[k] * (y[t] - y[e]) <= -stop[k]:
                out_i[k] = t
                stopped[k] = 1
                break
    return out_i, stopped


def trades_year(yr, rule):
    p = RULES[rule]
    y, mins, blk, mid = load_series(yr)
    n = len(y)
    s60 = sigma60(y, blk)
    if p["theta"] == "sigma60":
        th_series = p["k"] * s60
    else:
        sl = sigma1440(y, blk)
        th_series = p["k"] * np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    idx, d, ext, exi, th = zigzag(y, blk, th_series)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    leg = np.full(len(idx), np.nan)
    leg[1:] = d[1:] * (ext[:-1] - ext[1:])
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    nxt = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ex = np.minimum(nxt + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, nxt)
    ok = (blk[ent] == eb) & same_prev & (leg / th >= LEG_SIGNAL) & (ex > ent)
    theta_usd = th * mid[ent] / 1e4
    ok &= (theta_usd >= p["theta_min_usd"]) & (leg / th >= p["leg_min"])
    sgn = -d[ok].astype(np.float64)  # swing low confirmed -> SELL (fade the bounce); swing high -> BUY
    e, x = ent[ok], ex[ok]
    out_i, stopped = apply_stop(y, e, x, sgn, STOP_THETA * th[ok])
    gross = sgn * (mid[out_i] - mid[e])
    te = mins[e]
    return pd.DataFrame(dict(rule=rule, yr=yr, side=np.where(sgn < 0, "SELL", "BUY"), t_entry=te, t_exit=mins[out_i],
                             entry_mid=mid[e], exit_mid=mid[out_i], theta_usd=theta_usd[ok], leg_theta=(leg / th)[ok],
                             stop_usd=STOP_THETA * theta_usd[ok], stopped=stopped == 1, gross_usd_oz=gross,
                             net_usd_oz=gross - SPREAD_USD, net_thb=(gross - SPREAD_USD) * OZ * FX))


def money_table(T, start=100_000.0):
    T = T.sort_values("t_exit", kind="stable")
    pnl = T["net_thb"].to_numpy()
    eq = start + np.cumsum(pnl)
    pk = np.maximum.accumulate(np.r_[start, eq])[1:]
    i = int(np.argmax(pk - eq))
    j = int(np.argmax(eq[: i + 1] == pk[i]))
    ts = pd.to_datetime(T["t_exit"].to_numpy() * 60, unit="s")
    rows, e0 = {}, start
    for yr in sorted(T["yr"].unique()):
        m = (T["yr"] == yr).to_numpy()
        e = e0 + np.cumsum(pnl[m])
        pky = np.maximum.accumulate(np.r_[e0, e])[1:]
        w = pnl[m]
        rows[int(yr)] = dict(trades=int(m.sum()), trades_A=int((m & (T["rule"] == "A").to_numpy()).sum()),
                             thb_A=float(pnl[m & (T["rule"] == "A").to_numpy()].sum()), thb_B=float(pnl[m & (T["rule"] == "B").to_numpy()].sum()),
                             win=float((w > 0).mean()), net=float(w.sum()), start=e0, end=float(e[-1]), dd=float((pky - e).max()),
                             best=float(w.max()), worst=float(w.min()))
        e0 = float(e[-1])
    return dict(years=rows, end=float(eq[-1]), max_dd=float(pk[i] - eq[i]), dd_from=str(ts[j].date()), dd_to=str(ts[i].date()),
                lowest=float(eq.min()))


if __name__ == "__main__":
    T = pd.concat([trades_year(yr, r) for r in RULES for yr in range(2010, 2020)], ignore_index=True)
    T.to_pickle(OUT / "V1_TRADES_2010_2019.private.pkl")
    M = money_table(T)
    days = int(((T["t_entry"] * 60 + 3 * 3600) // 86400).nunique())
    stats = {}
    for r, g in T.groupby("rule"):
        w, lo = g.loc[g["net_thb"] > 0, "net_thb"], g.loc[g["net_thb"] <= 0, "net_thb"]
        stats[r] = dict(trades=len(g), per_day=len(g) / days, win=float((g["net_thb"] > 0).mean()), avg_win=float(w.mean()), avg_loss=float(lo.mean()),
                        stop_rate=float(g["stopped"].mean()), worst=float(g["net_thb"].min()), net_usd_oz=float(g["net_usd_oz"].mean()),
                        thb=float(g["net_thb"].sum()), hold_min_median=float((g["t_exit"] - g["t_entry"]).median()),
                        theta_usd_median=float(g["theta_usd"].median()))
    json.dump(dict(rules=RULES, stats=stats, money=M), open(OUT / "V1_BACKTEST_2010_2019.json", "w"), indent=1)
    print("year | trades (A) | A THB | B THB | win | year net | end capital | DD in year | worst trade")
    for yr, v in M["years"].items():
        print(f"{yr} | {v['trades']} ({v['trades_A']}) | {v['thb_A']:+,.0f} | {v['thb_B']:+,.0f} | {100 * v['win']:.0f}% | {v['net']:+,.0f} | "
              f"{v['end']:,.0f} | {v['dd']:,.0f} | {v['worst']:+,.0f}")
    print(f"end {M['end']:,.0f} | max DD {M['max_dd']:,.0f} ({M['dd_from']} -> {M['dd_to']}) | lowest {M['lowest']:,.0f}")
    for r, s in stats.items():
        print(r, {k: round(v, 3) if isinstance(v, float) else v for k, v in s.items()})
    # reproduction of the swing-cost-ratio locked portfolio (2010-19)
    assert abs(M["end"] - 479_450) < 1.0 and abs(M["max_dd"] - 58_773) < 1.0, "reproduction failed"
    print("REPRODUCTION OK (swing-cost-ratio locked: end 479,450, max DD 58,773)")
