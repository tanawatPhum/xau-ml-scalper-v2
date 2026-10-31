"""Smoke test of v1-r3 code paths on 2010-2011 (design years). Prints only signal counts, never trade outcomes."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v1_r3 as v  # noqa: E402

v.load_events = lambda last: np.array([v.utc_minute_demo] if False else [], np.int64)
t0 = time.time()
l2 = v.lock2_info()
c = v.d.load([2010, 2011], "design")
c = v.add_features(c, "2011-12-31")
print("features ok", round(time.time() - t0, 1), "s; s60_seas finite", float(np.isfinite(c["s60_seas"]).mean()),
      "u finite", float(np.isfinite(c["u"]).mean()), "gvz days", len(c["gvz_days"]), flush=True)
for r in ("A", "B"):
    mine, _ = v.build_rule3(c, l2["base"]["rules"][r], l2["ov"].get(r, {}))
    ref = v.r2.build_rule(c, l2["base"]["rules"][r], l2["ov"].get(r, {}))
    np.testing.assert_array_equal(mine, ref)
print("build_rule3 == v1-r2 build_rule", flush=True)
v.load_events = lambda last: np.sort(__import__("pandas").read_csv(v.OUT / "EVENTS_2010_2022.csv").query("date <= @last").utc_minute.to_numpy(np.int64))
c["events"] = v.load_events("2011-12-31")
for fam, variants in v.FAMILIES.items():
    if fam == "F8":
        continue
    for var in variants:
        sig, info = v.signals(c, l2["base"]["rules"], l2["ov"], {"A": {fam: var}, "B": {fam: var}})
        print(fam, var, {r: (info[r]["eligible"], info[r]["blocked"]) for r in ("A", "B")}, flush=True)
print("SMOKE OK", round(time.time() - t0, 1), "s", flush=True)
