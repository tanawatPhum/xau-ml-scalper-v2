"""Descriptive, after the check: A with its locked filter + B unfiltered (B's filter failed)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = pd.read_pickle(ROOT / "out" / "TRADES.private.pkl")
c = json.load(open(ROOT / "out" / "LOCK.json"))["A"]
X = D[(D["rule"] == "B") | (D["R"] >= c["R_min"])].sort_values("t_exit", kind="stable")
pnl = X["net"].to_numpy() * 10 * 33.77
eq = 100_000 + np.cumsum(pnl)
e0 = 100_000.0
for y in range(2010, 2020):
    m = (X["yr"] == y).to_numpy()
    e = e0 + np.cumsum(pnl[m])
    dd = (np.maximum.accumulate(np.r_[e0, e])[1:] - e).max()
    print(f"{y} | {m.sum()} | {pnl[m].sum():+,.0f} | {e[-1]:,.0f} | {dd:,.0f}")
    e0 = e[-1]
v = (X["yr"] >= 2017).to_numpy()
ev = np.cumsum(pnl[v])
print(f"2017-19 {pnl[v].sum():+,.0f} THB DD {(np.maximum.accumulate(np.r_[0.0, ev])[1:] - ev).max():,.0f}")
print(f"2010-19 end {eq[-1]:,.0f} max DD {(np.maximum.accumulate(np.r_[100_000, eq])[1:] - eq).max():,.0f}")
