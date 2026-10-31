"""Owner 23:35: original swing v1 (code/swing_v1.py trades, not v1-r1), results by session of entry, 2010-2022."""
import numpy as np
import pandas as pd

import swing_v1 as v1

T = pd.concat([pd.read_pickle(v1.OUT / "V1_TRADES_2010_2019.private.pkl"), pd.read_pickle(v1.OUT / "V1_TRADES_2020_2022.private.pkl")],
              ignore_index=True)
ny = pd.to_datetime(T.t_entry * 60, unit="s", utc=True).dt.tz_convert("America/New_York")
h = ny.dt.hour
T["session"] = np.select([(h >= 18) | (h < 3), h < 8, h < 12], ["1 Asia", "2 London", "3 NY morning"], "4 NY afternoon")
T["yr"] = T["yr"].astype(int)


def agg(g):
    w, l = g.net_thb[g.net_thb > 0], g.net_thb[g.net_thb <= 0]
    return pd.Series(dict(trades=len(g), win=(g.net_thb > 0).mean(), wins=w.sum(), losses=l.sum(), net=g.net_thb.sum(),
                          per_trade=g.net_thb.mean(), stop=g.stopped.mean()))


pd.set_option("display.width", 250)
S = T.groupby("session").apply(agg, include_groups=False)
print("2010-2022 by session:")
print(S.round(3).to_string())
print("\nby session and rule:")
print(T.groupby(["session", "rule"]).apply(agg, include_groups=False)[["trades", "win", "net", "per_trade"]].round(3).to_string())
Y = T.pivot_table(index="yr", columns="session", values="net_thb", aggfunc="sum").round(0)
Y["total"] = Y.sum(1)
print("\nnet THB per year and session:")
print(Y.to_string())
print("\nyears positive per session:", (Y.drop(columns="total") > 0).sum().to_dict())
for per, (lo, hi) in {"2010-16": (2010, 2016), "2017-19": (2017, 2019), "2020-22": (2020, 2022)}.items():
    print(per, T[T.yr.between(lo, hi)].groupby("session").net_thb.sum().round(0).to_dict())
S.to_csv(v1.OUT / "V1_BY_SESSION_2010_2022.csv")
Y.to_csv(v1.OUT / "V1_BY_SESSION_YEAR_2010_2022.csv")
