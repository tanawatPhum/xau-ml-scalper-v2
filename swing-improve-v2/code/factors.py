"""Part 1: batch-2 factor tests (pre-registered in ../PLAN.md)."""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE, OUT = ROOT / "cache", ROOT / "out"
FACTORS = ("vol_bounce_leg", "vol_bounce_day", "vol_climax", "spread_rel")
NAMES = ("low", "mid", "high")


def gstat(x, day, g):
    out = []
    for i in range(3):
        m = g == i
        if m.sum() < 30:
            out.append((int(m.sum()), np.nan, np.nan))
            continue
        u, inv = np.unique(day[m], return_inverse=True)
        S, N = np.bincount(inv, weights=x[m]), np.bincount(inv)
        mu = S.sum() / N.sum()
        se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
        out.append((int(m.sum()), float(mu), float(se)))
    return out


def test(z, g, outcome, disc, val):
    x = z["net"] if outcome == "O1" else z["ext"]
    sd, sv = gstat(x[disc], z["day"][disc], g[disc]), gstat(x[val], z["day"][val], g[val])
    means = np.array([s[1] for s in sd])
    b, w = int(np.nanargmax(means)), int(np.nanargmin(means))
    td = (sd[b][1] - sd[w][1]) / np.hypot(sd[b][2], sd[w][2])
    tv = (sv[b][1] - sv[w][1]) / np.hypot(sv[b][2], sv[w][2])
    return dict(best=b, worst=w, t_disc=float(td), t_val=float(tv), matters=bool(abs(td) >= 3 and tv >= 2))


rep, rng, fp = {}, np.random.default_rng(32), [0] * 20
for rule in ("A", "B"):
    z = dict(np.load(CACHE / f"ROWS_{rule}.private.npz"))
    disc, val = z["yr"] <= 2016, z["yr"] >= 2017
    rr = {}
    for f in FACTORS:
        cuts = np.nanquantile(z[f][disc], [1 / 3, 2 / 3])
        g = np.where(np.isfinite(z[f]), np.digitize(z[f], cuts), -1)
        res = {o: test(z, g, o, disc, val) for o in ("O1", "O2")}
        tab = []
        for i in range(3):
            row = {"group": NAMES[i]}
            for per, m in (("disc", disc), ("val", val)):
                mm = m & (g == i)
                row[per] = dict(n=int(mm.sum()), O1=float(z["net"][mm].mean()), O1O2=float((z["net"][mm] + z["ext"][mm]).mean()),
                                stop=float(z["stop"][mm].mean()))
            tab.append(row)
        rr[f] = dict(cuts=[float(c) for c in cuts], tests=res, table=tab)
        for draw in range(20):
            gs = g.copy()
            for yr in np.unique(z["yr"]):
                ii = np.flatnonzero(z["yr"] == yr)
                gs[ii] = rng.permutation(gs[ii])
            fp[draw] += sum(test(z, gs, o, disc, val)["matters"] for o in ("O1", "O2"))
    rep[rule] = rr
rep["null_false_passes_per_draw"] = fp
json.dump(rep, open(OUT / "FACTORS.json", "w"), indent=1)
for rule in ("A", "B"):
    print(f"\n######## rule {rule}")
    for f, r in rep[rule].items():
        tl = " | ".join(f"{o}: best {NAMES[t['best']]} vs worst {NAMES[t['worst']]} t {t['t_disc']:+.1f}/{t['t_val']:+.1f}"
                        f" -> {'MATTERS' if t['matters'] else 'no'}" for o, t in r["tests"].items())
        print(f"  [{f}] cuts {np.round(r['cuts'], 3).tolist()} :: {tl}")
        for row in r["table"]:
            d, v = row["disc"], row["val"]
            print(f"      {row['group']:5s} disc n {d['n']:4d} O1 {d['O1']:+.3f} O1+O2 {d['O1O2']:+.3f} stop {100 * d['stop']:4.1f}% | "
                  f"val n {v['n']:4d} O1 {v['O1']:+.3f} O1+O2 {v['O1O2']:+.3f} stop {100 * v['stop']:4.1f}%")
print(f"\nshuffle null false passes (16 tests) per draw: {fp}")
