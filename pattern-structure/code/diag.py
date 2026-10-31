"""Post-hoc diagnostics (labelled as such; pre-registered rules unchanged).
1. Sign-flip null: keeps the order and size of minute moves (volatility timing), removes
   direction dependence. Real vs random-order vs sign-flip family shares.
2. NY16 patterns UU/DD by exact decision minute (is it only the 16:00 effect?).
3. Net per-trade economics of the playable cells after the owner's cost."""

import json

import numpy as np

from patterns import (CACHE, FAM_OF_CODE, FAMILIES, OUT, OWNER_BPS, YEARS, build_triples,
                      load_year, states)

LS = (5, 10, 20)
rng = np.random.default_rng(99)
rep = {}
for L in LS:
    real_c, sign_c = [], []
    for yr in YEARS:
        base, bid, ask, mid = load_year(yr)
        d = build_triples(base, bid, ask, mid, L, 10, rng, null_kind="sign")
        st = states(np.stack([d["m1"], d["m2"], d["m3"]], 1),
                    np.stack([d["sig1"], d["sig2"], d["sig3"]], 1), 0.5)
        real_c.append(9 * st[:, 0] + 3 * st[:, 1] + st[:, 2])
        sign_c.append(d["null"].ravel())
    rc = np.concatenate(real_c).astype(int)
    sc = np.concatenate(sign_c).astype(int)
    z = np.load(CACHE / f"TRIPLES_L{L}.private.npz")
    pc = z["null"].ravel().astype(int)
    fr = np.bincount(FAM_OF_CODE[rc], minlength=5) / len(rc)
    fs = np.bincount(FAM_OF_CODE[sc], minlength=5) / len(sc)
    fp = np.bincount(FAM_OF_CODE[pc], minlength=5) / len(pc)
    rep[L] = {"families": {f: dict(real=float(fr[i]), random_order=float(fp[i]),
                                   sign_flip=float(fs[i])) for i, f in enumerate(FAMILIES)}}
    print(f"\nL {L}: family real% | random-order% | sign-flip% (direction removed, timing kept)")
    for i, f in enumerate(FAMILIES):
        print(f"  {f:9s} {fr[i] * 100:6.2f} | {fp[i] * 100:6.2f} | {fs[i] * 100:6.2f}")

    # 2 + 3: NY16 UU / DD by decision minute, and economics, from the cached triples
    st = states(np.stack([z["m1"], z["m2"], z["m3"]], 1),
                np.stack([z["sig1"], z["sig2"], z["sig3"]], 1), 0.5)
    pre = 3 * st[:, 0] + st[:, 1]
    yr = z["yr"]
    cost = OWNER_BPS * z["mid_t"] / 1e4
    rep[L]["ny16"] = {}
    for name, p, sgn in (("UU", 8, -1.0), ("DD", 0, +1.0)):
        m = (pre == p) & (z["nyh"] == 16)
        print(f"  {name} at NY16 (fade = {'sell' if sgn < 0 else 'buy'}), 2017-2022 by minute:")
        for mm in sorted(np.unique(z["nymin"][m])):
            k = m & (z["nymin"] == mm) & (yr >= 2017)
            g = sgn * z["m3"][k]
            if k.sum() >= 20:
                print(f"    16:{mm - 960:02d} n {k.sum():4d} gross {g.mean():+.3f} net "
                      f"{(g - cost[k]).mean():+.3f} win {(g - cost[k] > 0).mean() * 100:.0f}%")
        k = m & (yr >= 2017)
        g = sgn * z["m3"][k] - cost[k]
        per_year = [round(float(g[yr[k] == y].mean()), 3) for y in range(2017, 2023)]
        rep[L]["ny16"][name] = dict(n=int(k.sum()), net_mean=float(g.mean()),
                                    win=float((g > 0).mean()), per_year=per_year,
                                    trades_per_year=float(k.sum() / 6))
        print(f"    all NY16 2017-22: n {k.sum()} ({k.sum() / 6:.0f}/yr) net {g.mean():+.3f} "
              f"win {(g > 0).mean() * 100:.0f}% per-year net {per_year}")
with open(OUT / "DIAG.json", "w", encoding="utf-8") as f:
    json.dump(rep, f, indent=1)
