"""Per-year view of the accepted set (rules A and B together), 100,000 THB, 0.01 lot each rule
(1 oz each), USD/THB 33.77, 2010-2019 in-sample. Realised at trade exit."""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE, OUT = ROOT / "cache", ROOT / "out"
FX, START = 33.77, 100_000.0
A = dict(np.load(CACHE / "ROWS_A.private.npz"))
B = dict(np.load(CACHE / "ROWS_B.private.npz"))
net = np.concatenate([A["net"], B["net"]]) * FX            # 1 oz each = 0.01 lot each
te = np.concatenate([A["t_exit"], B["t_exit"]])
yr = np.concatenate([A["yr"], B["yr"]])
rule = np.r_[np.zeros(len(A["net"]), int), np.ones(len(B["net"]), int)]
o = np.argsort(te, kind="stable")
net, te, yr, rule = net[o], te[o], yr[o], rule[o]
eq = START + np.cumsum(net)
peak = np.maximum.accumulate(np.r_[START, eq])[1:]
out, eq0 = {}, START
print("year | trades A+B | win | P&L A | P&L B | P&L total | % of 100k | start -> end | max DD in year | worst month")
for y in range(2010, 2020):
    m = yr == y
    p = net[m]
    e = eq0 + np.cumsum(p)
    pk = np.maximum.accumulate(np.r_[eq0, e])[1:]
    mon = (te[m] * 60).astype("datetime64[s]").astype("datetime64[M]")
    _, inv = np.unique(mon, return_inverse=True)
    ms = np.bincount(inv, weights=p)
    r = dict(trades=int(m.sum()), win=float((p > 0).mean()), pnl_A=float(p[rule[m] == 0].sum()),
             pnl_B=float(p[rule[m] == 1].sum()), pnl=float(p.sum()), start=eq0, end=float(e[-1]),
             dd=float((pk - e).max()), worst_month=float(ms.min()))
    out[y] = r
    print(f"{y} | {r['trades']} | {100 * r['win']:.0f}% | {r['pnl_A']:+,.0f} | {r['pnl_B']:+,.0f} | {r['pnl']:+,.0f} | "
          f"{r['pnl'] / START * 100:+.0f}% | {r['start']:,.0f} -> {r['end']:,.0f} | {r['dd']:,.0f} | {r['worst_month']:+,.0f}")
    eq0 = r["end"]
dd_all = float((peak - eq).max())
i = int(np.argmax(peak - eq))
print(f"whole period: end {eq[-1]:,.0f} THB, lowest equity {eq.min():,.0f}, max drawdown {dd_all:,.0f} THB "
      f"(to {(te[i] * 60).astype('datetime64[s]').astype('datetime64[D]')})")
out["whole"] = dict(end=float(eq[-1]), lowest=float(eq.min()), max_dd=dd_all)
json.dump(out, open(OUT / "YEARLY_AB_100K.json", "w"), indent=1)
