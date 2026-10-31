"""Per-year view of the two accepted rules (rule A = k 1 V2, rule B = k 1.5 V0), 2010-2019, per oz."""
import json

import numpy as np

import variants as V  # rebuilds the variant rows (prints the variant report first)

res = {}
print("\n=== PER YEAR (today's $ per oz, after cost, entry/exit 1 minute late)")
for name, key in (("A k1 V2", (1.0, "V2")), ("B k1.5 V0", (1.5, "V0"))):
    z = V.rows[key]
    print(name)
    res[name] = {}
    tot = 0.0
    for yr in V.RUN_YEARS:
        m = z["yr"] == yr
        x = z["net"][m]
        o = np.argsort(z["t"][m], kind="stable")
        eq = np.cumsum(x[o])
        dd = float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max())
        tot += x.sum()
        r = dict(n=int(m.sum()), per_day=float(m.sum() / V.DAYS[yr]), net=float(x.mean()), total=float(x.sum()),
                 win=float((x > 0).mean()), worst=float(x.min()), max_dd=dd, cum=float(tot))
        res[name][yr] = r
        print(f"  {yr}: trades {r['n']:4d} ({r['per_day']:.1f}/day) net/trade {r['net']:+.3f} year total {r['total']:+7.1f} "
              f"win {100 * r['win']:.0f}% worst {r['worst']:+.1f} maxDD {r['max_dd']:.0f} cumulative {r['cum']:+.0f}")
json.dump(res, open(V.OUT / "YEARLY.json", "w"), indent=1)
