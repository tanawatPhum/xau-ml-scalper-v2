"""Owner 21:41: run swing v1 on 5m / 15m / 30m / 1h charts (descriptive; v1 itself unchanged).
Same parameters as SPEC.md. The swings, signals and stops are read on the TF bar closes (bars on the clock,
split at blocks). Theta = the v1 volatility measure at the bar's last minute (time-based, from M1), so
'theta' means the same dollar size on every TF. Execution as in v1: entry and exit at the M1 close one
minute after the signal bar closes; the stop is checked at TF bar closes and exits at that close.
TF = 1 must reproduce v1 exactly. Years 2010-2022 (2020-22 already used once for the v1 exam)."""
import numba as nb
import numpy as np
import pandas as pd

import swing_v1 as v1

TFS = (1, 5, 15, 30, 60)


@nb.njit(cache=True)
def stop_tf(ytf, lastm, y, e, x, kb, sgn, stop):
    """Check closes of TF bars kb.. whose last minute is in (e, x]; return the exit minute index."""
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


def trades_tf(yr, rule, N):
    p = v1.RULES[rule]
    y, mins, blk, mid = v1.load_series(yr)
    n = len(y)
    s60 = v1.sigma60(y, blk)
    if p["theta"] == "sigma60":
        th_m = p["k"] * s60
    else:
        sl = v1.sigma1440(y, blk)
        th_m = p["k"] * np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    key = blk * 10 ** 9 + mins // N
    lastm = np.r_[np.flatnonzero(np.diff(key) != 0), n - 1]  # last M1 index of each TF bar
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
    ok = (blk[ent] == eb) & same_prev & (leg / th >= v1.LEG_SIGNAL) & (ex > ent)
    tu = th * mid[ent] / 1e4
    ok &= (tu >= p["theta_min_usd"]) & (leg / th >= p["leg_min"])
    sgn = -d[ok].astype(np.float64)
    e, x = ent[ok], ex[ok]
    out_i, st = stop_tf(ytf, lastm, y, e, x, idx[ok] + 1, sgn, v1.STOP_THETA * th[ok])
    gross = sgn * (mid[out_i] - mid[e])
    return pd.DataFrame(dict(tf=N, rule=rule, yr=yr, t_entry=mins[e], t_exit=mins[out_i], stopped=st == 1,
                             net_usd_oz=gross - v1.SPREAD_USD, net_thb=(gross - v1.SPREAD_USD) * v1.OZ * v1.FX))


rows = []
allT = []
for N in TFS:
    T = pd.concat([trades_tf(yr, r, N) for r in v1.RULES for yr in range(2010, 2023)], ignore_index=True)
    allT.append(T)
    if N == 1:
        ref = pd.concat([pd.read_pickle(v1.OUT / "V1_TRADES_2010_2019.private.pkl"), pd.read_pickle(v1.OUT / "V1_TRADES_2020_2022.private.pkl")])
        print(f"TF 1 reproduction: n {len(T)} vs {len(ref)}; THB {T['net_thb'].sum():,.1f} vs {ref['net_thb'].sum():,.1f}", flush=True)
    for per, (lo, hi) in {"2010-19": (2010, 2019), "2020-22": (2020, 2022), "2010-22": (2010, 2022)}.items():
        X = T[T["yr"].between(lo, hi)]
        M = v1.money_table(X)
        days = int(((X["t_entry"] * 60 + 3 * 3600) // 86400).nunique())
        g = X.sort_values("t_exit")
        rows.append(dict(tf=N, period=per, trades=len(X), per_day=len(X) / max(days, 1), win=float((X["net_thb"] > 0).mean()),
                         net_usd_oz=float(X["net_usd_oz"].mean()), thb=float(X["net_thb"].sum()), A=float(X.loc[X.rule == "A", "net_thb"].sum()),
                         B=float(X.loc[X.rule == "B", "net_thb"].sum()), max_dd=M["max_dd"], stop=float(X["stopped"].mean()),
                         worst=float(X["net_thb"].min()), years_pos=int(sum(v["net"] > 0 for v in M["years"].values())),
                         hold_med=float((X["t_exit"] - X["t_entry"]).median())))
    print("TF", N, "done", flush=True)
R = pd.DataFrame(rows)
R.to_csv(v1.OUT / "V1_TIMEFRAMES.csv", index=False)
pd.concat(allT).to_pickle(v1.OUT / "V1_TF_TRADES.private.pkl")
pd.set_option("display.width", 250)
print(R.round(3).to_string(index=False))
Y = pd.concat(allT).pivot_table(index="yr", columns="tf", values="net_thb", aggfunc="sum").round(0)
print(Y.to_string())
