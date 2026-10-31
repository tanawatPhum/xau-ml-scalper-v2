"""2010-16 only: rule C selection (see ../PLAN.md). Writes out/CELLS_2010_16.csv and out/LOCK.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SB = ROOT.parent
D = pd.read_pickle(ROOT / "out" / "C_TRADES.private.pkl")
D = D[(D["yr"] <= 2016) & ~D["cell"].str.startswith("v1_")]
V1 = pd.read_pickle(SB / "swing-v1" / "out" / "V1_TRADES_2010_2019.private.pkl")
V1 = V1[V1["yr"] <= 2016].copy()
V1["day"] = (V1["t_entry"] * 60 + 3 * 3600) // 86400
NDAYS = int(V1["day"].nunique())
CELLS = sorted(D["cell"].unique())


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


def curve(t_exit, thb, start=100_000.0):
    o = np.argsort(t_exit, kind="stable")
    eq = start + np.cumsum(np.asarray(thb)[o])
    return float(eq[-1] - start), float((np.maximum.accumulate(np.r_[start, eq])[1:] - eq).max())


v1_tot, v1_dd = curve(V1["t_exit"].to_numpy(), V1["net_thb"].to_numpy())
v1_ratio = v1_tot / v1_dd
v1_daily = V1.groupby("day")["net_thb"].sum()
ent_side = {s: np.sort(V1.loc[V1["side"] == s, "t_entry"].to_numpy()) for s in ("BUY", "SELL")}
rows = []
for c in CELLS:
    g = D[D["cell"] == c]
    mu, t = ct(g["net_usd_oz"], g["day"])
    h1 = g[g["yr"] <= 2013]["net_thb"].sum()
    h2 = g[g["yr"] >= 2014]["net_thb"].sum()
    tot, dd = curve(np.r_[V1["t_exit"].to_numpy(), g["t_exit"].to_numpy()], np.r_[V1["net_thb"].to_numpy(), g["net_thb"].to_numpy()])
    ov = 0
    for s in ("BUY", "SELL"):
        te = g.loc[g["side"] == s, "t_entry"].to_numpy()
        a = ent_side[s]
        pos = np.searchsorted(a, te)
        near = np.zeros(len(te), bool)
        for q in (pos - 1, pos):
            q = np.clip(q, 0, len(a) - 1)
            near |= np.abs(a[q] - te) <= 10
        ov += int(near.sum())
    dly = g.groupby("day")["net_thb"].sum()
    j = pd.concat([v1_daily, dly], axis=1).fillna(0.0)
    rows.append(dict(cell=c, n=len(g), per_day=len(g) / NDAYS, net=mu, t=t, win=float((g["net_usd_oz"] > 0).mean()), thb=float(g["net_thb"].sum()),
                     h1013=float(h1), h1416=float(h2), port_thb=tot, port_dd=dd, port_ratio=tot / dd, overlap=ov / max(len(g), 1),
                     corr_daily=float(j.corr().iloc[0, 1])))
R = pd.DataFrame(rows)
# family-wise null: same day signs for every cell
days = np.unique(D["day"].to_numpy())
pos_of = {d: i for i, d in enumerate(days)}
sums, cnts = [], []
for c in CELLS:
    g = D[D["cell"] == c]
    i = np.array([pos_of[d] for d in g["day"].to_numpy()])
    sums.append(np.bincount(i, weights=g["net_usd_oz"].to_numpy(), minlength=len(days)))
    cnts.append(np.bincount(i, minlength=len(days)))
sums, cnts = np.array(sums), np.array(cnts)
rng = np.random.default_rng(17)
best = []
for _ in range(500):
    fs = sums * rng.choice([-1.0, 1.0], len(days))
    N = cnts.sum(1)
    mu = fs.sum(1) / N
    nd = (cnts > 0).sum(1)
    se = np.sqrt(((fs - mu[:, None] * cnts) ** 2).sum(1) * nd / (nd - 1)) / N
    best.append(float(np.max(mu / se)))
best = np.array(best)
R["p_fw"] = [float(np.mean(best >= t)) for t in R["t"]]
R["qualifies"] = (R["net"] > 0) & (R["t"] >= 2) & (R["h1013"] > 0) & (R["h1416"] > 0) & (R["per_day"] >= 0.3) & (R["port_ratio"] >= v1_ratio)
R = R.sort_values("port_thb", ascending=False)
R.to_csv(ROOT / "out" / "CELLS_2010_16.csv", index=False)
pd.set_option("display.width", 250)
print(f"v1 alone 2010-16: +{v1_tot:,.0f} THB, max DD {v1_dd:,.0f}, ratio {v1_ratio:.2f}; trading days {NDAYS}; "
      f"family-wise null best t p50 {np.median(best):.2f} p95 {np.quantile(best, 0.95):.2f}")
print(R.round(3).to_string(index=False))
q = R[R["qualifies"]]
lock = dict(cell=q.iloc[0]["cell"] if len(q) else None, v1_ratio_2010_16=v1_ratio)
if len(q):
    lock.update({k: (float(q.iloc[0][k]) if k != "cell" else q.iloc[0][k]) for k in ("t", "p_fw", "net", "per_day", "port_thb", "port_dd", "port_ratio",
                                                                                     "overlap", "corr_daily")})
    lock["real"] = bool(q.iloc[0]["p_fw"] < 0.05)
json.dump(lock, open(ROOT / "out" / "LOCK.json", "w"), indent=1)
print("LOCK", lock)
