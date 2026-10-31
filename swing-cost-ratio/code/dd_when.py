"""When did the max drawdown happen (base vs locked), and the worst single trade."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = pd.read_pickle(ROOT / "out" / "TRADES.private.pkl")
LK = json.load(open(ROOT / "out" / "LOCK.json"))
keep = np.zeros(len(D), bool)
for r, c in LK.items():
    keep |= (D["rule"] == r) & (D["R"] >= c["R_min"]) & (D["leg_ratio"] >= c["leg"])
for name, X in (("base", D), ("locked", D[keep])):
    X = X.sort_values("t_exit", kind="stable")
    pnl = X["net"].to_numpy() * 10 * 33.77
    eq = 100_000 + np.cumsum(pnl)
    pk = np.maximum.accumulate(eq)
    i = int(np.argmax(pk - eq))
    j = int(np.argmax(eq[: i + 1] == pk[i]))
    ts = pd.to_datetime(X["t_exit"].to_numpy() * 60, unit="s")
    w = int(np.argmin(pnl))
    print(f"{name}: max DD {pk[i] - eq[i]:,.0f} THB = from {eq[j]:,.0f} on {ts[j]:%Y-%m-%d} down to {eq[i]:,.0f} on {ts[i]:%Y-%m-%d} "
          f"({i - j} trades); back above the old peak: "
          f"{(ts[i + np.argmax(eq[i:] >= pk[i])] if (eq[i:] >= pk[i]).any() else 'not by end-2019')}; "
          f"worst single trade {pnl[w]:,.0f} THB on {ts[w]:%Y-%m-%d}")
