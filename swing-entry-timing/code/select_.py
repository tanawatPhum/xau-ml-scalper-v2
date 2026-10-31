"""2010-16 only: paired gain of each entry policy vs base, family-wise sign-flip null, automatic LOCK (see ../PLAN.md)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
S = pd.read_pickle(ROOT / "out" / "SIGNALS.private.pkl")
S = S[S["keep"]].copy()
THB = 10 * 33.77
TIMING = [c for c in S.columns if c.startswith(("L_", "LF_", "D_")) and not c.endswith(("_stop", "_wait"))]
SESS = {"Asia": lambda h: (h >= 23) | (h < 7), "London": lambda h: (h >= 7) & (h < 13), "NewYork": lambda h: (h >= 13) & (h < 23)}


def deltas(g):
    base = g["base"].to_numpy() * THB
    out = {c: np.nan_to_num(g[c].to_numpy() * THB, nan=0.0) - base for c in TIMING}
    for s, f in SESS.items():
        out["S_skip_" + s] = np.where(f(g["hour"].to_numpy()), -base, 0.0)
    return pd.DataFrame(out, index=g.index)


def tstat(x, day):
    u, inv = np.unique(day, return_inverse=True)
    Ssum, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = Ssum.sum() / N.sum()
    se = np.sqrt(((Ssum - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return mu / se if se > 0 else 0.0


rng = np.random.default_rng(11)
lock, table = {}, []
for rule, g in S[S["yr"] <= 2016].groupby("rule"):
    Dl = deltas(g)
    day = g["day"].to_numpy()
    h1 = (g["yr"] <= 2013).to_numpy()
    rows = []
    for c in Dl.columns:
        x = Dl[c].to_numpy()
        pol = g[c] if c in TIMING else None
        rows.append(dict(rule=rule, cell=c, total_delta=float(x.sum()), t=tstat(x, day), d1013=float(x[h1].sum()), d1416=float(x[~h1].sum()),
                         trades=int(pol.notna().sum()) if pol is not None else int((x == 0).sum()),
                         net_per_trade=float(pol.mean()) if pol is not None else float(g["base"][x == 0].mean()),
                         stop=float(g[c + "_stop"][pol.notna()].mean()) if pol is not None else np.nan))
    R = pd.DataFrame(rows).sort_values("total_delta", ascending=False)
    base_tot = float(g["base"].sum() * THB)
    # family-wise null: the same day signs for every cell
    u, inv = np.unique(day, return_inverse=True)
    sums = np.stack([np.bincount(inv, weights=Dl[c].to_numpy()) for c in Dl.columns])  # cells x days
    N = np.bincount(inv)
    best_null = []
    for _ in range(500):
        sg = rng.choice([-1.0, 1.0], len(u))
        fs = sums * sg
        mu = fs.sum(1) / N.sum()
        se = np.sqrt(((fs - mu[:, None] * N) ** 2).sum(1) * len(u) / (len(u) - 1)) / N.sum()
        best_null.append(float(np.max(mu / se)))
    best_null = np.array(best_null)
    R["p_fw"] = [float(np.mean(best_null >= t)) for t in R["t"]]
    table.append(R)
    print(f"\nRULE {rule} 2010-16: base {len(g)} trades, {base_tot:+,.0f} THB, net {g['base'].mean():+.3f} $/oz; family-wise null best t "
          f"p50 {np.median(best_null):.2f} p95 {np.quantile(best_null, 0.95):.2f}")
    print(R.drop(columns="rule").round(3).to_string(index=False))
    cand = R[(R["t"] >= 2) & (R["d1013"] > 0) & (R["d1416"] > 0)]
    tim = cand[cand["cell"].isin(TIMING)]
    ses = cand[cand["cell"].str.startswith("S_")]
    lock[rule] = dict(timing=tim.iloc[0]["cell"] if len(tim) else None, session=ses.iloc[0]["cell"] if len(ses) else None,
                      timing_t=float(tim.iloc[0]["t"]) if len(tim) else None, timing_p_fw=float(tim.iloc[0]["p_fw"]) if len(tim) else None,
                      session_t=float(ses.iloc[0]["t"]) if len(ses) else None, session_p_fw=float(ses.iloc[0]["p_fw"]) if len(ses) else None)
    print("LOCK", rule, lock[rule])
pd.concat(table).to_csv(ROOT / "out" / "CELLS_2010_16.csv", index=False)
json.dump(lock, open(ROOT / "out" / "LOCK.json", "w"), indent=1)

print("\ndescriptive 2010-16: bounce extension after E0 (theta units, closes) - survival and mean remaining extension")
for rule, g in S[S["yr"] <= 2016].groupby("rule"):
    x = g["ext_theta"].to_numpy()
    line = []
    for a in (0.0, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0):
        m = x >= a
        line.append(f"x>={a}: {100 * m.mean():.0f}% rem {np.mean(x[m] - a):.2f}")
    print(rule, " | ".join(line))
