"""2011-16 only: ratio grid, bar-permutation null, factor scan, automatic LOCK (see ../PLAN.md v2)."""
import json

import numpy as np
import pandas as pd

from common import FX, OZ, ROOT, add_factors, ct, load_sessions, permute, trades

YRS = list(range(2011, 2017))
S = load_sessions(YRS)
M = S["meta"]
print("sessions", len(M), "spans", M["span"].value_counts().to_dict(), "by session", M["session"].value_counts().to_dict(), flush=True)
NDAYS = int(((M["lock"] + 180) // 1440).nunique())
sel = np.ones(len(M), bool)
GRID = [(rho, m, r, q, s) for rho in (0.5, 1.0) for m in (1.5, 2.5, 4.0) for r in (0.236, 0.382, 0.5, 0.618)
        for q in (0.25, 0.0, -0.25, -0.5) for s in (0.0, 0.25) if q < r]


def stats(D):
    if len(D) == 0:
        return dict(n=0, net=0.0, t=0.0)
    mu, se = ct(D["net"], D["day"])
    return dict(n=int(len(D)), net=mu, t=mu / se if se > 0 else 0.0, gross=float(D["gross"].mean()), win=float((D["oc"] == 1).mean()),
                loss=float((D["oc"] == -1).mean()), none=float((D["oc"] == 0).mean()), p0=float(D["p0"].mean()),
                per_day=len(D) / NDAYS, thb=float(D["net"].sum() * OZ * FX))


def run_grid(H=None, L=None, C=None, U=None):
    rows = []
    for g in GRID:
        D = trades(S, sel, *g, H=H, L=L, C=C, U=U)
        rows.append(dict(zip(("rho", "m", "r", "q", "s"), g), **stats(D)))
    return pd.DataFrame(rows)


G = run_grid()
G.to_csv(ROOT / "out" / "GRID_2011_16.csv", index=False)
elig = G[G["n"] >= 300]
best = elig.loc[elig["t"].idxmax()]
print("cells", len(G), "eligible", len(elig), "| cells with t>=2:", int((elig["t"] >= 2).sum()), "| t<=-2:", int((elig["t"] <= -2).sum()))
print("best cell:", best[["rho", "m", "r", "q", "s", "n", "net", "t", "win", "p0", "per_day"]].to_dict(), flush=True)

null_best = []
for d in range(5):
    H, L, C, U = permute(S, np.random.default_rng(1000 + d))
    Gn = run_grid(H, L, C, U)
    e = Gn[Gn["n"] >= 300]
    null_best.append(float(e["t"].max()))
    print(f"null {d}: best t {e['t'].max():+.2f}, median t {e['t'].median():+.2f}, cells t>=2 {int((e['t'] >= 2).sum())}, "
          f"mean gross over cells {e['gross'].mean():+.3f}", flush=True)
print("real best t", round(float(best["t"]), 2), "null best t", [round(x, 2) for x in null_best])
print("real grid: median t", round(float(elig["t"].median()), 2), "mean gross over cells", round(float(elig["gross"].mean()), 3))

cell = tuple(float(best[c]) for c in ("rho", "m", "r", "q", "s"))
D = add_factors(trades(S, sel, *cell), S)
cuts = {f: [float(np.quantile(D[f], 1 / 3)), float(np.quantile(D[f], 2 / 3))] for f in ("run_u", "speed", "bounce_min")}
for f, (a, b) in cuts.items():
    D[f + "_g"] = np.where(D[f] <= a, 0, np.where(D[f] <= b, 1, 2))
FACT = {"Z": "Z", "run_u": "run_u_g", "speed": "speed_g", "bounce_min": "bounce_min_g", "session": "session"}


def scan(D):
    res = []
    for f, col in FACT.items():
        for g in sorted(D[col].unique()):
            a, b = D[D[col] == g], D[D[col] != g]
            if len(a) < 50 or len(b) < 50:
                continue
            ma, sa = ct(a["net"], a["day"])
            mb, sb = ct(b["net"], b["day"])
            h = [float(a[a["yr"].between(*p)]["net"].mean() - b[b["yr"].between(*p)]["net"].mean()) for p in ((2011, 2013), (2014, 2016))]
            res.append(dict(factor=f, group=str(g), n=len(a), net=ma, rest=mb, t=(ma - mb) / np.hypot(sa, sb), half1=h[0], half2=h[1]))
    if not res:
        return pd.DataFrame(columns=["factor", "group", "n", "net", "rest", "t", "half1", "half2"])
    return pd.DataFrame(res).sort_values("t", ascending=False)


filters, cur = [], D
print("\nfactor scan inside the best cell (2011-16):")
for step in range(2):
    sc = scan(cur)
    print(sc.round(3).to_string(index=False))
    ok = sc[(sc["t"] >= 2) & (sc["half1"] > 0) & (sc["half2"] > 0) & ~sc["factor"].isin([f for f, _ in filters])]
    if not len(ok):
        break
    f, g = ok.iloc[0]["factor"], ok.iloc[0]["group"]
    filters.append((f, g))
    col = FACT[f]
    cur = cur[cur[col].astype(str) == g]
    print(f"-> keep filter {f} = {g}: n {len(cur)}\n")


def yearly(X):
    out = {}
    for yr, x in X.groupby("yr"):
        thb = x.sort_values("t_exit")["net"].to_numpy() * OZ * FX
        eq = np.cumsum(thb)
        out[int(yr)] = dict(n=len(x), win=float((x["oc"] == 1).mean()), thb=float(thb.sum()),
                            dd=float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max()))
    return out


edge = bool(best["t"] >= 2 and best["t"] > max(null_best))
lock = dict(cell=dict(zip(("rho", "m", "r", "q", "s"), cell)), filters=filters, cuts=cuts, edge_found=edge, real_best_t=float(best["t"]),
            null_best_t=null_best, all_2011_16=stats(D), filtered_2011_16=stats(cur), yearly_all=yearly(D), yearly_filtered=yearly(cur))
json.dump(lock, open(ROOT / "out" / "LOCK.json", "w"), indent=1)
D.to_pickle(ROOT / "out" / "TRADES_2011_16.private.pkl")
print("\nLOCK:", json.dumps({k: lock[k] for k in ("cell", "filters", "edge_found", "real_best_t", "null_best_t")}))
print("all trades in cell:", {k: round(v, 3) if isinstance(v, float) else v for k, v in lock["all_2011_16"].items()})
print("after filters:", {k: round(v, 3) if isinstance(v, float) else v for k, v in lock["filtered_2011_16"].items()})
print("yearly (cell / filtered):")
for yr in sorted(lock["yearly_all"]):
    a, b = lock["yearly_all"][yr], lock["yearly_filtered"].get(yr, dict(n=0, win=0, thb=0, dd=0))
    print(f"  {yr}: {a['n']} trades win {100 * a['win']:.0f}% {a['thb']:+,.0f} THB dd {a['dd']:,.0f} | {b['n']} win {100 * b['win']:.0f}% "
          f"{b['thb']:+,.0f} dd {b['dd']:,.0f}")
rm = G[(G["rho"] == cell[0]) & (G["m"] == cell[1]) & (G["s"] == cell[4])]
print("\nratio map at the best rho/m/s: net $/oz (t)")
print(rm.pivot(index="r", columns="q", values="net").round(3).to_string())
print(rm.pivot(index="r", columns="q", values="t").round(1).to_string())
print("\nbest cell per (rho, m):")
print(elig.loc[elig.groupby(["rho", "m"])["t"].idxmax(), ["rho", "m", "r", "q", "s", "n", "net", "t", "win", "p0", "per_day"]].round(3).to_string(index=False))

# descriptive only (not used for the lock): does the zone condition help in any cell?
from common import zone_flag  # noqa: E402

zr = []
for _, c in elig.iterrows():
    X = trades(S, sel, c["rho"], c["m"], c["r"], c["q"], c["s"])
    for tol in (0.5, 0.0):
        z = zone_flag(X, S, tol)
        if z.sum() < 30 or (~z).sum() < 30:
            continue
        ma, sa = ct(X["net"][z], X["day"][z])
        mb, sb = ct(X["net"][~z], X["day"][~z])
        zr.append(dict(tol=tol, share=float(z.mean()), zn=ma, nn=mb, t=(ma - mb) / np.hypot(sa, sb)))
zr = pd.DataFrame(zr)
zr.to_csv(ROOT / "out" / "ZONE_BY_CELL_2011_16.csv", index=False)
for tol, g in zr.groupby("tol"):
    print(f"zone tol {tol}: cells {len(g)}, zone share median {g['share'].median():.2f}, Z net mean {g['zn'].mean():+.3f} vs non-Z "
          f"{g['nn'].mean():+.3f}; cells Z better {int((g['t'] > 0).sum())}, Z better t>=2 {int((g['t'] >= 2).sum())}, Z worse t<=-2 "
          f"{int((g['t'] <= -2).sum())}")
