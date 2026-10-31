"""Step 0: spread (cost) map, 2010-2022."""

import json

import numpy as np

from common import OUT, OWNER_BPS, YEARS, load, ny_time, s60

OUT.mkdir(exist_ok=True)
rows = []
for yr in YEARS:
    base, bid, ask, mid = load(yr)
    hr, slot, wd = ny_time(base, len(bid))
    s = s60(bid)
    ok = np.isfinite(mid)
    sp = ask - bid
    bps = sp / mid * 1e4
    for i in np.flatnonzero(ok):
        pass
    rows.append(dict(year=yr, sp=sp[ok], bps=bps[ok], mid=mid[ok], slot=slot[ok], wd=wd[ok],
                     s=s[ok], hr=hr[ok]))
    print(yr, "loaded", flush=True)

sp = np.concatenate([r["sp"] for r in rows])
bps = np.concatenate([r["bps"] for r in rows])
mid = np.concatenate([r["mid"] for r in rows])
slot = np.concatenate([r["slot"] for r in rows])
wd = np.concatenate([r["wd"] for r in rows])
s = np.concatenate([r["s"] for r in rows])
yrs = np.concatenate([np.full(len(r["sp"]), r["year"]) for r in rows])
cuts = np.nanquantile(s[(yrs <= 2016)], [1 / 3, 2 / 3])
terc = np.where(np.isfinite(s), np.searchsorted(cuts, s), -1)
rep = {"owner_bps": OWNER_BPS, "s60_cuts_2010_2016": cuts.tolist()}

print(f"\nOwner broker reference: {OWNER_BPS:.3f} bps")
print("year | median $ | p90 $ | median bps | p90 bps | owner ref $ at median price")
rep["by_year"] = {}
for y in YEARS:
    m = yrs == y
    v = dict(med=float(np.median(sp[m])), p90=float(np.quantile(sp[m], 0.9)),
             med_bps=float(np.median(bps[m])), p90_bps=float(np.quantile(bps[m], 0.9)),
             owner_usd=float(OWNER_BPS * np.median(mid[m]) / 1e4))
    rep["by_year"][y] = v
    print(f"{y} | {v['med']:.3f} | {v['p90']:.3f} | {v['med_bps']:.2f} | {v['p90_bps']:.2f} "
          f"| {v['owner_usd']:.3f}")

print("\nNY half-hour slot (2017-2022): median bps, p90 bps, share of minutes")
test = yrs >= 2017
rep["by_slot_2017_2022"] = {}
for g in range(48):
    m = test & (slot == g)
    if m.sum() < 1000:
        continue
    v = (float(np.median(bps[m])), float(np.quantile(bps[m], 0.9)), float(m.mean()))
    rep["by_slot_2017_2022"][g] = v
    th = (g // 2 + 11) % 24  # NY -> Thai (summer, +11; winter +12)
    print(f"NY {g // 2:02d}:{30 * (g % 2):02d} (~Thai {th:02d}:{30 * (g % 2):02d}/+1h winter) "
          f"| {v[0]:.2f} | {v[1]:.2f} | {v[2] * 100:.1f}%")

print("\nWeekday (2017-2022) median bps:",
      {int(d): round(float(np.median(bps[test & (wd == d)])), 2) for d in range(7)
       if (test & (wd == d)).sum() > 1000})
print("S60 tercile (2017-2022) median bps:",
      {int(t): round(float(np.median(bps[test & (terc == t)])), 2) for t in range(3)})
rep["by_tercile_2017_2022"] = {int(t): float(np.median(bps[test & (terc == t)])) for t in range(3)}
with open(OUT / "STEP0_SPREAD.json", "w", encoding="utf-8") as f:
    json.dump(rep, f, indent=1)
