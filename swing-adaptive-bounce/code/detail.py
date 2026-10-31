"""Descriptive detail for the two passing cells (k 1 and 1.5, large leg), 2010-2019 only.
Not part of the verdict. Also the fixed-$ version of the large-leg cell."""

import json

import numpy as np

from adaptive import BIN_NAMES, CACHE, DISC, OUT, VAL, YEARS, events, load_series, sigma60, trades

COST = 0.168
RUN_YEARS = [y for y in YEARS if y <= 2019]
DAYS = {int(k): v for k, v in json.load(open(OUT / "TRADING_DAYS.json")).items()}
META = json.load(open(OUT / "RUN_META.json"))
LARGE = BIN_NAMES.index("large")
out = {}
data = {yr: load_series(yr) for yr in RUN_YEARS}
for k in (1.0, 1.5):
    rows = {"s0": [], "s3": []}
    for yr in RUN_YEARS:
        y, mins, blk = data[yr]
        sig = sigma60(y, blk)
        ev = events(y, blk, k * sig)
        for key, s in (("s0", 0.0), ("s3", 3.0)):
            r = trades(ev, y, mins, blk, 1, s, "fade")
            m = r["bin"] == LARGE
            rows[key].append({f: v[m] for f, v in r.items()} | {"yr": np.full(m.sum(), yr)})
    z = {key: {f: np.concatenate([p[f] for p in v]) for f in v[0]} for key, v in rows.items()}
    a = z["s3"]
    q = lambda x: [round(float(v), 2) for v in np.quantile(x, [0.1, 0.5, 0.9])]  # noqa: E731
    d = dict(theta_usd=q(a["th_usd"]), leg_B_usd=q(a["b_usd"]), hold_min=q(a["hold"]),
             stop_rate=float(a["stopped"].mean()))
    d["year_net_no_stop"] = {int(yr): round(float(z["s0"]["net"][z["s0"]["yr"] == yr].mean()), 3) for yr in RUN_YEARS}
    d["year_net_stop3"] = {int(yr): round(float(a["net"][a["yr"] == yr].mean()), 3) for yr in RUN_YEARS}
    d["trades_per_day"] = {int(yr): round(float((a["yr"] == yr).sum() / DAYS[yr]), 2) for yr in RUN_YEARS}
    hr = (a["t_ent"].astype(np.int64) % 1440) // 60
    sess = {}
    for nm, lo, hi in (("Asia 00-07", 0, 7), ("London 07-13", 7, 13), ("NY 13-21", 13, 21), ("late 21-24", 21, 24)):
        for per, yrs in (("disc", DISC), ("val", VAL)):
            m = (hr >= lo) & (hr < hi) & np.isin(a["yr"], list(yrs))
            sess[f"{nm} {per}"] = (int(m.sum()), round(float(a["net"][m].mean()), 3) if m.any() else None)
    d["sessions_stop3"] = sess
    for side in ("long after up-bounce? no: fade sells up-bounces",):
        pass
    out[f"k{k:g}"] = d
    # fixed-$ version of the same cell (theta fixed at the discovery median of k x sigma60)
    fx = {}
    for key in ("fade_d1_s0", "fade_d1_s3"):
        zf = dict(np.load(CACHE / f"FX_k{k:g}_{key}.private.npz"))
        for per, yrs in (("disc", DISC), ("val", VAL)):
            m = (zf["bin"] == LARGE) & np.isin(zf["yr"], list(yrs))
            fx[f"{key} {per}"] = (int(m.sum()), round(float(zf["net"][m].mean()), 3))
    out[f"k{k:g}"]["fixed_usd"] = round(META["fixed_theta_bps"][str(k)] * 0.4083276, 2)
    out[f"k{k:g}"]["fixed_large_cell"] = fx
json.dump(out, open(OUT / "DETAIL.json", "w"), indent=1)
for k, d in out.items():
    print(k)
    for key, v in d.items():
        print("  ", key, v)
