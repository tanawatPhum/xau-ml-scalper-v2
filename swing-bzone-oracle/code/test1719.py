"""2017-19 blind test of the setup locked in out/LOCK.json (run once; see ../PLAN.md v2)."""
import json

import numpy as np
import pandas as pd

from common import FX, OZ, ROOT, add_factors, ct, load_sessions, trades

LK = json.load(open(ROOT / "out" / "LOCK.json"))
c = LK["cell"]
S = load_sessions([2017, 2018, 2019])
M = S["meta"]
NDAYS = int(((M["lock"] + 180) // 1440).nunique())
sel = np.ones(len(M), bool)
D = add_factors(trades(S, sel, c["rho"], c["m"], c["r"], c["q"], c["s"]), S)
for f, (a, b) in LK["cuts"].items():
    D[f + "_g"] = np.where(D[f] <= a, 0, np.where(D[f] <= b, 1, 2))
COL = {"Z": "Z", "run_u": "run_u_g", "speed": "speed_g", "bounce_min": "bounce_min_g", "session": "session"}
F = D
for f, g in LK["filters"]:
    F = F[F[COL[f]].astype(str) == g]


def summ(X):
    mu, se = ct(X["net"], X["day"])
    yrs = {}
    for yr, x in X.groupby("yr"):
        thb = x.sort_values("t_exit")["net"].to_numpy() * OZ * FX
        eq = np.cumsum(thb)
        yrs[int(yr)] = dict(n=len(x), win=float((x["oc"] == 1).mean()), thb=float(thb.sum()),
                            dd=float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max()))
    thb = X.sort_values("t_exit")["net"].to_numpy() * OZ * FX
    eq = np.cumsum(thb)
    return dict(n=len(X), net=mu, t=mu / se if se > 0 else 0.0, gross=float(X["gross"].mean()), win=float((X["oc"] == 1).mean()),
                loss=float((X["oc"] == -1).mean()), none=float((X["oc"] == 0).mean()), p0=float(X["p0"].mean()), per_day=len(X) / NDAYS,
                thb=float(thb.sum()), dd=float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max()) if len(eq) else 0.0, years=yrs)


A, B = summ(D), summ(F)
pas = bool(B["net"] > 0 and B["t"] >= 2 and sum(v["thb"] > 0 for v in B["years"].values()) >= 2)
json.dump(dict(locked=LK["cell"], filters=LK["filters"], edge_found_2011_16=LK["edge_found"], cell_all=A, locked_filtered=B, pass_=pas),
          open(ROOT / "out" / "TEST_2017_19.json", "w"), indent=1)
D.to_pickle(ROOT / "out" / "TRADES_2017_19.private.pkl")
for name, X in (("cell, all trades", A), ("locked (cell + filters)", B)):
    print(f"{name}: n {X['n']} ({X['per_day']:.2f}/day) net {X['net']:+.3f} $/oz (t {X['t']:+.2f}) gross {X['gross']:+.3f} | TP {100 * X['win']:.0f}% "
          f"SL {100 * X['loss']:.0f}% session-end {100 * X['none']:.0f}% | RW TP-before-SL {100 * X['p0']:.0f}% | {X['thb']:+,.0f} THB dd {X['dd']:,.0f}")
    for yr, v in X["years"].items():
        print(f"   {yr}: {v['n']} trades TP {100 * v['win']:.0f}% {v['thb']:+,.0f} THB dd {v['dd']:,.0f}")
print("PASS:", pas, "| edge found on 2011-16:", LK["edge_found"])
print("\nowner's example London sessions (cell, all trades):")
for d in ("2017-01-18", "2017-01-20", "2017-01-23", "2017-01-24"):
    k = M.index[M["key"].str.startswith(d) & (M["session"] == "london")]
    x = D[D["k"].isin(k)]
    print(d, "london:", len(x), "trades")
    for r in x.itertuples():
        ft = pd.Timestamp(int(r.t_fill) * 60, unit="s") + pd.Timedelta(hours=7)
        print(f"   fill {ft:%H:%M} ICT P {r.P:.2f} T {r.T:.2f} sell {r.X:.2f} TP {r.TP:.2f} SL {r.SL:.2f} exit {r.exitp:.2f} "
              f"({ {1: 'TP', -1: 'SL', 0: 'end'}[r.oc] }) net {r.net:+.2f} Z {r.Z}")
