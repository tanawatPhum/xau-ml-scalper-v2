"""Descriptive only, after the lock: what the state machine does on the owner's 2017 example London sessions
at smaller run sizes (the locked cell needs run >= 4u and took no trade there)."""
import numpy as np
import pandas as pd

from common import add_factors, load_sessions, trades

S = load_sessions([2017])
M = S["meta"]
days = ("2017-01-18", "2017-01-20", "2017-01-23", "2017-01-24")
k = M.index[M["key"].str[:10].isin(days) & (M["session"] == "london")].to_numpy()
sel = np.zeros(len(M), bool)
sel[k] = True
for i in k:
    a = S["sw"][i]
    print(M.loc[i, "key"], "u at lock $%.2f" % S["U"][a], "zones", np.round(S["zones"][M.loc[i, "key"]], 2).tolist())
for cell in ((0.5, 1.5, 0.382, 0.0, 0.25), (0.5, 1.5, 0.5, 0.0, 0.25), (0.5, 2.5, 0.382, 0.0, 0.25), (0.5, 4.0, 0.382, 0.25, 0.25)):
    D = add_factors(trades(S, sel, *cell), S)
    print("\ncell rho m r q s =", cell, "trades", len(D))
    for r in D.itertuples():
        ft = pd.Timestamp(int(r.t_fill) * 60, unit="s") + pd.Timedelta(hours=7)
        et = pd.Timestamp(int(r.t_exit) * 60, unit="s") + pd.Timedelta(hours=7)
        print(f"  {M.loc[r.k, 'key'][:10]} fill {ft:%H:%M} ICT  P {r.P:.2f} T {r.T:.2f} run {r.run_u:.1f}u  sell {r.X:.2f}  TP {r.TP:.2f}  "
              f"SL {r.SL:.2f}  exit {et:%H:%M} {r.exitp:.2f} ({ {1: 'TP', -1: 'SL', 0: 'end'}[r.oc] })  net {r.net:+.2f}  Z {r.Z}")
