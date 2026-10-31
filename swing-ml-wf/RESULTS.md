# ML walk-forward filter: results (2026-10-31)

Plan `PLAN.md` (before outcomes). Code `code/build_ml.py`, `code/wf.py`; post-hoc `code/seeds.py`.
Outputs `out/WF.txt`, `out/WF.json`. Data 2010-2019 only (2020-2022 not used; 2023+ locked).
Money at the gold price of the time, fixed $0.168 spread, 0.1 lot per trade, USD/THB 33.77.
Dataset check: A+B 2010 net per trade +0.149 $/oz, same as swing-holdout historical_price.py.

## Pre-registered result (seed 7): ACCEPT (borderline)
| Year | Trades | Kept | Base THB | ML THB | Base max DD | ML max DD |
|---|---:|---:|---:|---:|---:|---:|
| 2012 | 1419 | 1216 | +101,212 | +85,308 | 26,755 | 35,804 |
| 2013 | 1308 | 1018 | +64,638 | +31,957 | 34,269 | 36,146 |
| 2014 | 1223 | 1044 | +23,037 | +32,870 | 26,367 | 31,628 |
| 2015 | 1222 | 1070 | -30,658 | -6,368 | 45,997 | 30,624 |
| 2016 | 1335 | 1002 | -78,285 | -59,205 | 85,635 | 74,618 |
| 2017 | 1266 | 728 | +74,636 | +57,591 | 8,925 | 9,137 |
| 2018 | 1282 | 815 | -13,006 | +3,852 | 41,358 | 24,496 |
| 2019 | 1277 | 762 | +15,595 | +26,719 | 44,747 | 22,798 |
- 2012-2019 pooled: base +157,170 THB, max DD 126,314; ML +172,725 THB, max DD 94,210; ML >= base
  in 5/8 years -> all three rules met.
- Ranking power is weak: Spearman(prediction, outcome) +0.066; outcome by prediction decile is not
  monotonic (top decile +0.174 $/oz, decile 9 -0.050, bottom +0.050).
- Importance: theta_over_cost 17, theta_bps 15, vol_bounce_leg 12, spread_rel 10, rangepos 7.

## Post-hoc robustness: 5 more random seeds -> accepted in 1 of 5
| Seed | ML net THB | ML max DD | Years >= base | Accept |
|---|---:|---:|---:|---|
| 1 | +146,436 | 90,002 | 4/8 | no |
| 2 | +121,956 | 95,461 | 5/8 | no |
| 3 | +199,111 | 97,451 | 5/8 | yes |
| 4 | +124,559 | 115,457 | 4/8 | no |
| 5 | +217,553 | 113,930 | 4/8 | no |
- Consistent: ML skips ~25-28% of trades and max drawdown is always lower (90-115k vs 126k).
- Not consistent: net ranges from -22% to +38% vs base; the seed-7 pass is not robust.

## Reading
- The ML filter does not reliably improve profit; it mostly trades less. Not a candidate for the
  2020-2022 exam in this form.
- What the model leans on most is the bounce size relative to the spread (theta / cost): the cost
  share decides much of the outcome, consistent with the historical-price re-check.
