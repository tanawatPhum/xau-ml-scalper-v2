# Swing strategy on Model B zones (E68 A2): results (2026-10-31)

Plan `PLAN.md` (before outcomes). Code `code/bid_cache.py`, `code/bzone.py`; descriptive
`code/debug_counts.py`, `code/example_check.py`. Output `out/BZONE.txt`, `out/BZONE.json`.
Data 2011-2019. Money at the gold price of the time, $0.168 spread, 0.1 lot, USD/THB 33.77.

## Pre-registered result: primary NOT passed
- Population (rules A + B trades whose peak and entry are inside the same B session window):
  578 trades in 9 years. Z (peak touched a B zone and closed back inside/below it): 156.
- Z net +0.316 $/oz per trade (t 1.9), win 58%, stop 0.6%; N net +0.082 (t 0.6), win 56%.
  Difference +0.234 (t 1.1); 2011-16 +0.056 (t 0.2), 2017-19 +0.551 (t 2.2) -> fails (pooled t < 2).
- Z with the stop at the peak: +0.137 (t 0.7) - worse than the 3 theta stop.
- Money (Z, 3 theta, 0.1 lot): 2011 +4,012; 2012 +6,494; 2013 +1,010; 2014 -1,346; 2015 -930;
  2016 +887; 2017 +2,463; 2018 +900; 2019 +3,166 THB -> about +16,700 THB in 9 years.
- Breakdown (Z, small samples): zone rank 2-3 positive (+0.57 / +0.81), rank 1 and 4 negative;
  London +0.79, Asia +0.59, New York -0.08.

## Why so few trades: scale mismatch
- The strategy's legs are long: rule A median leg 157-166 minutes, peak-to-entry about 210 minutes,
  while a B session window is 240 minutes. Only ~5-7% of the strategy's trades fit inside one window.
- Owner's example (2017-01-18 London): peak 10:09 UTC at 1214.80 (zone #3 1213.85-1214.35, price
  poked $0.45 above the zone top), low 11:32; leg $3.35. The strategy's theta was $2.21 (A) /
  $2.65 (B) at that time, so the leg was only 1.6 theta (< 2.5) and the owner's entry bounce (~$1)
  is under half of theta. The owner's pattern lives at about half the strategy's scale.
- The pre-registered "rejection" also required the peak minute to close at or below the zone top;
  in the example the price closed above the zone first, so a looser touch rule would be needed.

## Reading
- At its own scale the strategy rarely forms a B-zone peak inside a session; the result is too
  small to judge. Testing the owner's pattern needs a B-zone version: smaller theta (about
  0.4-0.5 x sigma), the leg measured from the zone touch, and a touch rule that allows a short
  poke through the zone.
