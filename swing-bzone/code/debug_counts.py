"""Why is the in-session population small? Count each condition for one year."""
import numpy as np

import bzone as Z  # noqa: F401 (runs the study; reuse its loaded objects)

for yr in (2015, 2018):
    y, mins, blk = Z.load_series(yr)
    n = len(y)
    s60 = Z.sigma60(y, blk)
    sl_ = Z.sigma_long(y, blk)
    seff = np.where(np.isfinite(sl_), np.fmax(s60, sl_), s60)
    idx, d, ext, exi, th = Z.zigzag_x(y, blk, 1.0 * seff)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(len(idx), np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    peak = np.r_[0, exi[:-1]]
    ok = same_prev & (B / th >= 2.5)
    tp, te = mins[peak[ok]].astype(np.int64), mins[np.minimum(idx[ok] + 1, n - 1)].astype(np.int64)
    s = np.searchsorted(Z.LOCK, tp, side="right") - 1
    valid = s >= 0
    in_peak = valid & (tp < Z.END[np.maximum(s, 0)])
    in_both = in_peak & (te < Z.END[np.maximum(s, 0)])
    yrsess = (Z.LOCK >= mins[0]) & (Z.LOCK <= mins[-1])
    print(yr, "rule A ok events", ok.sum(), "| peak inside a session", in_peak.sum(), "| peak+entry same session", in_both.sum(),
          "| sessions this year", yrsess.sum(), "| median leg minutes", np.median((mins[exi] - mins[peak])[ok]),
          "| median peak-to-entry minutes", np.median(te - tp))
