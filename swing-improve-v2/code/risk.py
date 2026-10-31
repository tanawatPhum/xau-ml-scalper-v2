"""Part 2: drawdown controls (pre-registered in ../PLAN.md). Per-oz P&L, realised at trade exit."""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE, OUT = ROOT / "cache", ROOT / "out"
DAYS = {int(k): v for k, v in json.load(open(ROOT.parent / "swing-adaptive-bounce" / "out" / "TRADING_DAYS.json")).items()}
PERIODS = {"2010-16": list(range(2010, 2017)), "2017-19": [2017, 2018, 2019]}
FX = 33.77


def load(rule):
    z = dict(np.load(CACHE / f"ROWS_{rule}.private.npz"))
    o = np.argsort(z["t_ent"], kind="stable")
    return {f: a[o] for f, a in z.items()}


def metrics(pnl, z, yrs):
    m = np.isin(z["yr"], yrs) & (pnl != 0)
    p, te = pnl[m], z["t_exit"][m]
    o = np.argsort(te, kind="stable")
    p, te = p[o], te[o]
    eq = np.cumsum(p)
    peak = np.maximum.accumulate(np.r_[0.0, eq])[1:]
    dd = float((peak - eq).max()) if len(eq) else 0.0
    under, longest, t0 = False, 0.0, 0
    for k in range(len(eq)):
        if eq[k] < peak[k] and not under:
            under, t0 = True, te[k]
        elif eq[k] >= peak[k] and under:
            under, longest = False, max(longest, (te[k] - t0) / 1440)
    if under:
        longest = max(longest, (te[-1] - t0) / 1440)
    mon = (te * 60).astype("datetime64[s]").astype("datetime64[M]")
    _, inv = np.unique(mon, return_inverse=True)
    ms = np.bincount(inv, weights=p)
    total = float(p.sum())
    return dict(trades=int(m.sum()), total=total, net_per_day=total / sum(DAYS[y] for y in yrs), max_dd=dd,
                calmar=(total / len(yrs)) / dd if dd > 0 else np.inf, worst_month=float(ms.min()),
                months_pos=float((ms > 0).mean()), underwater_days=float(longest))


def size_r1(z):
    th = z["th_usd"]
    disc = z["yr"] <= 2016
    lo, hi = 1e-6, 1e3
    for _ in range(100):
        c = (lo + hi) / 2
        s = np.minimum(c / th[disc], 3.0).mean()
        lo, hi = (c, hi) if s < 1 else (lo, c)
    return np.minimum(c / th, 3.0)


def take_r2(z):
    take = np.ones(len(z["net"]), bool)
    for i in range(len(take)):
        same = (z["day"][:i] == z["day"][i]) & take[:i] & (z["t_exit"][:i] <= z["t_ent"][i]) & (z["net"][:i] <= 0)
        if same.sum() >= 2:
            take[i] = False
    return take


def take_r3(z, n=50):
    take = np.ones(len(z["net"]), bool)
    order = np.argsort(z["t_exit"], kind="stable")
    ex_t, ex_p = z["t_exit"][order], z["net"][order]
    cs = np.r_[0.0, np.cumsum(ex_p)]
    for i in range(len(take)):
        k = np.searchsorted(ex_t, z["t_ent"][i], side="right")  # trades closed by this entry
        if k >= n:
            take[i] = cs[k] - cs[k - n] >= 0
    return take


def evaluate(pnl, z):
    return {p: metrics(pnl, z, yrs) for p, yrs in PERIODS.items()} | {"2010-19": metrics(pnl, z, list(range(2010, 2020)))}


Z = {r: load(r) for r in ("A", "B")}
res, pnls = {}, {}
for r, z in Z.items():
    base = z["net"].copy()
    pnls[(r, "R0")] = base
    pnls[(r, "R1")] = base * size_r1(z)
    pnls[(r, "R2")] = np.where(take_r2(z), base, 0.0)
    pnls[(r, "R3")] = np.where(take_r3(z), base, 0.0)
    for c in ("R0", "R1", "R2", "R3"):
        res[f"{r} {c}"] = evaluate(pnls[(r, c)], z)
# portfolio A + B at 0.5 oz each
AB = {f: np.concatenate([Z["A"][f], Z["B"][f]]) for f in Z["A"]}
pab = 0.5 * np.concatenate([Z["A"]["net"], Z["B"]["net"]])
res["A+B R4"] = evaluate(pab, AB)


def better(a, b):
    return all(res[a][p]["calmar"] > res[b][p]["calmar"] and res[a][p]["max_dd"] < res[b][p]["max_dd"] for p in PERIODS)


acc = {r: [c for c in ("R1", "R2", "R3") if better(f"{r} {c}", f"{r} R0")] for r in ("A", "B")}
acc["R4"] = better("A+B R4", "A R0") and better("A+B R4", "B R0")
# accepted controls together (report only)
final = {}
for r, z in Z.items():
    w = np.ones(len(z["net"]))
    take = np.ones(len(z["net"]), bool)
    if "R1" in acc[r]:
        w = size_r1(z)
    if "R2" in acc[r]:
        take &= take_r2(z)
    if "R3" in acc[r]:
        take &= take_r3(z)
    final[r] = np.where(take, z["net"] * w, 0.0)
    res[f"{r} FINAL"] = evaluate(final[r], z)
if acc["R4"]:
    res["A+B FINAL"] = evaluate(0.5 * np.concatenate([final["A"], final["B"]]), AB)
rep = dict(results=res, accepted=acc)
json.dump(rep, open(OUT / "RISK.json", "w"), indent=1, default=float)
print("Per oz (today's $). Columns: trades | net/day | max DD | Calmar | worst month | months>0 | longest under water (days)")
for name, r in res.items():
    print(name)
    for p, s in r.items():
        print(f"   {p}: {s['trades']:5d} | {s['net_per_day']:+.3f} | {s['max_dd']:7.1f} | {s['calmar']:5.2f} | "
              f"{s['worst_month']:+7.1f} | {100 * s['months_pos']:3.0f}% | {s['underwater_days']:5.0f}"
              + (f"   [100k THB @0.01 lot: max DD {s['max_dd'] * FX:,.0f} THB]" if p == "2010-19" else ""))
print("accepted:", acc)
