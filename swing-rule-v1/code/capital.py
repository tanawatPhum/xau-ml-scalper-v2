"""Illustration for the owner: 100,000 THB, fixed 0.1 lot (10 oz), 2010-2019 (in-sample),
USD/THB 33.77 (27 Oct 2026). Rule A = k 1 V2, rule B = k 1.5 V0, and A + B together."""
import json

import numpy as np

import variants as V  # rebuilds the rows

FX, OZ, START = 33.77, 10, 100_000.0
out = {}
seqs = {"A": V.rows[(1.0, "V2")], "B": V.rows[(1.5, "V0")]}
seqs["A+B"] = {f: np.concatenate([seqs["A"][f], seqs["B"][f]]) for f in ("net", "t", "yr")}
print("\n=== 100,000 THB, 0.1 lot, USD/THB 33.77, 2010-2019 (in-sample)")
for name, z in seqs.items():
    o = np.argsort(z["t"], kind="stable")
    pnl = z["net"][o] * OZ * FX
    t, yr = z["t"][o], z["yr"][o]
    eq = START + np.cumsum(pnl)
    peak = np.maximum.accumulate(np.r_[START, eq])[1:]
    dd = peak - eq
    i = int(np.argmax(dd))
    pk_i = int(np.argmax(eq[: i + 1])) if i > 0 else 0
    mon = (t.astype(np.int64) * 60).astype("datetime64[s]").astype("datetime64[M]")
    um, inv = np.unique(mon, return_inverse=True)
    msum = np.bincount(inv, weights=pnl)
    # longest time under water (days) between a peak and its recovery
    under, longest, start_t = False, 0, 0
    for k in range(len(eq)):
        if eq[k] < peak[k] and not under:
            under, start_t = True, t[k]
        elif eq[k] >= peak[k] and under:
            under = False
            longest = max(longest, (t[k] - start_t) / 1440)
    if under:
        longest = max(longest, (t[-1] - start_t) / 1440)
    r = dict(end=float(eq[-1]), lowest=float(eq.min()), max_dd_thb=float(dd.max()),
             max_dd_pct_of_peak=float(dd.max() / peak[i] * 100),
             max_dd_from=str((t[pk_i] * 60).astype("datetime64[s]").astype("datetime64[D]")),
             max_dd_to=str((t[i] * 60).astype("datetime64[s]").astype("datetime64[D]")),
             longest_underwater_days=float(longest), worst_month=float(msum.min()),
             best_month=float(msum.max()), months_pos=float((msum > 0).mean()), years={})
    eq_start = START
    for y in V.RUN_YEARS:
        m = yr == y
        p = pnl[m]
        e = eq_start + np.cumsum(p)
        pk = np.maximum.accumulate(np.r_[eq_start, e])[1:]
        r["years"][y] = dict(start=eq_start, pnl=float(p.sum()), end=float(e[-1]), dd=float((pk - e).max()),
                             ret_pct=float(p.sum() / START * 100))
        eq_start = float(e[-1])
    out[name] = r
    print(f"\n{name}: end {r['end']:,.0f} THB | lowest equity {r['lowest']:,.0f} | max drawdown {r['max_dd_thb']:,.0f} THB "
          f"({r['max_dd_pct_of_peak']:.1f}% of peak) {r['max_dd_from']} -> {r['max_dd_to']} | longest underwater "
          f"{r['longest_underwater_days']:.0f} days | worst month {r['worst_month']:,.0f} | best month "
          f"{r['best_month']:,.0f} | months > 0 {100 * r['months_pos']:.0f}%")
    for y, s in r["years"].items():
        print(f"   {y}: start {s['start']:,.0f} -> end {s['end']:,.0f} | year P&L {s['pnl']:+,.0f} ({s['ret_pct']:+.0f}% of 100k) "
              f"| max drawdown in year {s['dd']:,.0f}")
json.dump(out, open(V.OUT / "CAPITAL_100K_THB.json", "w"), indent=1)
