"""Robustness of the 16:00 NY reversal: per year, outliers, delayed entry, both directions,
and the same test at other on-the-hour NY times (control)."""

import numpy as np
import pandas as pd

from common import YEARS, load, s60

PREV_H = (5, 15, 30)
rows = []
for yr in YEARS:
    base, bid, ask, mid = load(yr)
    n = len(mid)
    t_ny = pd.to_datetime((base + np.arange(n)) * 60, unit="s", utc=True).tz_convert(
        "America/New_York")
    hr, mn = t_ny.hour.to_numpy(), t_ny.minute.to_numpy()
    valid = np.isfinite(mid)
    idx = np.maximum.accumulate(np.where(valid, np.arange(n), -1))

    def at(tt, arr=mid):
        j = idx[np.clip(tt - 1, 0, n - 1)]
        ok = (j >= 0) & ((tt - 1 - j) <= 2)
        return np.where(ok, arr[np.maximum(j, 0)], np.nan)

    t = np.flatnonzero((mn == 0) & valid)
    t = t[(t >= 61) & (t < n - 61)]
    for h in PREV_H:
        p_prev = at(t - h)
        p0 = at(t)
        p1, p2 = at(t + 1), at(t + 2)
        ph = at(t + h)
        sp_out = at(t + h, ask) - at(t + h, bid)
        ok = np.isfinite(p_prev) & np.isfinite(p0) & np.isfinite(ph) & np.isfinite(p1) & \
            np.isfinite(p2)
        for k in np.flatnonzero(ok):
            rows.append((yr, h, int(hr[t[k]]), p0[k] - p_prev[k], ph[k] - p0[k], ph[k] - p1[k],
                         ph[k] - p2[k], sp_out[k], mid[idx[t[k] - 1]]))
    print(yr, flush=True)
df = pd.DataFrame(rows, columns=["yr", "h", "hr", "prev", "nxt", "nxt_d1", "nxt_d2", "sp_out",
                                 "price"])
df["owner"] = 0.168 / 4083.276 * df["price"]

for h in PREV_H:
    d = df[df.h == h]
    print(f"\n===== prev {h} min into the hour, fade for the next {h} min =====")
    # control: every NY on-the-hour start, strong moves (threshold per hour from 2010-2016)
    print(" NY hour | n(2017-22) | E 2010-16 | E 2017-22 | t 2017-22 | win% | E delay1 | owner")
    for hh in range(24):
        x = d[d.hr == hh]
        if len(x) < 500:
            continue
        thr = np.quantile(np.abs(x[x.yr <= 2016].prev), 0.8)
        s = x[np.abs(x.prev) >= thr]
        a, b = s[s.yr <= 2016], s[s.yr >= 2017]
        oa = -np.sign(a.prev) * a.nxt  # fade profit
        ob = -np.sign(b.prev) * b.nxt
        od = -np.sign(b.prev) * b.nxt_d1
        tt = ob.mean() / (ob.std() / np.sqrt(len(ob)))
        flag = " <==" if hh == 16 else ""
        print(f"  {hh:02d}:00 | {len(b):4d} | {oa.mean():+.3f} | {ob.mean():+.3f} | {tt:+.1f} | "
              f"{(ob > 0).mean() * 100:.0f} | {od.mean():+.3f} | {b.owner.median():.3f}{flag}")
    x = d[d.hr == 16]
    thr = np.quantile(np.abs(x[x.yr <= 2016].prev), 0.8)
    s = x[np.abs(x.prev) >= thr].copy()
    s["fade"] = -np.sign(s.prev) * s.nxt
    s["fade_d1"] = -np.sign(s.prev) * s.nxt_d1
    s["fade_d2"] = -np.sign(s.prev) * s.nxt_d2
    print(f" 16:00 detail (threshold ${thr:.2f}):")
    for y in YEARS:
        z = s[s.yr == y]
        print(f"   {y}: n {len(z):3d} fade mean {z.fade.mean():+.3f} median {z.fade.median():+.3f}"
              f" win {(z.fade > 0).mean() * 100:.0f}% | delay1 {z.fade_d1.mean():+.3f} "
              f"delay2 {z.fade_d2.mean():+.3f}")
    b = s[s.yr >= 2017]
    lo, hi = b.fade.quantile([0.01, 0.99])
    tr = b.fade[(b.fade >= lo) & (b.fade <= hi)]
    print(f"   2017-22 trimmed 1% mean {tr.mean():+.3f}; up-moves faded {b[b.prev > 0].fade.mean():+.3f} "
          f"(n {int((b.prev > 0).sum())}), down-moves faded {b[b.prev < 0].fade.mean():+.3f} "
          f"(n {int((b.prev < 0).sum())}); exit spread median {b.sp_out.median():.3f}")
