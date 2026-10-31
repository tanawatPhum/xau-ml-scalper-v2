"""Run the adaptive bounce scan on 2010-2019 only (holdout 2020-2022 is not computed here), plus the
fixed-$ comparison and the sign-flip price null."""

import json

import numpy as np

from adaptive import (CACHE, DELAYS, DISC, KS, OUT, SIDES, STOPS, YEARS, events, load_series, sigma60,
                      signflip, trades)

CACHE.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
F = ("net", "bin", "day", "t_ent", "stopped", "th_usd")
RUN_YEARS = [y for y in YEARS if y <= 2019]

data, days = {}, {}
for yr in RUN_YEARS:
    y, mins, blk = load_series(yr)
    sig = sigma60(y, blk)
    data[yr] = (y, mins, blk, sig)
    t = mins.astype(np.int64) * 60 + 3 * 3600
    dd = np.unique(t // 86400)
    days[yr] = int(np.sum(((dd + 3) % 7) < 5))
json.dump(days, open(OUT / "TRADING_DAYS.json", "w"), indent=1)
print("loaded", flush=True)


def save(tag, store):
    for key, v in store.items():
        arrs = {f: np.concatenate([v[yr][f] for yr in RUN_YEARS]) for f in F}
        arrs["yr"] = np.concatenate([np.full(len(v[yr]["net"]), yr, np.int16) for yr in RUN_YEARS])
        np.savez(CACHE / f"{tag}_{key}.private.npz", **arrs)


null_sum = {}
fixed_theta = {}
for k in KS:
    store = {}
    th_disc = []
    for yr in RUN_YEARS:
        y, mins, blk, sig = data[yr]
        ev = events(y, blk, k * sig)
        if yr in DISC:
            th_disc.append(ev["th"][ev["has_b"]])
        for side in SIDES:
            for d in DELAYS:
                for s in STOPS:
                    store.setdefault(f"{side}_d{d}_s{s:g}", {})[yr] = trades(ev, y, mins, blk, d, s, side)
        ys = signflip(y, blk, np.random.default_rng(20261031 + yr))
        evn = events(ys, blk, k * sig)
        for s in (0.0, 3.0):
            r = trades(evn, ys, mins, blk, 1, s, "fade")
            acc = null_sum.setdefault(f"k{k:g}_s{s:g}", [0.0, 0.0, 0])
            g = r["net"].astype(np.float64) + 0.168
            acc[0] += g.sum()
            acc[1] += (g * g).sum()
            acc[2] += len(g)
    save(f"AD_k{k:g}", store)
    fixed_theta[k] = float(np.median(np.concatenate(th_disc)))
    fstore = {}
    for yr in RUN_YEARS:
        y, mins, blk, sig = data[yr]
        th = np.where(np.isnan(sig), np.nan, fixed_theta[k])
        ev = events(y, blk, th)
        for side in SIDES:
            for s in (0.0, 3.0):
                fstore.setdefault(f"{side}_d1_s{s:g}", {})[yr] = trades(ev, y, mins, blk, 1, s, side)
    save(f"FX_k{k:g}", fstore)
    print("k", k, "done; fixed theta bps", round(fixed_theta[k], 3), flush=True)

null_out = {}
for key, (s1, s2, n) in null_sum.items():
    m = s1 / n
    sd = np.sqrt(max(s2 / n - m * m, 0.0))
    null_out[key] = dict(gross_usd=m, t_simple=m / (sd / np.sqrt(n)), n=n)
json.dump(dict(null=null_out, fixed_theta_bps=fixed_theta), open(OUT / "RUN_META.json", "w"), indent=1)
print("saved")
