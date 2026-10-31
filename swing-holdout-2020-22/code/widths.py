"""Dollar width per trade (bounce theta, stop 3 theta, required leg 2.5 theta, realised win/loss),
rules A and B, 2020-2022: at the gold price of the time and converted to today's price 4083."""
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
P_NOW = 4083.276
for r, (k, kind) in ex.RULES.items():
    th_b, px, win_b, loss_b, legb = [], [], [], [], []
    for yr in (2020, 2021, 2022):
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
        out_i, _ = ex.apply_stop(y, ent[ok], ex_[ok], sgn, 3.0 * th[ok])
        g = sgn * (y[out_i] - y[ent[ok]])  # bps
        th_b.append(th[ok])
        legb.append(B[ok])
        px.append(np.exp(y[ent[ok]] / 1e4))
        win_b.append(g[g > 0])
        loss_b.append(g[g <= 0])
    th_b, px, legb = np.concatenate(th_b), np.concatenate(px), np.concatenate(legb)
    wb, lb = np.concatenate(win_b), np.concatenate(loss_b)
    q = lambda a: " / ".join(f"{v:,.2f}" for v in np.quantile(a, [0.1, 0.5, 0.9]))  # noqa: E731
    th_then, th_now = th_b * px / 1e4, th_b * P_NOW / 1e4
    print(f"\nRULE {r} 2020-22 (p10 / median / p90), gold then avg {px.mean():,.0f}")
    print(f"  bounce theta  bps: {q(th_b)} | $ then: {q(th_then)} | $ at 4083: {q(th_now)}")
    print(f"  stop 3 theta  $ then: {q(3 * th_then)} | $ at 4083: {q(3 * th_now)}")
    print(f"  leg before    $ then: {q(legb * px / 1e4)} | $ at 4083: {q(legb * P_NOW / 1e4)}")
    print(f"  realised gross win avg: {wb.mean():.1f} bps = $ {wb.mean() * px.mean() / 1e4:.2f} then / $ {wb.mean() * P_NOW / 1e4:.2f} at 4083; "
          f"loss avg {lb.mean():.1f} bps = $ {lb.mean() * px.mean() / 1e4:.2f} then / $ {lb.mean() * P_NOW / 1e4:.2f} at 4083")
