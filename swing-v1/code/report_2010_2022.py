"""Swing v1 yearly report 2010-2022 (100,000 THB start in 2010, A + B at 0.1 lot each). Reads the saved trades only."""
import numpy as np
import pandas as pd

import swing_v1 as v1

T = pd.concat([pd.read_pickle(v1.OUT / "V1_TRADES_2010_2019.private.pkl"), pd.read_pickle(v1.OUT / "V1_TRADES_2020_2022.private.pkl")],
              ignore_index=True).sort_values("t_exit", kind="stable")
pnl = T["net_thb"].to_numpy()
eq = 100_000 + np.cumsum(pnl)
rows, e0 = [], 100_000.0
for yr in range(2010, 2023):
    m = (T["yr"] == yr).to_numpy()
    p = pnl[m]
    e = e0 + np.cumsum(p)
    pk = np.maximum.accumulate(np.r_[e0, e])[1:]
    rows.append(dict(yr=yr, trades=int(m.sum()), win=f"{100 * (p > 0).mean():.0f}%", wins=p[p > 0].sum(), losses=p[p <= 0].sum(), net=p.sum(),
                     A=p[(T["rule"] == "A").to_numpy()[m]].sum(), B=p[(T["rule"] == "B").to_numpy()[m]].sum(), start=e0, end=e[-1],
                     best=p.max(), worst=p.min(), dd=(pk - e).max()))
    e0 = e[-1]
R = pd.DataFrame(rows)
R.to_csv(v1.OUT / "V1_YEARLY_2010_2022.csv", index=False)
pd.set_option("display.width", 250)
print(R.round(0).to_string(index=False))
pk = np.maximum.accumulate(np.r_[100_000, eq])[1:]
print(f"total net {pnl.sum():,.0f} | trades {len(T)} | win {100 * (pnl > 0).mean():.1f}% | end {eq[-1]:,.0f} | max DD {(pk - eq).max():,.0f} | "
      f"lowest {eq.min():,.0f} | positive years {(R['net'] > 0).sum()}/13")
