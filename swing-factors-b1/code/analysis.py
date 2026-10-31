"""Batch-1 factor tests (pre-registered in ../PLAN.md): disc 2010-16, val 2017-19."""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE, OUT = ROOT / "cache", ROOT / "out"
OUT.mkdir(exist_ok=True)
KS = (1.0, 1.5)
TERC = ("legsize", "legtime", "bouncetime", "volratio", "rangepos")
FACTORS = TERC + ("session", "htf", "structure")
GROUP_NAMES = {f: ("low", "mid", "high") for f in TERC}
GROUP_NAMES["session"] = ("Asia 00-07", "London 07-13", "NY 13-21", "late 21-24")
GROUP_NAMES["htf"] = ("against k3", "with k3")
GROUP_NAMES["structure"] = ("TREND", "CONTRACT", "COUNTER", "EXPAND")


def groups(z, f, cuts):
    if f in TERC:
        x = z[f]
        g = np.where(np.isnan(x), -1, np.digitize(x, cuts))
    elif f == "session":
        h = z["hour"].astype(int)
        g = np.select([h < 7, h < 13, h < 21], [0, 1, 2], 3)
    elif f == "htf":
        g = z["htf"].astype(int)
    else:
        g = z["structure"].astype(int)
    return g


def gstat(x, day, g, ng):
    out = []
    for i in range(ng):
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


def test(z, g, outcome, ng, disc, val):
    x = z["net"] if outcome == "O1" else z["ext"]
    sd = gstat(x[disc], z["day"][disc], g[disc], ng)
    sv = gstat(x[val], z["day"][val], g[val], ng)
    means = np.array([s[1] for s in sd])
    if np.all(np.isnan(means)):
        return dict(matters=False)
    b, w = int(np.nanargmax(means)), int(np.nanargmin(means))
    td = (sd[b][1] - sd[w][1]) / np.hypot(sd[b][2], sd[w][2])
    tv = (sv[b][1] - sv[w][1]) / np.hypot(sv[b][2], sv[w][2]) if not np.isnan(sv[b][1] + sv[w][1]) else np.nan
    return dict(best=b, worst=w, t_disc=float(td), t_val=float(tv),
                matters=bool(abs(td) >= 3 and tv == tv and tv >= 2), disc=sd, val=sv)


rep = {}
rng = np.random.default_rng(31)
false_passes = []
for k in KS:
    z = dict(np.load(CACHE / f"ROWS_k{k:g}.private.npz"))
    disc, val = z["yr"] <= 2016, (z["yr"] >= 2017) & (z["yr"] <= 2019)
    cuts = {f: np.nanquantile(z[f][disc], [1 / 3, 2 / 3]) for f in TERC}
    rk = {"cuts": {f: [float(c) for c in v] for f, v in cuts.items()}, "factors": {}}
    G = {f: groups(z, f, cuts.get(f)) for f in FACTORS}
    for f in FACTORS:
        ng = len(GROUP_NAMES[f])
        res = {o: test(z, G[f], o, ng, disc, val) for o in ("O1", "O2")}
        # per-group table: n, O1, O1+O2, stop rate
        tab = []
        for i in range(ng):
            row = {"group": GROUP_NAMES[f][i]}
            for per, m in (("disc", disc), ("val", val)):
                mm = m & (G[f] == i)
                row[per] = dict(n=int(mm.sum()), O1=float(z["net"][mm].mean()) if mm.any() else None,
                                O1O2=float((z["net"][mm] + z["ext"][mm]).mean()) if mm.any() else None,
                                stop=float(z["stop"][mm].mean()) if mm.any() else None)
            tab.append(row)
        rk["factors"][f] = dict(tests=res, table=tab)
    rep[f"k{k:g}"] = rk
    # shuffle null: permute labels within year
    for draw in range(20):
        c = 0
        for f in FACTORS:
            g = G[f].copy()
            for yr in np.unique(z["yr"]):
                m = np.flatnonzero(z["yr"] == yr)
                g[m] = rng.permutation(g[m])
            ng = len(GROUP_NAMES[f])
            c += sum(test(z, g, o, ng, disc, val)["matters"] for o in ("O1", "O2"))
        if len(false_passes) <= draw:
            false_passes.append(0)
        false_passes[draw] += c
rep["null_false_passes_per_draw"] = false_passes
json.dump(rep, open(OUT / "REPORT.json", "w"), indent=1, default=float)

for kk, rk in rep.items():
    if not kk.startswith("k"):
        continue
    print(f"\n######## base {kk} (large leg, fade, stop 3 theta). Cut points (2010-16): "
          + "; ".join(f"{f} {np.round(v, 2).tolist()}" for f, v in rk["cuts"].items()))
    for f, r in rk["factors"].items():
        tl = []
        for o in ("O1", "O2"):
            t = r["tests"][o]
            if "best" in t:
                tl.append(f"{o}: best {GROUP_NAMES[f][t['best']]} vs worst {GROUP_NAMES[f][t['worst']]} "
                          f"t disc {t['t_disc']:+.1f} val {t['t_val']:+.1f} -> {'MATTERS' if t['matters'] else 'no'}")
        print(f"  [{f}] " + " | ".join(tl))
        for row in r["table"]:
            d, v = row["disc"], row["val"]
            fmt = lambda s: (f"n {s['n']:5d} O1 {s['O1']:+.3f} O1+O2 {s['O1O2']:+.3f} stop {100 * s['stop']:4.1f}%"  # noqa: E731
                             if s["n"] else "n 0")
            print(f"      {row['group']:13s} disc {fmt(d)} | val {fmt(v)}")
print(f"\nshuffle null: false 'matters' over 32 tests per draw: {false_passes}")
