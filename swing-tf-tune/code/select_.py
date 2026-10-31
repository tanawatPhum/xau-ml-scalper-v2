"""2010-16 only: per-TF selection (see ../PLAN.md). Writes out/CELLS_2010_16.csv and out/LOCK.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ALL = pd.read_pickle(ROOT / "out" / "TF_TRADES.private.pkl")
chk = ALL[(ALL.tf == 5) & (ALL.cell == "A_k1.0_leg2.5") & (ALL.yr <= 2019)]["net_thb"].sum()
print(f"consistency: TF5 A k1 leg2.5 2010-19 THB {chk:,.0f} (tf_run v1-on-5m rule A: +65,714)")
D = ALL[ALL["yr"] <= 2016]


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se) if se > 0 else 0.0


ndays = int(D["day"].nunique())
rng = np.random.default_rng(23)
lock, tabs = {}, []
for N, g in D.groupby("tf"):
    rows = []
    cells = sorted(g["cell"].unique())
    days = np.unique(g["day"])
    pos = {d: i for i, d in enumerate(days)}
    sums, cnts = [], []
    for c in cells:
        x = g[g["cell"] == c]
        mu, t = ct(x["net_usd_oz"], x["day"])
        rows.append(dict(tf=N, cell=c, typ=x["typ"].iloc[0], n=len(x), per_day=len(x) / ndays, net=mu, t=t, thb=float(x["net_thb"].sum()),
                         h1=float(x.loc[x.yr <= 2013, "net_thb"].sum()), h2=float(x.loc[x.yr >= 2014, "net_thb"].sum()),
                         win=float((x["net_thb"] > 0).mean())))
        i = np.array([pos[d] for d in x["day"]])
        sums.append(np.bincount(i, weights=x["net_usd_oz"].to_numpy(), minlength=len(days)))
        cnts.append(np.bincount(i, minlength=len(days)))
    sums, cnts = np.array(sums), np.array(cnts)
    best = []
    for _ in range(500):
        fs = sums * rng.choice([-1.0, 1.0], len(days))
        Nn = cnts.sum(1)
        mu = fs.sum(1) / Nn
        nd = (cnts > 0).sum(1)
        se = np.sqrt(((fs - mu[:, None] * cnts) ** 2).sum(1) * nd / (nd - 1)) / Nn
        best.append(float(np.max(mu / se)))
    best = np.array(best)
    R = pd.DataFrame(rows)
    R["p_fw"] = [float(np.mean(best >= t)) for t in R["t"]]
    R["qual"] = (R["net"] > 0) & (R["t"] >= 2) & (R["h1"] > 0) & (R["h2"] > 0) & (R["per_day"] >= 0.3)
    tabs.append(R)
    pick = {}
    for typ in ("A", "B"):
        q = R[(R["typ"] == typ) & R["qual"]].sort_values("t", ascending=False)
        if len(q):
            pick[typ] = dict(cell=q.iloc[0]["cell"], t=float(q.iloc[0]["t"]), p_fw=float(q.iloc[0]["p_fw"]), net=float(q.iloc[0]["net"]),
                             per_day=float(q.iloc[0]["per_day"]), thb_2010_16=float(q.iloc[0]["thb"]))
    lock[int(N)] = pick
    print(f"\nTF {N}m: null best t p95 {np.quantile(best, 0.95):.2f}")
    print(R.sort_values("t", ascending=False).round(3).to_string(index=False))
    print("PICK", pick)
pd.concat(tabs).to_csv(ROOT / "out" / "CELLS_2010_16.csv", index=False)
json.dump(lock, open(ROOT / "out" / "LOCK.json", "w"), indent=1)
