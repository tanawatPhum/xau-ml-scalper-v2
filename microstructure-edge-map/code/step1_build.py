"""Step 1 data: clock-aligned block boundaries per horizon with r_prev / r_next (mid), S60,
NY hour, spread and mid at t. Price at boundary t = mid close of the last traded minute < t
(within 2 minutes)."""

import numpy as np

from common import CACHE, YEARS, load, ny_time, s60

H = (1, 5, 15, 30, 60)


def ffill_idx(valid):
    idx = np.where(valid, np.arange(len(valid)), -1)
    return np.maximum.accumulate(idx)


for h in H:
    parts = []
    for yr in YEARS:
        base, bid, ask, mid = load(yr)
        n = len(mid)
        hr, _, _ = ny_time(base, n)
        s = s60(bid)
        valid = np.isfinite(mid)
        ff = ffill_idx(valid)
        ctr = np.r_[0, np.cumsum(valid)]

        def price_at(t):
            j = ff[t - 1]
            ok = (j >= 0) & ((t - 1 - j) <= 2)
            return np.where(ok, mid[np.maximum(j, 0)], np.nan), np.where(ok, np.maximum(j, 0), 0)

        start = (-base) % h
        t = np.arange(start + 2 * h, n - h, h)
        t = t[t >= 61]
        p0, j0 = price_at(t)
        pm, _ = price_at(t - h)
        pp, _ = price_at(t + h)
        cov = (ctr[t + h] - ctr[t - h]) >= 0.9 * 2 * h
        ok = np.isfinite(p0) & np.isfinite(pm) & np.isfinite(pp) & cov & np.isfinite(s[t])
        t, j0 = t[ok], j0[ok]
        parts.append(np.column_stack([
            np.full(len(t), yr), (base + t) // 1440, hr[t], s[t],
            p0[ok] - pm[ok], pp[ok] - p0[ok], (ask - bid)[j0], mid[j0]]))
        print(h, yr, len(t), flush=True)
    A = np.concatenate(parts)
    np.save(CACHE / f"BLOCKS_h{h}.private.npy", A)
    print("h", h, "total", len(A), flush=True)
