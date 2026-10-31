"""Owner 22:21: per year, total of winning trades and total of losing trades separately (Exness version EX)."""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
T = pd.read_csv(HERE / "out" / "TRADES_EX.private.csv")
T["yr"] = pd.to_datetime(T.t_exit * 60, unit="s").dt.year
rows = []
for y, g in T.groupby("yr"):
    w, l = g[g.net_thb > 0], g[g.net_thb <= 0]
    rows.append(dict(yr=y, trades=len(g), win_n=len(w), win_thb=w.net_thb.sum(), loss_n=len(l), loss_thb=l.net_thb.sum(),
                     net=g.net_thb.sum(), best=g.net_thb.max(), worst=g.net_thb.min(), spread=g.spread_cost_thb.sum()))
R = pd.DataFrame(rows)
tot = dict(yr="total", trades=R.trades.sum(), win_n=R.win_n.sum(), win_thb=R.win_thb.sum(), loss_n=R.loss_n.sum(), loss_thb=R.loss_thb.sum(),
           net=R.net.sum(), best=R.best.max(), worst=R.worst.min(), spread=R.spread.sum())
R = pd.concat([R, pd.DataFrame([tot])])
R.to_csv(HERE / "out" / "GROSS_BY_YEAR_EX.csv", index=False)
pd.set_option("display.width", 250)
print(R.round(0).to_string(index=False))
