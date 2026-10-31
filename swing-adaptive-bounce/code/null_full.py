"""Full-pipeline price null (added after the first report: the 1-draw price null in run.py showed
gross t up to +3.25 at k 0.5-1, which must be ~0 for any rule on a martingale).
Each draw: per-block random signs on the real 1-minute returns (sizes and timing kept, sigma60
identical to the real one), then the exact study pipeline and the pre-registered pass rule.
Reports the gross fade mean per k x cell over draws and the number of false PASSes per draw."""

import json

import numpy as np

from adaptive import BIN_NAMES, DISC, KS, OUT, VAL, YEARS, events, load_series, sigma60, signflip, trades

COST = 0.168
CELLS = ["all"] + list(BIN_NAMES)
DAYS = {int(k): v for k, v in json.load(open(OUT / "TRADING_DAYS.json")).items()}
N_VAL_DAYS = sum(DAYS[y] for y in VAL)
RUN_YEARS = [y for y in YEARS if y <= 2019]
N_DRAWS = 10


def ct(x, day):
    if len(x) < 3:
        return 0.0, 0.0
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se) if se > 0 else 0.0


def cat(parts):
    return {f: np.concatenate([p[f] for p in parts]) for f in parts[0]}


def mask(z, cell, years):
    m = np.isin(z["yr"], list(years))
    if cell != "all":
        m &= z["bin"] == BIN_NAMES.index(cell)
    return m


def verdict(z0, zs3, cell):
    m = mask(z0, cell, DISC)
    g = z0["net"][m].astype(np.float64) + COST
    mu, t = ct(g, z0["day"][m])
    sg = 1.0 if mu > 0 else -1.0
    r1 = abs(t) >= 3 and sg * mu - COST > 0
    mv = mask(z0, cell, VAL)
    gv = z0["net"][mv].astype(np.float64) + COST
    muv, tv = ct(gv, z0["day"][mv])
    yrs = z0["yr"][mv]
    ypos = sum(1 for y in VAL if (yrs == y).any() and sg * gv[yrs == y].mean() - COST > 0)
    r2 = sg * tv >= 2 and sg * muv - COST > 0 and ypos >= 2
    r4 = mv.sum() / N_VAL_DAYS >= 1
    zz = zs3["fade" if sg > 0 else "follow"]
    r3 = all(zz["net"][mask(zz, cell, yy)].mean() > 0 if mask(zz, cell, yy).any() else False for yy in (DISC, VAL))
    return dict(gross_disc=mu, t_disc=t, gross_val=muv, t_val=tv, PASS=bool(r1 and r2 and r3 and r4),
                r12=bool(r1 and r2))


data = {}
for yr in RUN_YEARS:
    y, mins, blk = load_series(yr)
    data[yr] = (y, mins, blk, sigma60(y, blk))

res = {"draws": []}
for draw in range(N_DRAWS):
    parts = {k: {"f0": [], "fade3": [], "follow3": []} for k in KS}
    for yr in RUN_YEARS:
        y, mins, blk, sig = data[yr]
        ys = signflip(y, blk, np.random.default_rng(900000 + 1000 * draw + yr))
        for k in KS:
            ev = events(ys, blk, k * sig)
            for key, side, s in (("f0", "fade", 0.0), ("fade3", "fade", 3.0), ("follow3", "follow", 3.0)):
                r = trades(ev, ys, mins, blk, 1, s, side)
                parts[k][key].append(dict(net=r["net"], bin=r["bin"], day=r["day"],
                                          yr=np.full(len(r["net"]), yr, np.int16)))
    d = {}
    for k in KS:
        z0 = cat(parts[k]["f0"])
        zs3 = {"fade": cat(parts[k]["fade3"]), "follow": cat(parts[k]["follow3"])}
        for cell in CELLS:
            d[f"k{k:g}_{cell}"] = verdict(z0, zs3, cell)
    res["draws"].append(d)
    npass = sum(v["PASS"] for v in d.values())
    n12 = sum(v["r12"] for v in d.values())
    print(f"draw {draw}: false PASS {npass}, rules 1+2 {n12}; "
          + " ".join(f"{key}:{v['gross_disc']:+.3f}/{v['gross_val']:+.3f}" for key, v in d.items()
                     if key.endswith('_all') or key.endswith('_large')), flush=True)

keys = list(res["draws"][0].keys())
summary = {}
for key in keys:
    gd = np.array([dr[key]["gross_disc"] for dr in res["draws"]])
    gv = np.array([dr[key]["gross_val"] for dr in res["draws"]])
    summary[key] = dict(mean_gross_disc=float(gd.mean()), sd_gross_disc=float(gd.std(ddof=1)),
                        mean_gross_val=float(gv.mean()), sd_gross_val=float(gv.std(ddof=1)),
                        false_pass=int(sum(dr[key]["PASS"] for dr in res["draws"])))
res["summary"] = summary
json.dump(res, open(OUT / "NULL_FULL.json", "w"), indent=1)
print("\nper cell over draws: mean gross disc (sd) | mean gross val (sd) | false PASS count")
for key, v in summary.items():
    print(f"  {key:12s} {v['mean_gross_disc']:+.4f} ({v['sd_gross_disc']:.4f}) | {v['mean_gross_val']:+.4f} "
          f"({v['sd_gross_val']:.4f}) | {v['false_pass']}")
