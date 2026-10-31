"""Check the NY 16h reversal: is it real price action or rollover quote noise?
For boundaries t in NY hour 16: strong-move reversal E measured on mid, BID only and ASK only,
split by the start minute; spreads at entry (t) and at exit (t+h)."""

import numpy as np
import pandas as pd

from common import YEARS, load, ny_time, s60

rows = []
for yr in YEARS:
    base, bid, ask, mid = load(yr)
    n = len(mid)
    hr, _, _ = ny_time(base, n)
    t_ny = pd.to_datetime((base + np.arange(n)) * 60, unit="s", utc=True).tz_convert(
        "America/New_York")
    mnt = t_ny.minute.to_numpy()
    s = s60(bid)
    valid = np.isfinite(mid)
    idx = np.maximum.accumulate(np.where(valid, np.arange(n), -1))
    ctr = np.r_[0, np.cumsum(valid)]
    for h in (5, 15, 30, 60):
        start = (-base) % h
        t = np.arange(start + 2 * h, n - h, h)
        t = t[(t >= 61) & (hr[t] == 16)]

        def at(tt, arr):
            j = idx[tt - 1]
            ok = (j >= 0) & ((tt - 1 - j) <= 2)
            return np.where(ok, arr[np.maximum(j, 0)], np.nan)

        cols = {}
        for nm, arr in (("mid", mid), ("bid", bid), ("ask", ask)):
            cols[nm] = (at(t - h, arr), at(t, arr), at(t + h, arr))
        sp_in = at(t, ask) - at(t, bid)
        sp_out = at(t + h, ask) - at(t + h, bid)
        cov = (ctr[t + h] - ctr[t - h]) >= 0.9 * 2 * h
        ok = cov & np.isfinite(s[t]) & np.all([np.isfinite(c) for v in cols.values() for c in v],
                                              axis=0)
        for k in np.flatnonzero(ok):
            r = dict(yr=yr, h=h, minute=int(mnt[t[k]]), day=int((base + t[k]) // 1440),
                     sp_in=sp_in[k], sp_out=sp_out[k])
            for nm, (a, b, c) in cols.items():
                r[f"prev_{nm}"] = b[k] - a[k]
                r[f"next_{nm}"] = c[k] - b[k]
            rows.append(r)
    print(yr, flush=True)
df = pd.DataFrame(rows)
for h in (5, 15, 30, 60):
    d = df[df.h == h]
    thr = np.quantile(np.abs(d[d.yr <= 2016]["prev_mid"]), 0.8)
    st = d[np.abs(d["prev_mid"]) >= thr]
    print(f"\n=== h {h}: strong threshold ${thr:.3f}")
    for per, m in (("2010-16", st.yr <= 2016), ("2017-22", st.yr >= 2017)):
        x = st[m]
        line = []
        for nm in ("mid", "bid", "ask"):
            o = np.sign(x["prev_mid"]) * x[f"next_{nm}"]
            line.append(f"{nm} {o.mean():+.3f}")
        print(f"  {per} n {len(x):5d} | E " + " ".join(line)
              + f" | spread in {x.sp_in.median():.3f} out {x.sp_out.median():.3f} "
              f"(p90 out {x.sp_out.quantile(0.9):.3f})")
    for mm in sorted(st.minute.unique()):
        x = st[(st.minute == mm) & (st.yr >= 2017)]
        if len(x) < 30:
            continue
        o = np.sign(x["prev_mid"]) * x["next_mid"]
        ob = np.sign(x["prev_mid"]) * x["next_bid"]
        print(f"    start NY 16:{mm:02d} (2017-22) n {len(x):4d} E mid {o.mean():+.3f} "
              f"bid {ob.mean():+.3f} | exit spread median {x.sp_out.median():.3f}")
