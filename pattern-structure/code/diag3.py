"""Post-hoc look (descriptive, not a test): strong two-segment runs (theta = 1.0 sigma each),
fade the next segment; NY hour 16 excluded; by period and year, gross vs owner cost."""

import numpy as np

from analysis import cluster_t
from patterns import CACHE, OWNER_BPS, states

for L in (5, 10, 20):
    z = np.load(CACHE / f"TRIPLES_L{L}.private.npz")
    keep = z["nyh"] != 16
    st = states(np.stack([z["m1"], z["m2"], z["m3"]], 1),
                np.stack([z["sig1"], z["sig2"], z["sig3"]], 1), 1.0)[keep]
    yr, day, m3 = z["yr"][keep], z["day"][keep], z["m3"][keep]
    cost = (OWNER_BPS * z["mid_t"] / 1e4)[keep]
    pre = 3 * st[:, 0] + st[:, 1]
    print(f"\nL {L} (theta 1.0, NY16 excluded)")
    for name, p, sgn in (("DD->buy", 0, 1.0), ("UU->sell", 8, -1.0)):
        m = pre == p
        g = sgn * m3
        row = []
        for per, mm in (("2010-16", m & (yr <= 2016)), ("2017-22", m & (yr >= 2017))):
            E, t, n = cluster_t(g[mm], day[mm])
            row.append(f"{per} gross {E:+.3f} (t {t:+.1f}, n {n}) net {E - np.median(cost[mm]):+.3f}")
        yrs = [round(float((g - cost)[m & (yr == y)].mean()), 3) for y in range(2010, 2023)]
        print(f"  {name}: " + " | ".join(row))
        print(f"     net by year 2010-2022: {yrs}  (positive {sum(v > 0 for v in yrs)}/13)")
