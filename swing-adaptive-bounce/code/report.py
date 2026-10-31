"""Pre-registered verdict for the adaptive bounce scan (discovery 2010-16, validation 2017-19)."""

import json

import numpy as np

from adaptive import BIN_NAMES, CACHE, DISC, KS, OUT, VAL

DAYS = {int(k): v for k, v in json.load(open(OUT / "TRADING_DAYS.json")).items()}
META = json.load(open(OUT / "RUN_META.json"))
COST = 0.168
CELLS = ["all"] + list(BIN_NAMES)
N_VAL_DAYS = sum(DAYS[y] for y in VAL)
N_DISC_DAYS = sum(DAYS[y] for y in DISC)


def load(tag, k, key):
    return dict(np.load(CACHE / f"{tag}_k{k:g}_{key}.private.npz"))


def mask(z, cell, years):
    m = np.isin(z["yr"], list(years))
    if cell != "all":
        m &= z["bin"] == BIN_NAMES.index(cell)
    return m


def ct(x, day):
    if len(x) < 3:
        return 0.0, 0.0
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se) if se > 0 else 0.0


def evaluate(z0, cell, flip=None):
    out = {}
    m = mask(z0, cell, DISC)
    g, day = z0["net"][m].astype(np.float64) + COST, z0["day"][m]
    if flip is not None:
        g = g * flip(day)
    mu, t = ct(g, day)
    side = "fade" if mu > 0 else "follow"
    sg = 1.0 if side == "fade" else -1.0
    out.update(side=side, disc_gross=sg * mu, disc_t=sg * t, disc_net=sg * mu - COST, disc_n=int(m.sum()))
    m = mask(z0, cell, VAL)
    g, day, yr = z0["net"][m].astype(np.float64) + COST, z0["day"][m], z0["yr"][m]
    if flip is not None:
        g = g * flip(day)
    mu, t = ct(g, day)
    ynet = {int(y): float(sg * g[yr == y].mean() - COST) if (yr == y).any() else None for y in VAL}
    out.update(val_gross=sg * mu, val_t=sg * t, val_net=sg * mu - COST, val_n=int(m.sum()),
               val_ynet=ynet, val_years_pos=int(sum(v is not None and v > 0 for v in ynet.values())),
               val_trades_per_day=float(m.sum() / N_VAL_DAYS))
    out["r1"] = bool(abs(out["disc_t"]) >= 3 and out["disc_net"] > 0)
    out["r2"] = bool(out["val_t"] >= 2 and out["val_net"] > 0 and out["val_years_pos"] >= 2)
    out["r4"] = bool(out["val_trades_per_day"] >= 1)
    return out


def side_net(z, cell):
    res = {}
    for per, yrs in (("disc", DISC), ("val", VAL)):
        m = mask(z, cell, yrs)
        res[per] = float(z["net"][m].mean()) if m.any() else None
    return res


rep = {"k": {}, "fixed": {}, "null_price": META["null"]}
for k in KS:
    z0 = load("AD", k, "fade_d1_s0")
    md = mask(z0, "all", DISC)
    th = z0["th_usd"][md]
    rk = {"theta_usd_p10_p50_p90": [float(v) for v in np.quantile(th, [0.1, 0.5, 0.9])],
          "trades_per_day_disc": float(md.sum() / N_DISC_DAYS), "cells": {}}
    for cell in CELLS:
        e = evaluate(z0, cell)
        side = e["side"]
        s3 = side_net(load("AD", k, f"{side}_d1_s3"), cell)
        e["stop3"] = s3
        e["r3"] = bool(s3["disc"] is not None and s3["val"] is not None and s3["disc"] > 0 and s3["val"] > 0)
        e["stop2"] = side_net(load("AD", k, f"{side}_d1_s2"), cell)
        e["delay2"] = side_net(load("AD", k, f"{side}_d2_s0"), cell)
        e["PASS"] = bool(e["r1"] and e["r2"] and e["r3"] and e["r4"])
        if e["PASS"]:
            for nm, key in (("no_stop", f"{side}_d1_s0"), ("stop3", f"{side}_d1_s3")):
                z = load("AD", k, key)
                m = mask(z, cell, VAL)
                x = z["net"][m].astype(np.float64)
                w = x > 0
                e[f"risk_{nm}_val"] = dict(win=float(w.mean()), avg_win=float(x[w].mean()),
                                           avg_loss=float(x[~w].mean()), p1=float(np.quantile(x, 0.01)),
                                           worst=float(x.min()))
        rk["cells"][cell] = e
    rep["k"][str(k)] = rk
    zf = load("FX", k, "fade_d1_s0")
    ef = evaluate(zf, "all")
    ef["theta_usd"] = META["fixed_theta_bps"][str(k)] * 0.4083276
    rep["fixed"][str(k)] = ef

# day-level sign-flip null of trade P&L: false passes of rules 1, 2, 4 over all 28 cells
rng = np.random.default_rng(7)
caches = {k: load("AD", k, "fade_d1_s0") for k in KS}
all_days = np.unique(np.concatenate([z["day"] for z in caches.values()]))
fp = []
for draw in range(20):
    sgn = rng.choice([-1.0, 1.0], len(all_days))

    def flip(day, sgn=sgn):
        return sgn[np.searchsorted(all_days, day)]

    c = 0
    for k in KS:
        for cell in CELLS:
            e = evaluate(caches[k], cell, flip)
            c += e["r1"] and e["r2"] and e["r4"]
    fp.append(int(c))
rep["null_dayflip_false_passes"] = fp
json.dump(rep, open(OUT / "REPORT.json", "w"), indent=1)

print("=== Adaptive bounce = k x sigma60, delay 1, no stop. Cells: side | disc gross (t) net | val gross (t) net "
      "| val years>0 | trades/day | stop3 net disc/val | rules r1 r2 r3 r4 | PASS")
for k in KS:
    rk = rep["k"][str(k)]
    q = rk["theta_usd_p10_p50_p90"]
    print(f"k {k:g}: theta today-$ p10 {q[0]:.2f} p50 {q[1]:.2f} p90 {q[2]:.2f}; trades/day (all, disc) "
          f"{rk['trades_per_day_disc']:.1f}")
    for cell, e in rk["cells"].items():
        s3 = e["stop3"]
        print(f"   {cell:5s} {e['side']:6s} | {e['disc_gross']:+.3f} ({e['disc_t']:+.1f}) {e['disc_net']:+.3f} | "
              f"{e['val_gross']:+.3f} ({e['val_t']:+.1f}) {e['val_net']:+.3f} | {e['val_years_pos']}/3 | "
              f"{e['val_trades_per_day']:.2f} | {s3['disc']:+.3f}/{s3['val']:+.3f} | "
              f"{int(e['r1'])}{int(e['r2'])}{int(e['r3'])}{int(e['r4'])} | {e['PASS']}")
print("\n=== Sensitivity for the chosen side (net disc / val): stop 2 theta | delay 2 no stop")
for k in KS:
    for cell, e in rep["k"][str(k)]["cells"].items():
        s2, d2 = e["stop2"], e["delay2"]
        print(f"  k {k:g} {cell:5s} {e['side']:6s} stop2 {s2['disc']:+.3f}/{s2['val']:+.3f} | delay2 "
              f"{d2['disc']:+.3f}/{d2['val']:+.3f}")
print("\n=== Fixed-$ comparison (theta fixed at the discovery median, all cells): side | disc net (t gross) | val net (t)")
for k in KS:
    f, a = rep["fixed"][str(k)], rep["k"][str(k)]["cells"]["all"]
    print(f"  k {k:g} fixed ${f['theta_usd']:.2f}: {f['side']:6s} {f['disc_net']:+.3f} ({f['disc_t']:+.1f}) | "
          f"{f['val_net']:+.3f} ({f['val_t']:+.1f})   vs adaptive {a['side']:6s} {a['disc_net']:+.3f} "
          f"({a['disc_t']:+.1f}) | {a['val_net']:+.3f} ({a['val_t']:+.1f})")
print("\n=== Checks")
for key, v in META["null"].items():
    print(f"  sign-flip price null {key}: gross {v['gross_usd']:+.4f} (t {v['t_simple']:+.2f}) n {v['n']}")
print(f"  day-flip null false passes (rules 1,2,4; 28 cells) over 20 draws: {fp}")
for k in KS:
    for cell, e in rep["k"][str(k)]["cells"].items():
        if e["PASS"]:
            print(f"  PASS k {k:g} {cell}: risk no stop {e['risk_no_stop_val']} | stop3 {e['risk_stop3_val']}")
