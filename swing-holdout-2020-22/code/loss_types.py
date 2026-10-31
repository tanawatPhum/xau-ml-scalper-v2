"""Losing trades of rules A + B by type, 2010-2022, money at the time's price, 0.1 lot, $0.168 spread."""
import contextlib
import importlib.util
import io
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("exam", HERE / "exam.py")
ex = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(ex)
EDGE = HERE.parents[1] / "microstructure-edge-map" / "cache"
rows = []
for r, (k, kind) in ex.RULES.items():
    for yr in range(2010, 2023):
        y, mins, blk = ex.load_series(yr)
        n = len(y)
        s60 = ex.sigma60(y, blk)
        sl = ex.sigma_long(y, blk)
        seff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
        T = k * (seff if kind == "eff" else s60)
        idx, d, ext, exi, th = ex.zigzag_x(y, blk, T)
        eb = blk[idx]
        same_prev = np.r_[False, eb[1:] == eb[:-1]]
        B = np.full(len(idx), np.nan)
        B[1:] = d[1:] * (ext[:-1] - ext[1:])
        last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
        same_next = np.r_[eb[1:] == eb[:-1], False]
        exit_i = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
        ent = np.minimum(idx + 1, n - 1)
        ok = (blk[ent] == eb) & same_prev & (B / th >= 2.5)
        ex_ = np.minimum(exit_i + 1, n - 1)
        ex_ = np.where(blk[ex_] == eb, ex_, exit_i)
        ok &= ex_ > ent
        sgn = -d[ok].astype(np.float64)
        out_i, stopped = ex.apply_stop(y, ent[ok], ex_[ok], sgn, 3.0 * th[ok])
        zp = np.load(EDGE / f"M1_{yr}.private.npz")
        pos = (mins - int(zp["base"])).astype(np.int64)
        mid = (zp["bid"][pos] + zp["ask"][pos]) / 2
        gross = sgn * (mid[out_i] - mid[ent[ok]])
        net_thb = (gross - 0.168) * 10 * 33.77
        kind_ = np.where(stopped == 1, 0, np.where(~same_next[ok], 3, np.where(gross < 0, 1, 2)))
        # MFE before exit: how far the trade went in our favour first (to see near-wins)
        rows.append(np.c_[net_thb, kind_, gross])
a = np.vstack(rows)
net, kd = a[:, 0], a[:, 1].astype(int)
lose = net < 0
names = ["SL hit (ก้นจริง)", "TP-trail exit below entry (เด้งเกิน θ)", "gross >= 0 but spread made it a loss",
         "forced close before daily break"]
tot = -net[lose].sum()
print(f"trades {len(net)}, losers {lose.sum()} ({100 * lose.mean():.0f}%), total loss {tot:,.0f} THB, total win {net[~lose].sum():,.0f}")
for i, nm in enumerate(names):
    m = lose & (kd == i)
    print(f"{nm}: {m.sum()} losers ({100 * m.sum() / lose.sum():.0f}% of losers), loss {-net[m].sum():,.0f} THB "
          f"({100 * -net[m].sum() / tot:.0f}% of all losses), avg {net[m].mean():,.0f} THB")
