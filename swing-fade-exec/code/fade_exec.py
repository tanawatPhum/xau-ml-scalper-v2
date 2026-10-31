"""Swing fade with delayed fills and a stop-loss (see ../PLAN.md). Reuses swing-structure code read-only."""

import sys
from pathlib import Path

import numba as nb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-structure" / "code"))
from swing import (COST_BPS, NAMES, USD_PER_BPS, YEARS, load_series, process,  # noqa: E402
                   signflip)

CACHE = ROOT / "cache"
OUT = ROOT / "out"
U = USD_PER_BPS
THETA = {5: 5 / U, 10: 10 / U}
# cell -> (theta in today's $, pattern code or None for every swing)
# A = every patterned swing (codes 0-7), as the swing-structure "ALL" cell; A0 also includes the
# first three swings of each block (no pattern yet). A0 was the first-run A; the planned
# reconciliation check showed it is not the swing-structure cell, so A was corrected (see RESULTS.md).
CELLS = {"A $10 every swing": (10, "patterned"), "A0 $10 every swing incl. unpatterned": (10, None),
         "B $10 COUNTER deep": (10, NAMES.index("COUNTER deep")),
         "C $5 COUNTER deep": (5, NAMES.index("COUNTER deep")),
         "D $5 EXPAND mild": (5, NAMES.index("EXPAND mild"))}
DELAYS = (0, 1, 2)
STOPS = (0.0, 2.0, 1.5)  # 0 = no stop
PRIMARY = (1, 2.0)


@nb.njit(cache=True)
def apply_stop(y, ent, ex, side, stop):
    m = len(ent)
    out_i = ex.copy()
    stopped = np.zeros(m, np.int64)
    if stop <= 0:
        return out_i, stopped
    for k in range(m):
        e = ent[k]
        for t in range(e + 1, ex[k] + 1):
            if side[k] * (y[t] - y[e]) <= -stop:
                out_i[k] = t
                stopped[k] = 1
                break
    return out_i, stopped


def trades(ev, y, mins, blk, theta_bps, delay, k_stop):
    idx = ev["idx"]
    eb = blk[idx]
    n = len(y)
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    nxt = np.r_[idx[1:], -1]
    same = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same, nxt, last_of_blk[eb])
    ent = np.minimum(idx + delay, n - 1)
    ok = blk[ent] == eb
    ex = np.minimum(exit_i + delay, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    side = -ev["dir"].astype(np.float64)
    ent, ex, side, code = ent[ok], ex[ok], side[ok], ev["code"][ok]
    blockend = ~same[ok]
    out_i, stopped = apply_stop(y, ent, ex, side, k_stop * theta_bps)
    gross = side * (y[out_i] - y[ent])
    reason = np.where(stopped == 1, 1, np.where(blockend, 2, 0))
    return dict(net=(gross - COST_BPS) * U, gross=gross * U, code=code, side=side.astype(np.int8),
                reason=reason.astype(np.int8), t_ent=mins[ent], hold=mins[out_i] - mins[ent])
