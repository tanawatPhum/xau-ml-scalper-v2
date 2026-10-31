"""Pre-registered verdict + reported metrics (see ../PLAN.md)."""

import json

import numpy as np

from fade_exec import CACHE, CELLS, DELAYS, OUT, PRIMARY, STOPS

DAYS = {int(k): v for k, v in json.load(open(OUT / "TRADING_DAYS.json")).items()}


def load(tu, d, k, null=False):
    pre = "NULL" if null else "T"
    return dict(np.load(CACHE / f"{pre}_th{tu}_d{d}_k{k:g}.private.npz"))


def sel(z, code):
    if code is None:
        m = np.ones(len(z["net"]), bool)
    elif code == "patterned":
        m = z["code"] >= 0
    else:
        m = z["code"] == code
    return {k: v[m] for k, v in z.items()}


def day_key(t_ent):
    return (t_ent.astype(np.int64) * 60 + 3 * 3600) // 86400


def ct(x, day):
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


def summary(z):
    yr, out = z["yr"], {}
    for per, m in (("disc", yr <= 2016), ("conf", yr >= 2017)):
        mu, t = ct(z["net"][m], day_key(z["t_ent"][m]))
        out[per] = dict(net=mu, t=t, n=int(m.sum()))
    out["ynet"] = {y: float(z["net"][yr == y].mean()) for y in range(2017, 2023)}
    out["years_pos"] = int(sum(v > 0 for v in out["ynet"].values()))
    c = yr >= 2017
    out["gross_conf"] = float(z["gross"][c].mean())
    out["stop_rate_conf"] = float((z["reason"][c] == 1).mean())
    out["pass"] = bool(out["conf"]["net"] > 0 and out["conf"]["t"] >= 2 and out["years_pos"] >= 4
                       and out["disc"]["net"] >= 0)
    return out


def extra(z):
    c = z["yr"] >= 2017
    x, te = z["net"][c], z["t_ent"][c]
    o = np.argsort(te, kind="stable")
    x, te = x[o], te[o]
    eq = np.cumsum(x)
    dd = float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max())
    streak = best = 0
    for v in x:
        streak = streak + 1 if v <= 0 else 0
        best = max(best, streak)
    mon = (te.astype(np.int64) * 60).astype("datetime64[s]").astype("datetime64[M]")
    um, inv = np.unique(mon, return_inverse=True)
    msum = np.bincount(inv, weights=x)
    dk = day_key(te)
    wk = np.unique(dk[((dk + 3) % 7) < 5])
    ndays = sum(DAYS[y] for y in range(2017, 2023))
    hr = (te.astype(np.int64) % 1440) // 60
    sess = {}
    for name, lo, hi in (("Asia 00-07", 0, 7), ("London 07-13", 7, 13), ("NY 13-21", 13, 21),
                         ("late 21-24", 21, 24)):
        m = (hr >= lo) & (hr < hi)
        sess[name] = dict(n_per_day=float(m.sum() / ndays), net=float(x[m].mean()) if m.any() else None)
    w = x > 0
    return dict(trades_per_day=float(len(x) / ndays), share_days_with_trade=float(len(wk) / ndays),
                win=float(w.mean()), avg_win=float(x[w].mean()), avg_loss=float(x[~w].mean()),
                p1=float(np.quantile(x, 0.01)), worst=float(x.min()), total=float(x.sum()),
                max_dd=dd, longest_losing_streak=int(best),
                months_pos=float((msum > 0).mean()), n_months=int(len(um)),
                median_hold_min=float(np.median(z["hold"][c])), sessions=sess)


rep = {"cells": {}, "null": {}}
for cell, (tu, code) in CELLS.items():
    rep["cells"][cell] = {}
    for d in DELAYS:
        for k in STOPS:
            rep["cells"][cell][f"d{d}_k{k:g}"] = summary(sel(load(tu, d, k), code))
    rep["cells"][cell]["primary_extra"] = extra(sel(load(tu, *PRIMARY), code))
    for k in (0.0, 2.0):
        z = sel(load(tu, 1, k, null=True), code)
        mu, t = ct(z["gross"], day_key(z["t_ent"]))
        rep["null"][f"{cell} d1_k{k:g}"] = dict(gross=mu, t=t, n=int(len(z["gross"])))
json.dump(rep, open(OUT / "REPORT.json", "w"), indent=1)

pk = f"d{PRIMARY[0]}_k{PRIMARY[1]:g}"
print("=== PRIMARY (delay 1 min, stop 2 theta): 2010-16 net (t) | 2017-22 net (t) | years>0 | PASS")
for cell, r in rep["cells"].items():
    s = r[pk]
    print(f"  {cell:20s} {s['disc']['net']:+.3f} ({s['disc']['t']:+.1f}) | {s['conf']['net']:+.3f} "
          f"({s['conf']['t']:+.1f}) n {s['conf']['n']} | {s['years_pos']}/6 | {s['pass']} | stop rate "
          f"{100 * s['stop_rate_conf']:.1f}% | years {' '.join(f'{v:+.2f}' for v in s['ynet'].values())}")
print("\n=== Sensitivity, 2017-22 net (t) [2010-16 net]")
for cell, r in rep["cells"].items():
    print(" ", cell)
    for d in DELAYS:
        row = []
        for k in STOPS:
            s = r[f"d{d}_k{k:g}"]
            row.append(f"stop {('none' if k == 0 else f'{k:g}th'):5s} {s['conf']['net']:+.3f} ({s['conf']['t']:+.1f}) "
                       f"[{s['disc']['net']:+.3f}]")
        print(f"    delay {d}: " + " | ".join(row))
print("\n=== Primary extra (2017-22, per 1 oz)")
for cell, r in rep["cells"].items():
    e = r["primary_extra"]
    print(f"  {cell}: trades/day {e['trades_per_day']:.2f}, days with trade {100 * e['share_days_with_trade']:.0f}%, "
          f"win {100 * e['win']:.1f}%, avg win {e['avg_win']:+.2f}, avg loss {e['avg_loss']:+.2f}, p1 {e['p1']:+.2f}, "
          f"worst {e['worst']:+.2f}, total {e['total']:+.1f}, maxDD {e['max_dd']:.1f}, losing streak "
          f"{e['longest_losing_streak']}, months>0 {100 * e['months_pos']:.0f}% of {e['n_months']}, hold "
          f"{e['median_hold_min']:.0f} min")
    print("     sessions: " + "; ".join(f"{k} {v['n_per_day']:.2f}/day net {v['net']:+.3f}"
                                     for k, v in e["sessions"].items() if v["net"] is not None))
print("\n=== Sign-flip null gross (should be ~0)")
for k, v in rep["null"].items():
    print(f"  {k:28s} gross {v['gross']:+.4f} (t {v['t']:+.2f}) n {v['n']}")
