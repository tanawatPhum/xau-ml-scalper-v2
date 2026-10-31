"""Per-trade risk profile of v1-r2 (descriptive, 2010-2022 fixed-spread trades, 0.1 lot per rule)."""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "out"
t = pd.read_csv(OUT / "TRADES_2010_2022_v1-r2.private.csv")
t["theta_usd"] = t.theta_bps / 1e4 * t.entry_mid
t["risk_thb"] = 2.5 * t.theta_usd * 10 * 33.77          # loss at the stop level, before spread/gap
t["win"] = t.net_thb > 0
t["year"] = pd.to_datetime(t.t_exit * 60, unit="s", utc=True).dt.year


def prof(g):
    w, l = g[g.win], g[~g.win]
    return pd.Series(dict(n=len(g), win_pct=100 * g.win.mean(), avg_win=w.net_thb.mean(), avg_loss=l.net_thb.mean(),
                          stop_pct=100 * (g.exit_reason == "stop").mean(),
                          avg_stop=g.loc[g.exit_reason == "stop", "net_thb"].mean(),
                          avg_net=g.net_thb.mean(), avg_risk=g.risk_thb.mean(),
                          worst=g.net_thb.min(), best=g.net_thb.max()))


pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
import warnings; warnings.filterwarnings("ignore")
pd.set_option("display.float_format", lambda x: f"{x:,.0f}")
print("exit reasons:", t.exit_reason.value_counts().to_dict())
print("\nBY RULE\n", t.groupby("rule").apply(prof))
print("\nBY EXIT\n", t.groupby(["rule", "exit_reason"]).apply(prof)[["n", "avg_net", "worst"]])
for r in ("A", "B"):
    g = t[t.rule == r].copy()
    g["q"] = pd.qcut(g.theta_usd, 5, labels=False)
    tab = g.groupby("q").apply(prof)
    tab.insert(0, "theta_usd", g.groupby("q").theta_usd.agg(lambda s: f"{s.min():.1f}-{s.max():.1f}"))
    print(f"\nRULE {r} BY THETA$ QUINTILE\n", tab)
# loss beyond the planned stop (gap/slippage)
s = t[t.exit_reason == "stop"]
print("\nstop trades: loss / planned risk  median %.2f  p95 %.2f  max %.2f" %
      tuple(np.percentile(-s.net_thb / s.risk_thb, [50, 95, 100])))
# win-rate stability by year
print("\nwin% by year\n", t.groupby("year").win.mean().mul(100).round(0).to_dict())
