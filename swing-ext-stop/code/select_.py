"""2010-16 only: paired gain of stop s x theta vs the 3 theta base, family-wise null, automatic LOCK (see ../PLAN.md)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
S = pd.read_pickle(ROOT / "out" / "SIGNALS.private.pkl")
S = S[S["keep"] & (S["yr"] <= 2016)]
THB = 10 * 33.77
CELLS = ["s1.0", "s1.25", "s1.5", "s2.0", "s2.5"]


def tstat(x, day):
    u, inv = np.unique(day, return_inverse=True)
    Ssum, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = Ssum.sum() / N.sum()
    se = np.sqrt(((Ssum - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return mu / se


rng = np.random.default_rng(13)
lock, out = {}, []
for rule, g in S.groupby("rule"):
    day = g["day"].to_numpy()
    h1 = (g["yr"] <= 2013).to_numpy()
    base = g["s3.0"].to_numpy() * THB
    rows, dl = [], {}
    for c in ["s3.0"] + CELLS:
        p = g[c].to_numpy() * THB
        x = p - base
        dl[c] = x
        w, lo = p[p > 0], p[p <= 0]
        rows.append(dict(rule=rule, cell=c, total_thb=float(p.sum()), gain=float(x.sum()), t=tstat(x, day) if c != "s3.0" else 0.0,
                         g1013=float(x[h1].sum()), g1416=float(x[~h1].sum()), win=float((p > 0).mean()), avg_win=float(w.mean()),
                         avg_loss=float(lo.mean()), stop=float(g[c + "_stop"].mean()), worst=float(p.min()),
                         hold_med=float(g[c + "_hold"].median())))
    R = pd.DataFrame(rows)
    u, inv = np.unique(day, return_inverse=True)
    sums = np.stack([np.bincount(inv, weights=dl[c]) for c in CELLS])
    N = np.bincount(inv)
    bn = []
    for _ in range(500):
        fs = sums * rng.choice([-1.0, 1.0], len(u))
        mu = fs.sum(1) / N.sum()
        se = np.sqrt(((fs - mu[:, None] * N) ** 2).sum(1) * len(u) / (len(u) - 1)) / N.sum()
        bn.append(float(np.max(mu / se)))
    bn = np.array(bn)
    R["p_fw"] = [float(np.mean(bn >= t)) if c != "s3.0" else np.nan for c, t in zip(R["cell"], R["t"])]
    out.append(R)
    print(f"\nRULE {rule} 2010-16 ({len(g)} trades); family-wise null best t p95 {np.quantile(bn, 0.95):.2f}")
    print(R.drop(columns="rule").round(3).to_string(index=False))
    cand = R[(R["cell"] != "s3.0") & (R["t"] >= 2) & (R["g1013"] > 0) & (R["g1416"] > 0)].sort_values("gain", ascending=False)
    lock[rule] = dict(stop=float(cand.iloc[0]["cell"][1:]) if len(cand) else 3.0, t=float(cand.iloc[0]["t"]) if len(cand) else None,
                      p_fw=float(cand.iloc[0]["p_fw"]) if len(cand) else None, gain_2010_16=float(cand.iloc[0]["gain"]) if len(cand) else 0.0)
    print("LOCK", rule, lock[rule])
pd.concat(out).to_csv(ROOT / "out" / "CELLS_2010_16.csv", index=False)
json.dump(lock, open(ROOT / "out" / "LOCK.json", "w"), indent=1)
