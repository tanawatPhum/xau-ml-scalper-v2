"""2017-19 check of the per-TF rule sets locked in out/LOCK.json (once), plus 2010-19 money tables (see ../PLAN.md)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-v1" / "code"))
import swing_v1 as v1  # noqa: E402

ALL = pd.read_pickle(ROOT / "out" / "TF_TRADES.private.pkl")
LK = json.load(open(ROOT / "out" / "LOCK.json"))
V1 = pd.read_pickle(ROOT.parent / "swing-v1" / "out" / "V1_TRADES_2010_2019.private.pkl")


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


def dd(X):
    X = X.sort_values("t_exit", kind="stable")
    eq = np.cumsum(X["net_thb"].to_numpy())
    return float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max())


out = {}
rows = []
v1c = V1[V1.yr >= 2017].copy()
v1c["day"] = (v1c["t_entry"] * 60 + 3 * 3600) // 86400
mu, t = ct(v1c["net_usd_oz"], v1c["day"])
rows.append(dict(set="1m v1", trades=len(v1c), net=mu, t=t, y2017=v1c[v1c.yr == 2017].net_thb.sum(), y2018=v1c[v1c.yr == 2018].net_thb.sum(),
                 y2019=v1c[v1c.yr == 2019].net_thb.sum(), thb=v1c.net_thb.sum(), dd=dd(v1c), verdict="-"))
tables = {"1m v1": v1.money_table(V1)}
for N, pick in LK.items():
    N = int(N)
    sel = ALL[(ALL.tf == N) & ALL.cell.isin([p["cell"] for p in pick.values()])]
    X = sel[sel.yr >= 2017]
    mu, t = ct(X["net_usd_oz"], X["day"])
    ys = {y: float(X[X.yr == y].net_thb.sum()) for y in (2017, 2018, 2019)}
    ypos = sum(v > 0 for v in ys.values())
    verdict = "PASS" if (mu > 0 and t >= 2 and ypos >= 2) else ("PARTIAL" if (mu > 0 and ypos >= 2) else "FAIL")
    name = f"{N}m " + " + ".join(p["cell"] for p in pick.values())
    rows.append(dict(set=name, trades=len(X), net=mu, t=t, y2017=ys[2017], y2018=ys[2018], y2019=ys[2019], thb=float(X.net_thb.sum()), dd=dd(X),
                     verdict=verdict))
    M = v1.money_table(sel.assign(rule=sel["typ"]))
    tables[name] = M
    out[N] = dict(cells=pick, verdict=verdict, net=mu, t=t, years=ys, thb=float(X.net_thb.sum()), dd_2017_19=dd(X), end_2010_19=M["end"],
                  max_dd_2010_19=M["max_dd"], per_rule={c: float(X[X.cell == c].net_thb.sum()) for c in X.cell.unique()})
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print("2017-19 check (0.1 lot per rule, at the time's price):")
print(R.round(3).to_string(index=False))
print("\n2010-19 money, 100,000 THB start:")
for name, M in tables.items():
    yrs = " ".join(f"{y}:{v['net']:+,.0f}" for y, v in M["years"].items())
    print(f"{name}: end {M['end']:,.0f} max DD {M['max_dd']:,.0f} ({M['dd_from']} -> {M['dd_to']}) | {yrs}")
for N, o in out.items():
    print(N, "per rule 2017-19:", {k: round(v) for k, v in o["per_rule"].items()})
json.dump(out, open(ROOT / "out" / "CHECK_2017_19.json", "w"), indent=1, default=float)
