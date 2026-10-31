"""Smoke test on one discovery year (2012): sigma60 scale, events per day, synthetic-walk P&L ~ 0."""
import numpy as np

from adaptive import U, events, load_series, sigma60, trades

y, mins, blk = load_series(2012)
sig = sigma60(y, blk)
print("sigma60 today-$ p10/p50/p90:", np.round(np.nanquantile(sig, [0.1, 0.5, 0.9]) * U, 2),
      "nan share", round(float(np.isnan(sig).mean()), 3))
ndays = len(np.unique((mins * 60 + 3 * 3600) // 86400))
for k in (0.5, 1.0, 2.0):
    ev = events(y, blk, k * sig)
    r = trades(ev, y, mins, blk, 1, 0.0, "fade")
    print(f"k {k}: events/day {len(ev['idx']) / ndays:.1f}, theta$ p50 {np.median(r['th_usd']):.2f}, "
          f"bins {np.bincount(r['bin'], minlength=3) / len(r['bin'])}, fade net mean {r['net'].mean():+.3f}")
# synthetic Gaussian walk with the same blocks and realized scale: P&L must be ~ 0 gross
rng = np.random.default_rng(1)
ys = np.cumsum(rng.normal(0, np.nanmedian(sig) / np.sqrt(60), len(y)))
sigs = sigma60(ys, blk)
for k in (0.5, 1.0, 2.0):
    ev = events(ys, blk, k * sigs)
    r = trades(ev, ys, mins, blk, 1, 0.0, "fade")
    g = r["net"].astype(float) + 0.168
    print(f"synthetic k {k}: n {len(g)}, gross {g.mean():+.4f} (t {g.mean() / (g.std() / np.sqrt(len(g))):+.2f}), "
          f"bins {np.round(np.bincount(r['bin'], minlength=3) / len(r['bin']), 3)}")
