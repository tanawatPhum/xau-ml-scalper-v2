"""Post-hoc: how many trades of the accepted k 1 rule (V2) coincide with the k 1.5 base (V0)?
Same side and entry within 10 minutes counts as the same trade. 2010-2019 only."""
import numpy as np

import variants as V  # runs the variant study once (prints its report)

out = {}
for yr in V.RUN_YEARS:
    y, mins, blk = V.data[yr]
    s60 = V.sigma60(y, blk)
    sl = V.sigma_long(y, blk)
    seff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    for name, T, S in (("k1V2", 1.0 * seff, 1.0 * seff), ("k15V0", 1.5 * s60, 1.5 * s60)):
        idx, d, ext, exi, th = V.zigzag_x(y, blk, T)
        eb = blk[idx]
        same_prev = np.r_[False, eb[1:] == eb[:-1]]
        B = np.full(len(idx), np.nan)
        B[1:] = d[1:] * (ext[:-1] - ext[1:])
        sel = same_prev & (B / th >= 2.5)
        out.setdefault(name, []).append((mins[idx[sel]].astype(np.int64), -d[sel]))
a_t = np.concatenate([p[0] for p in out["k1V2"]])
a_s = np.concatenate([p[1] for p in out["k1V2"]])
b_t = np.concatenate([p[0] for p in out["k15V0"]])
b_s = np.concatenate([p[1] for p in out["k15V0"]])
o = np.argsort(b_t)
b_t, b_s = b_t[o], b_s[o]
match = 0
for t, s in zip(a_t, a_s, strict=True):
    lo, hi = np.searchsorted(b_t, t - 10), np.searchsorted(b_t, t + 10, side="right")
    match += bool(np.any(b_s[lo:hi] == s))
print(f"\nOVERLAP: k1 V2 signals {len(a_t)}, k1.5 V0 signals {len(b_t)}, k1 V2 signals that coincide with a "
      f"k1.5 V0 signal (same side, within 10 min): {match} ({100 * match / len(a_t):.0f}%)")
