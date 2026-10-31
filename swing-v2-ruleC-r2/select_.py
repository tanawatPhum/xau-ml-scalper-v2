"""2010-16 only: round-2 selection (see PLAN.md). Writes out/CELLS_2010_16.csv and out/LOCK.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D = pd.read_csv(HERE / "out" / "C2_TRADES.private.csv")
D = D[D.yr <= 2016]
V1 = pd.read_csv(HERE.parent / "swing-v1-flat-daily" / "out" / "TRADES_EX.private.csv")
V1["yr"] = pd.to_datetime(V1.t_exit * 60, unit="s").dt.year
V1 = V1[V1.yr <= 2016]
NDAYS = int(((V1.t_entry * 60 + 3 * 3600) // 86400).nunique())


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


def curve(t, v):
    o = np.argsort(t, kind="stable")
    eq = 100_000 + np.cumsum(np.asarray(v)[o])
    return float(eq[-1] - 100_000), float((np.maximum.accumulate(np.r_[100_000, eq])[1:] - eq).max())


vt, vdd = curve(V1.t_exit.to_numpy(), V1.net_thb.to_numpy())
rows = []
days = np.unique(D.day)
pos = {d: i for i, d in enumerate(days)}
sums, cnts = [], []
for c, g in D.groupby("cell"):
    mu, t = ct(g.net, g.day)
    tot, dd = curve(np.r_[V1.t_exit, g.t_exit], np.r_[V1.net_thb, g.net_thb])
    rows.append(dict(cell=c, n=len(g), per_day=len(g) / NDAYS, net=mu, t=t, win=float((g.net > 0).mean()), thb=float(g.net_thb.sum()),
                     h1=float(g[g.yr <= 2013].net_thb.sum()), h2=float(g[g.yr >= 2014].net_thb.sum()), port=tot, port_dd=dd, port_ratio=tot / dd))
    i = np.array([pos[d] for d in g.day])
    sums.append(np.bincount(i, weights=g.net.to_numpy(), minlength=len(days)))
    cnts.append(np.bincount(i, minlength=len(days)))
sums, cnts = np.array(sums), np.array(cnts)
rng = np.random.default_rng(29)
best = []
for _ in range(500):
    fs = sums * rng.choice([-1.0, 1.0], len(days))
    N = cnts.sum(1)
    mu = fs.sum(1) / N
    nd = (cnts > 0).sum(1)
    se = np.sqrt(((fs - mu[:, None] * cnts) ** 2).sum(1) * nd / (nd - 1)) / N
    best.append(float(np.max(mu / se)))
best = np.array(best)
R = pd.DataFrame(rows)
R["p_fw"] = [float(np.mean(best >= t)) for t in R.t]
R["qual"] = (R.net > 0) & (R.t >= 2) & (R.h1 > 0) & (R.h2 > 0) & (R.per_day >= 0.3) & (R.port_ratio >= vt / vdd)
R = R.sort_values("t", ascending=False)
R.to_csv(HERE / "out" / "CELLS_2010_16.csv", index=False)
pd.set_option("display.width", 250)
print(f"v1 (Exness) 2010-16: +{vt:,.0f} THB, closed-trade DD {vdd:,.0f}, ratio {vt / vdd:.2f}; null best t p95 {np.quantile(best, 0.95):.2f}")
print(R.round(3).to_string(index=False))
q = R[R.qual].sort_values("port", ascending=False)
lock = dict(cell=q.iloc[0].cell if len(q) else None)
json.dump(lock, open(HERE / "out" / "LOCK.json", "w"), indent=1)
print("LOCK", lock)
s = pd.read_csv(HERE / "out" / "C2_TRADES.private.csv")
s = s[(s.yr <= 2016) & s.cell.str.startswith("R3")]
print("\nR3 per slot, 2010-16 (descriptive):")
print(s.groupby(["cell", "slot"]).agg(n=("net", "size"), net=("net", "mean"), win=("net", lambda v: (v > 0).mean()), thb=("net_thb", "sum")).round(3).to_string())
