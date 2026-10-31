import json

import numpy as np

from patterns import CACHE, OUT

R = json.load(open(OUT / "REPORT.json", encoding="utf-8"))
for L in ("5", "10", "20"):
    A = R[L]["A"]
    print(f"\nL {L}: families real% [CI] (disc / conf real%) vs random-order%")
    for f, e in A["families"].items():
        print(f"  {f:9s} {e['all'][0] * 100:5.2f} [{e['ci'][0] * 100:.2f}-{e['ci'][1] * 100:.2f}]"
              f" ({e['disc'][0] * 100:.2f} / {e['conf'][0] * 100:.2f}) vs {e['all'][1] * 100:.2f}")
    print("  pooled prefix E_sigma (all):",
          {p: round(v["all"]["E_sigma"], 3) for p, v in R[L]["pooled_prefix"].items()})
    print("  theta=1.0 pooled prefix E (all, t):",
          {p: (round(v["all"]["E"], 4), round(v["all"]["t"], 1))
           for p, v in R[L]["pooled_prefix_theta1"].items()})
z = np.load(CACHE / "TRIPLES_L10.private.npz")
S = z["sig3"] / np.sqrt(10 / 60)
print("\nmedian S60 all years", round(float(np.median(S)), 3), "-> 0.5 sigma (10 min) $",
      round(float(np.median(0.5 * z["sig3"])), 3))
print("windows per year (L10):", round(len(S) / 13))
