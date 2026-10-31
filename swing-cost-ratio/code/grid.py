"""2010-16 only: cost-ratio x leg-ratio grid per rule, random-subset null, automatic LOCK (see ../PLAN.md)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = pd.read_pickle(ROOT / "out" / "TRADES.private.pkl")
DEV = D[D["yr"] <= 2016]
NDAYS = int(DEV["day"].nunique())  # trading days with >= 1 trade (any rule)


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


rng = np.random.default_rng(7)
lock, rows = {}, []
for rule, g in DEV.groupby("rule"):
    qs = {p: float(np.quantile(g["R"], p / 100)) if p else 0.0 for p in (0, 20, 40, 60, 80)}
    mu0, t0 = ct(g["net"], g["day"])
    for p, rmin in qs.items():
        for leg in (2.5, 3.5, 5.0):
            x = g[(g["R"] >= rmin) & (g["leg_ratio"] >= leg)]
            mu, t = ct(x["net"], x["day"])
            nulls = []
            for _ in range(500):
                s = g.iloc[rng.choice(len(g), len(x), replace=False)]
                nulls.append(ct(s["net"], s["day"])[1])
            rows.append(dict(rule=rule, pct=p, R_min=rmin, theta_min_usd=rmin * 0.168, leg=leg, n=len(x), per_day=len(x) / NDAYS,
                             net=mu, t=t, p_null=float(np.mean(np.array(nulls) >= t)), thb=float(x["net"].sum() * 10 * 33.77),
                             win=float((x["net"] > 0).mean())))
G = pd.DataFrame(rows)
G.to_csv(ROOT / "out" / "GRID_2010_16.csv", index=False)
print(G.round(3).to_string(index=False))
for rule, g in G.groupby("rule"):
    e = g[g["per_day"] >= 0.5]
    b = e.loc[e["t"].idxmax()]
    base = g[(g["pct"] == 0) & (g["leg"] == 2.5)].iloc[0]
    real = bool(b["p_null"] < 0.05 and b["t"] > base["t"])
    lock[rule] = dict(pct=int(b["pct"]), R_min=float(b["R_min"]), theta_min_usd=float(b["theta_min_usd"]), leg=float(b["leg"]),
                      t=float(b["t"]), base_t=float(base["t"]), p_null=float(b["p_null"]), filter_real=real)
    print(f"\nRULE {rule}: chosen pct {b['pct']} (theta >= ${b['theta_min_usd']:.2f}) leg >= {b['leg']} | n {b['n']} ({b['per_day']:.2f}/day) "
          f"net {b['net']:+.3f} t {b['t']:+.2f} p_null {b['p_null']:.3f} | base t {base['t']:+.2f} net {base['net']:+.3f} -> real {real}")
json.dump(lock, open(ROOT / "out" / "LOCK.json", "w"), indent=1)

print("\ndescriptive 2010-16: edge in theta units and net by R quintile")
for rule, g in DEV.groupby("rule"):
    q = pd.qcut(g["R"], 5, labels=False)
    tab = g.groupby(q).agg(n=("net", "size"), theta_usd=("theta_usd", "median"), gross=("gross", "mean"), net=("net", "mean"))
    tab["gross_per_theta"] = g.groupby(q).apply(lambda x: (x["gross"] / x["theta_usd"]).mean())
    tab["t"] = [ct(g[q == i]["net"], g[q == i]["day"])[1] for i in tab.index]
    print(rule)
    print(tab.round(3).to_string())
