"""Post-hoc look at the no-stop sensitivity rows (not part of the verdict)."""
import json

import numpy as np

r = json.load(open("../out/REPORT.json"))
for c in ["A $10 every swing", "B $10 COUNTER deep"]:
    s = r["cells"][c]["d1_k0"]
    print(c, "delay1 no stop: years_pos", s["years_pos"], {k: round(v, 2) for k, v in s["ynet"].items()},
          "| would pass rule:", s["pass"])
for k in (0, 2):
    z = np.load(f"../cache/T_th10_d1_k{k}.private.npz")
    m = (z["code"] == 5) & (z["yr"] >= 2017)
    x = z["net"][m]
    st = z["reason"][m] == 1
    print(f"B stop k={k}: worst {x.min():+.2f} p1 {np.quantile(x, 0.01):+.2f}"
          + (f" | stopped {st.mean() * 100:.1f}% avg {x[st].mean():+.2f}" if k else ""))
z0 = np.load("../cache/T_th10_d1_k0.private.npz")
m = (z0["code"] == 5) & (z0["yr"] >= 2017)
z2 = np.load("../cache/T_th10_d1_k2.private.npz")
st = (z2["reason"][m] == 1)
print(f"B: the {st.sum()} trades stopped at 2 theta ended without stop at avg {z0['net'][m][st].mean():+.2f}, "
      f"{(z0['net'][m][st] > z2['net'][m][st]).mean() * 100:.0f}% of them better than the stop")
