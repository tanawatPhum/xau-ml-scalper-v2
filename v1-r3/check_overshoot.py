"""Sanity check of the overshoot audit (descriptive, 2010-16): distribution of O/theta by prior-leg bin, excluding stream resets."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v1_r3 as v  # noqa: E402

l2 = v.lock2_info()
c = v.context(list(range(2010, 2017)), "design", "2016-12-31")
for r in ("A", "B"):
    ev, aux = v.build_rule3(c, l2["base"]["rules"][r], l2["ov"].get(r, {}))
    idx = ev[:, 0].astype(np.int64)
    nxt_piv = np.r_[aux["piv"][1:], -1]
    nxt_ppiv = np.r_[aux["ppiv"][1:], -1]
    same_stream = nxt_ppiv == aux["piv"]  # next event's previous pivot is this event's extreme
    ok = np.isfinite(aux["leg"]) & (aux["ppiv"] >= 0) & same_stream
    O = np.full(len(ev), np.nan)
    O[ok] = ev[ok, 1] * (c["y"][nxt_piv[ok]] - c["y"][idx[ok]]) / ev[ok, 2]
    for lo, hi in ((0, 1.5), (1.5, 2.5), (2.5, 3.5), (3.5, 5), (5, np.inf)):
        sel = ok & (aux["leg"] >= lo) & (aux["leg"] < hi)
        o = O[sel]
        print(r, f"leg {lo}-{hi}", "n", sel.sum(), "mean", round(float(np.mean(o)), 3), "median", round(float(np.median(o)), 3),
              "P(O<1)", round(float(np.mean(o < 1)), 3), "P(O<=0.01)", round(float(np.mean(o <= .01)), 3),
              "min", round(float(o.min()), 3), "share_reset_excluded", round(1 - sel.sum() / max(1, ((aux['leg'] >= lo) & (aux['leg'] < hi) & (aux['ppiv'] >= 0)).sum()), 3))
