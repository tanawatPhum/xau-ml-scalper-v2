"""Run all configs on 2010-2022 (real) and the sign-flip null; write per-trade caches."""

import json

import numpy as np

from fade_exec import CACHE, DELAYS, OUT, PRIMARY, STOPS, THETA, YEARS, load_series, process, signflip, trades

CACHE.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
FIELDS = ("net", "gross", "code", "side", "reason", "t_ent", "hold")
days = {}
real = {(tu, d, k): {f: [] for f in FIELDS + ("yr",)} for tu in THETA for d in DELAYS for k in STOPS}
null = {(tu, k): {f: [] for f in FIELDS + ("yr",)} for tu in THETA for k in (0.0, 2.0)}

for yr in YEARS:
    y, mins, blk = load_series(yr)
    t = mins * 60 + 3 * 3600  # trading day = UTC date of time + 3 h
    dd = np.unique(t // 86400)
    days[yr] = int(np.sum(((dd + 3) % 7) < 5))  # Mon-Fri (1970-01-01 was a Thursday)
    for tu, th in THETA.items():
        ev = process(y, mins, blk, th)
        for d in DELAYS:
            for k in STOPS:
                r = trades(ev, y, mins, blk, th, d, k)
                for f in FIELDS:
                    real[(tu, d, k)][f].append(r[f])
                real[(tu, d, k)]["yr"].append(np.full(len(r["net"]), yr, np.int16))
        for draw in range(3):
            ys = signflip(y, blk, np.random.default_rng(20261031 + yr * 10 + draw))
            evn = process(ys, mins, blk, th)
            for k in (0.0, 2.0):
                r = trades(evn, ys, mins, blk, th, PRIMARY[0], k)
                for f in FIELDS:
                    null[(tu, k)][f].append(r[f])
                null[(tu, k)]["yr"].append(np.full(len(r["net"]), yr, np.int16))
    print(yr, "done", flush=True)

for key, v in real.items():
    tu, d, k = key
    np.savez(CACHE / f"T_th{tu}_d{d}_k{k:g}.private.npz", **{f: np.concatenate(a) for f, a in v.items()})
for key, v in null.items():
    tu, k = key
    np.savez(CACHE / f"NULL_th{tu}_d1_k{k:g}.private.npz", **{f: np.concatenate(a) for f, a in v.items()})
json.dump(days, open(OUT / "TRADING_DAYS.json", "w"), indent=1)
print("saved")
