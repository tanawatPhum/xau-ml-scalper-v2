"""Follow the move after a v1 stop-out (see PLAN.md). Exness version of v1 as the source of stops."""
import json
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SB = HERE.parent
sys.path.insert(0, str(SB / "swing-causal-execution"))
from run import DEFAULT_CACHE, load_prices  # noqa: E402

THB = 10 * 33.77
mins, bid, ask = load_prices(DEFAULT_CACHE, list(range(2010, 2023)), allow_2020_2022=True)
mid = (bid + ask) / 2
ny = pd.to_datetime(mins * 60, unit="s", utc=True).tz_convert("America/New_York")
mod = (ny.hour * 60 + ny.minute).to_numpy()
dow = ny.dayofweek.to_numpy()
blocked = (mod >= 16 * 60 + 55) & (mod < 18 * 60 + 1)                    # Exness: break 16:58-18:01 NY
blocked |= (dow == 6) & (mod >= 18 * 60) & (mod < 18 * 60 + 5)          # Sunday open 18:05 NY
gap_next = np.r_[np.diff(mins) > 30, True]
nxt_gap = pd.Series(np.where(gap_next, mins, np.nan)).bfill().to_numpy()
blocked |= (nxt_gap - mins) <= 4                                        # holiday / early closes
cut = np.where(blocked, np.arange(len(mins)), len(mins) - 1)
cut = np.minimum.accumulate(cut[::-1])[::-1]

V1 = pd.read_csv(SB / "swing-v1-flat-daily" / "out" / "TRADES_EX.private.csv")
ST = V1[V1.exit_reason == "stop"].sort_values("t_exit").reset_index(drop=True)
ST["ix"] = np.searchsorted(mins, ST.t_exit.to_numpy())
assert (mins[ST.ix] == ST.t_exit).all()
VARIANTS = {"E0 hold to cutoff": (0, 0.0, 0.0), "E1 trail 1 theta": (1, 1.0, 0.0), "E2 trail 2 theta": (1, 2.0, 0.0),
            "E3 +1 / -1 theta": (2, 1.0, 1.0), "E4 +2 / -1 theta": (2, 2.0, 1.0)}


@nb.njit(cache=True)
def run(mid, cut, blocked, ix, d, th, rule_id, kind, a, b, out_x, take):
    busy = np.full(2, -1)
    for k in range(len(ix)):
        e = ix[k]
        r = rule_id[k]
        if blocked[e] or e <= busy[r] or e >= cut[e]:
            continue
        c = cut[e]
        x = c
        best = mid[e]
        for t in range(e + 1, c + 1):
            if t == c:
                x = c
                break
            m = d[k] * (mid[t] - mid[e])
            if kind == 1:
                if d[k] * mid[t] > d[k] * best:
                    best = mid[t]
                elif d[k] * (best - mid[t]) >= a * th[k]:
                    x = min(t + 1, c)
                    break
            elif kind == 2:
                if m >= a * th[k] or m <= -b * th[k]:
                    x = min(t + 1, c)
                    break
        out_x[k] = x
        take[k] = 1
        busy[r] = x
    return out_x, take


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se) if se > 0 else 0.0


th = (ST.theta_bps * mid[ST.ix] / 1e4).to_numpy()
d = -ST.side.to_numpy().astype(float)
rid = (ST.rule == "B").astype(np.int64).to_numpy()
res, allF = {}, {}
for name, (kind, a, b) in VARIANTS.items():
    ox, tk = run(mid, cut, blocked, ST.ix.to_numpy(), d, th, rid, kind, a, b, np.zeros(len(ST), np.int64), np.zeros(len(ST), np.int8))
    F = ST[tk == 1].copy()
    F["x"], F["d"], F["th"] = ox[tk == 1], d[tk == 1], th[tk == 1]
    F["gross"] = F.d * (mid[F.x] - mid[F.ix])
    F["net"] = F.gross - 0.168
    F["net_thb"] = F.net * THB
    F["t_exit_f"] = mins[F.x]
    F["yr"] = pd.to_datetime(F.t_exit_f * 60, unit="s").dt.year
    F["day"] = (F.t_exit * 60 + 3 * 3600) // 86400
    F["hold"] = F.t_exit_f - F.t_exit
    allF[name] = F
    row = {}
    for per, (lo, hi) in {"2010-16": (2010, 2016), "2010-13": (2010, 2013), "2014-16": (2014, 2016), "2017-19": (2017, 2019),
                          "2020-22": (2020, 2022), "2010-22": (2010, 2022)}.items():
        X = F[F.yr.between(lo, hi)]
        mu, t = ct(X.net, X.day) if len(X) > 2 else (0.0, 0.0)
        row[per] = dict(n=len(X), net=mu, t=t, gross=float(X.gross.mean()) if len(X) else 0.0, win=float((X.net > 0).mean()) if len(X) else 0.0,
                        thb=float(X.net_thb.sum()), hold=float(X.hold.median()) if len(X) else 0.0)
    row["years"] = {int(y): float(v) for y, v in F.groupby("yr").net_thb.sum().items()}
    res[name] = row
pd.set_option("display.width", 250)
print(f"stop-outs in v1 (Exness version) 2010-22: {len(ST)} (A {int((ST.rule == 'A').sum())}, B {int((ST.rule == 'B').sum())})")
for name, r in res.items():
    print(f"\n{name}:")
    for per in ("2010-16", "2010-13", "2014-16", "2017-19", "2020-22", "2010-22"):
        v = r[per]
        print(f"  {per}: n {v['n']:4d} net {v['net']:+.3f} $/oz (t {v['t']:+.2f}) gross {v['gross']:+.3f} win {100 * v['win']:.0f}% "
              f"total {v['thb']:+,.0f} THB hold {v['hold']:.0f} min")
    print("  years:", " ".join(f"{y}:{v:+,.0f}" for y, v in r["years"].items()))
cand = {k: v for k, v in res.items() if v["2010-16"]["t"] >= 2 and v["2010-13"]["thb"] > 0 and v["2014-16"]["thb"] > 0}
best = max(res, key=lambda k: res[k]["2010-16"]["t"])
lock = dict(best_by_t=best, qualifies=best in cand, t_2010_16=res[best]["2010-16"]["t"])
v = res[best]["2017-19"]
ypos = sum(res[best]["years"].get(y, 0) > 0 for y in (2017, 2018, 2019))
lock["check_2017_19"] = ("PASS" if (v["net"] > 0 and v["t"] >= 2 and ypos >= 2) else ("PARTIAL" if (v["net"] > 0 and ypos >= 2) else "FAIL")) \
    if lock["qualifies"] else "not run as a check (no variant qualified)"
print("\nLOCK", lock)
# random-walk reference for the brackets
print("random-walk chance to hit the target first: E3 50%, E4 33%")
for name in ("E3 +1 / -1 theta", "E4 +2 / -1 theta"):
    F = allF[name]
    print(f"  {name}: target first {(F.gross > 0).mean():.1%} (all years)")
# portfolio v1 + best follow variant, closed-trade curve
V1["yr"] = pd.to_datetime(V1.t_exit * 60, unit="s").dt.year
for name in (best,):
    F = allF[name]
    P = pd.concat([V1[["t_exit", "net_thb"]], F[["t_exit_f", "net_thb"]].rename(columns={"t_exit_f": "t_exit"})]).sort_values("t_exit", kind="stable")
    for lab, X in (("v1 alone", V1.sort_values("t_exit", kind="stable")), (f"v1 + {name}", P)):
        eq = 100_000 + np.cumsum(X.net_thb.to_numpy())
        dd = (np.maximum.accumulate(np.r_[100_000, eq])[1:] - eq).max()
        print(f"{lab}: end {eq[-1]:,.0f} THB, max DD (closed trades) {dd:,.0f}")
json.dump(dict(results=res, lock=lock), open(HERE / "out" / "FOLLOW.json", "w"), indent=1, default=float)
pd.concat([f.assign(variant=k) for k, f in allF.items()]).to_csv(HERE / "out" / "FOLLOW_TRADES.private.csv", index=False)
