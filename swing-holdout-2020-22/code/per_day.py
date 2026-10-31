"""Trades per trading day (Mon-Fri) for rules A, B and A+B, 2010-2022."""
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
H, _ = ex.collect(list(range(2010, 2023)))
days_all = []
for yr in range(2010, 2023):
    y, mins, blk = ex.load_series(yr)
    d = np.unique((mins.astype(np.int64) * 60 + 3 * 3600) // 86400)
    days_all.append(d[((d + 3) % 7) < 5])
days_all = np.concatenate(days_all)
hold = {}
for name, day in (("A", H["A"]["day"]), ("B", H["B"]["day"]), ("A+B", np.r_[H["A"]["day"], H["B"]["day"]])):
    cnt = np.zeros(len(days_all), int)
    u, c = np.unique(day, return_counts=True)
    idx = np.searchsorted(days_all, u)
    ok = (idx < len(days_all)) & (days_all[np.minimum(idx, len(days_all) - 1)] == u)
    cnt[idx[ok]] = c[ok]
    print(f"{name}: mean {cnt.mean():.2f}/day, median {np.median(cnt):.0f}, days with 0 trades {100 * (cnt == 0).mean():.0f}%, "
          f"1-3: {100 * ((cnt >= 1) & (cnt <= 3)).mean():.0f}%, 4-6: {100 * ((cnt >= 4) & (cnt <= 6)).mean():.0f}%, "
          f"7+: {100 * (cnt >= 7).mean():.0f}%, p90 {np.quantile(cnt, 0.9):.0f}, max {cnt.max()}")
for r in ("A", "B"):
    h = (H[r]["t_exit"] - H[r]["t_ent"])
    print(f"hold minutes {r}: median {np.median(h):.0f}, p10 {np.quantile(h, 0.1):.0f}, p90 {np.quantile(h, 0.9):.0f}")
