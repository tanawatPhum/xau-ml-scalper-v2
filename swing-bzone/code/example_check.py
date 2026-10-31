"""Owner's chart example 2017-01-18 London: what did the strategy see? (descriptive)"""
import numpy as np
import pandas as pd

import bzone as Z  # noqa: F401

yr = 2017
y, mins, blk = Z.load_series(yr)
t0 = int(pd.Timestamp("2017-01-18 09:00", tz="UTC").value // 60e9)
t1 = int(pd.Timestamp("2017-01-18 13:00", tz="UTC").value // 60e9)
s60 = Z.sigma60(y, blk)
sl_ = Z.sigma_long(y, blk)
seff = np.where(np.isfinite(sl_), np.fmax(s60, sl_), s60)
mid = np.exp(y / 1e4)
for rule, (k, kind) in Z.RULES.items():
    T = k * (seff if kind == "eff" else s60)
    idx, d, ext, exi, th = Z.zigzag_x(y, blk, T)
    m = (mins[idx] >= t0) & (mins[idx] < t1)
    i0 = np.searchsorted(mins, t0)
    print(f"rule {rule}: theta at 09:00 UTC = {T[i0]:.1f} bps = ${T[i0] * mid[i0] / 1e4:.2f}; swing confirmations in the session:")
    for j in np.flatnonzero(m):
        B = d[j] * (ext[j - 1] - ext[j]) if j > 0 else np.nan
        print(f"   {pd.Timestamp(int(mins[idx[j]]) * 60e9, tz='UTC'):%H:%M} dir {d[j]:+d} extreme at {pd.Timestamp(int(mins[exi[j]]) * 60e9, tz='UTC'):%H:%M} "
              f"leg B {B:.1f} bps = {B / th[j]:.2f} theta")
D = pd.read_pickle(Z.ROOT / "cache" / "TRADES.private.pkl")
print(D[(D.t_ent >= t0) & (D.t_ent < t1)].to_string())
