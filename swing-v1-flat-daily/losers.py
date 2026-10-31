"""Owner 22:14: what do the losing trades mostly look like? Exness version (mode EX), 2010-2022, 0.1 lot per rule."""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
T = pd.read_csv(HERE / "out" / "TRADES_EX.private.csv")
T["theta_usd"] = T["theta_bps"] * T["entry_mid"] / 1e4
T["theta_thb"] = T["theta_usd"] * 10 * 33.77
T["net_theta"] = T["net_thb"] / T["theta_thb"]
T["gross_theta"] = T["gross_mid_thb"] / T["theta_thb"]
T["hold"] = T["t_exit"] - T["t_entry"]
ny = pd.to_datetime(T["t_entry"] * 60, unit="s", utc=True).dt.tz_convert("America/New_York")
T["ny_hour"] = ny.dt.hour
T["sess"] = np.select([(T.ny_hour >= 18) | (T.ny_hour < 3), T.ny_hour < 8, T.ny_hour < 12], ["Asia (18-03 NY)", "London (03-08 NY)", "NY morning (08-12 NY)"],
                      "NY afternoon (12-17 NY)")
W, L = T[T.net_thb > 0], T[T.net_thb <= 0]
print(f"trades {len(T)}, winners {len(W)} ({len(W) / len(T):.1%}) +{W.net_thb.sum():,.0f} THB, losers {len(L)} ({len(L) / len(T):.1%}) {L.net_thb.sum():,.0f} THB")
print(f"average win {W.net_thb.mean():+,.0f} THB ({W.net_theta.mean():+.2f} theta), average loss {L.net_thb.mean():+,.0f} THB ({L.net_theta.mean():+.2f} theta)")
print(f"median hold: winners {W.hold.median():.0f} min, losers {L.hold.median():.0f} min")

print("\nlosers by exit reason:")
g = L.groupby("exit_reason").agg(n=("net_thb", "size"), loss=("net_thb", "sum"), avg=("net_thb", "mean"), avg_theta=("net_theta", "mean"),
                                  hold=("hold", "median"))
g["share_n"] = g.n / len(L)
g["share_loss"] = g.loss / L.net_thb.sum()
print(g.round(3).to_string())

print("\nlosers by size (net loss in theta):")
b = pd.cut(-L.net_theta, [-np.inf, 0.25, 0.5, 1, 1.5, 2, 3, np.inf], labels=["<0.25", "0.25-0.5", "0.5-1", "1-1.5", "1.5-2", "2-3", ">3"])
s = L.groupby(b, observed=False).agg(n=("net_thb", "size"), loss=("net_thb", "sum"))
s["share_n"] = s.n / len(L)
s["share_loss"] = s.loss / L.net_thb.sum()
print(s.round(3).to_string())
sp = L[L.gross_mid_thb >= 0]
print(f"\nlosers that were flat or positive before the spread (lost only to the spread): {len(sp)} ({len(sp) / len(L):.1%} of losers), "
      f"{sp.net_thb.sum():,.0f} THB")

print("\nby rule:")
print(T.groupby("rule").apply(lambda x: pd.Series(dict(trades=len(x), losers=(x.net_thb <= 0).mean(), loss=x.net_thb[x.net_thb <= 0].sum(),
                                                       avg_loss=x.net_thb[x.net_thb <= 0].mean(), stop_losers=(x[x.net_thb <= 0].exit_reason == "stop").mean()))).round(3).to_string())
print("\nby session of entry (NY time):")
print(T.groupby("sess").apply(lambda x: pd.Series(dict(trades=len(x), win=(x.net_thb > 0).mean(), net=x.net_thb.sum(), loss=x.net_thb[x.net_thb <= 0].sum(),
                                                       avg_loss=x.net_thb[x.net_thb <= 0].mean()))).round(3).to_string())
print("\nby side:")
print(T.groupby("side").apply(lambda x: pd.Series(dict(trades=len(x), win=(x.net_thb > 0).mean(), net=x.net_thb.sum()))).round(3).to_string())
print("\n10 worst trades:")
w = L.nsmallest(10, "net_thb").copy()
w["entry_ny"] = pd.to_datetime(w.t_entry * 60, unit="s", utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d %H:%M")
w["side"] = np.where(w.side > 0, "BUY", "SELL")
print(w[["entry_ny", "rule", "side", "exit_reason", "theta_usd", "net_theta", "hold", "net_thb"]].round(2).to_string(index=False))
print("\nlosers by year:")
print(L.assign(yr=pd.to_datetime(L.t_exit * 60, unit="s").dt.year).groupby("yr").agg(n=("net_thb", "size"), loss=("net_thb", "sum"),
                                                                                     stop=("exit_reason", lambda v: (v == "stop").mean())).round(3).to_string())
