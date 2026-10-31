"""2017-19 check of the filters locked in out/LOCK.json (once), plus the A + B money table 2010-19 (see ../PLAN.md)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = pd.read_pickle(ROOT / "out" / "TRADES.private.pkl")
LK = json.load(open(ROOT / "out" / "LOCK.json"))
OZ, FX, START = 10, 33.77, 100_000.0


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


keep = np.zeros(len(D), bool)
for rule, c in LK.items():
    m = D["rule"] == rule
    keep |= m & (D["R"] >= c["R_min"]) & (D["leg_ratio"] >= c["leg"])
D["keep"] = keep
V = D[D["yr"] >= 2017]
NDAYS = V["day"].nunique()
res = {}
for rule in ("A", "B"):
    b, f = V[V["rule"] == rule], V[(V["rule"] == rule) & V["keep"]]
    mb, tb = ct(b["net"], b["day"])
    mf, tf = ct(f["net"], f["day"])
    res[rule] = dict(base=dict(n=len(b), per_day=len(b) / NDAYS, net=mb, t=tb, thb=float(b["net"].sum() * OZ * FX)),
                     filt=dict(n=len(f), per_day=len(f) / NDAYS, net=mf, t=tf, thb=float(f["net"].sum() * OZ * FX)),
                     rule_pass=bool(mf > mb and tf >= 2))
    print(f"RULE {rule} 2017-19 base: n {len(b)} ({len(b) / NDAYS:.2f}/day) net {mb:+.3f} t {tb:+.2f} {b['net'].sum() * OZ * FX:+,.0f} THB | "
          f"filtered: n {len(f)} ({len(f) / NDAYS:.2f}/day) net {mf:+.3f} t {tf:+.2f} {f['net'].sum() * OZ * FX:+,.0f} THB -> rule pass {res[rule]['rule_pass']}")


def money(X, col="net"):
    X = X.sort_values("t_exit", kind="stable")
    pnl = X[col].to_numpy() * OZ * FX
    eq = START + np.cumsum(pnl)
    rows, e0 = {}, START
    for y in range(2010, 2020):
        m = (X["yr"] == y).to_numpy()
        e = e0 + np.cumsum(pnl[m])
        pk = np.maximum.accumulate(np.r_[e0, e])[1:]
        rows[y] = dict(n=int(m.sum()), net=float(pnl[m].sum()), end=float(e[-1]) if m.any() else e0, dd=float((pk - e).max()) if m.any() else 0.0)
        e0 = rows[y]["end"]
    v = (X["yr"] >= 2017).to_numpy()
    ev = np.cumsum(pnl[v])
    dd_v = float((np.maximum.accumulate(np.r_[0.0, ev])[1:] - ev).max())
    return dict(rows=rows, end=float(eq[-1]), max_dd=float((np.maximum.accumulate(np.r_[START, eq])[1:] - eq).max()),
                v_thb=float(pnl[v].sum()), v_dd=dd_v)


MB, MF = money(D), money(D[D["keep"]])
MBd, MFd = money(D, "duka"), money(D[D["keep"]], "duka")
ratio_b, ratio_f = MB["v_thb"] / MB["v_dd"], MF["v_thb"] / MF["v_dd"]
port_pass = bool(ratio_f > ratio_b)
print(f"\nA+B 2017-19: base {MB['v_thb']:+,.0f} THB / DD {MB['v_dd']:,.0f} (ratio {ratio_b:.2f}) | filtered {MF['v_thb']:+,.0f} / DD {MF['v_dd']:,.0f} "
      f"(ratio {ratio_f:.2f}) -> portfolio pass {port_pass}")
print("\nyear | base trades | base THB | base end | base DD | filtered trades | filtered THB | filtered end | filtered DD")
for y in range(2010, 2020):
    a, b = MB["rows"][y], MF["rows"][y]
    print(f"{y} | {a['n']} | {a['net']:+,.0f} | {a['end']:,.0f} | {a['dd']:,.0f} | {b['n']} | {b['net']:+,.0f} | {b['end']:,.0f} | {b['dd']:,.0f}")
print(f"2010-19 end: base {MB['end']:,.0f} (max DD {MB['max_dd']:,.0f}) | filtered {MF['end']:,.0f} (max DD {MF['max_dd']:,.0f})")
print(f"Dukascopy-spread stress end: base {MBd['end']:,.0f} | filtered {MFd['end']:,.0f}")
json.dump(dict(lock=LK, rules=res, portfolio_pass=port_pass, base=MB, filtered=MF, duka_base_end=MBd["end"], duka_filt_end=MFd["end"]),
          open(ROOT / "out" / "CHECK_2017_19.json", "w"), indent=1, default=float)
