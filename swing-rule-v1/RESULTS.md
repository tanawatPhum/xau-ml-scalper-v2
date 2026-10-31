# Swing rule variants v1: results (2026-10-31)

Plan `PLAN.md` (before outcomes). Code `code/variants.py`; post-hoc `code/overlap.py`.
Output `out/REPORT.txt`, `out/REPORT.json`. Data 2010-2019 only; 2020-2022 sealed; 2023+ closed.
Today's $ per oz; entry/exit 1 minute late; cost $0.168. sigma_eff = max(sigma60, sigma1440).

## Results (net per trade (t) | net per day | trades per day | stop rate)
| Rule | 2010-16 | 2017-19 |
|---|---|---|
| k 1 V0 base | +0.232 (2.9) / +1.11 / 4.80 / 6.8% | +0.157 (1.8) / +0.69 / 4.40 / 6.6% |
| k 1 V1 stop from sigma_eff | +0.282 (3.4) / +1.35 / 4.80 / 2.8% | +0.171 (1.9) / +0.76 / 4.40 / 3.4% |
| k 1 V2 all from sigma_eff | +0.727 (4.9) / +1.93 / 2.65 / 5.0% | +0.504 (3.4) / +1.32 / 2.62 / 5.3% |
| k 1 V0 + no Asia | +0.352 (3.3) / +1.18 / 3.36 | +0.251 (2.2) / +0.76 / 3.05 |
| k 1 V1 + no Asia | +0.395 (3.7) / +1.33 / 3.36 | +0.299 (2.5) / +0.91 / 3.05 |
| k 1 V2 + no Asia | +0.774 (4.8) / +1.72 / 2.22 | +0.497 (3.1) / +1.07 / 2.16 |
| k 1.5 V0 base | +0.439 (2.9) / +1.12 / 2.54 / 7.2% | +0.583 (3.7) / +1.35 / 2.31 / 6.5% |
| k 1.5 V1 | +0.486 (3.1) / +1.24 / 2.54 / 2.7% | +0.561 (3.4) / +1.30 / 2.31 / 2.8% |
| k 1.5 V2 | +1.167 (3.8) / +1.45 / 1.24 / 4.4% | +0.499 (1.7) / +0.57 / 1.14 / 4.2% |

## Acceptance (pre-registered)
- k 1: V1 and V2 both improve per trade and per day in both periods; V2 kept (higher net per
  day). The Asia filter on top of V2 lowers net per day in both periods -> rejected.
  Accepted rule: k 1 V2 (bounce, trailing exit, large-leg test and stop all from sigma_eff).
- k 1.5: V1 and V2 do not improve both periods -> base V0 kept.

## k 1 V2 profile (2017-19)
- 2.6 trades/day, win 65.9%, average win +4.00 / loss -6.26, p1 -22.7, worst -40.1 (2010-16
  worst -103.4: a price jump through the stop, same event for every variant).
- 3/3 validation years positive, 6/7 discovery years.
- Overlap with k 1.5 V0: 24% of signals coincide (same side within 10 minutes): mostly
  different trades.

## Caveat
- In-sample: the idea for V1/V2 came from swing-factors-b1 stop rates on 2010-2019. The real test
  is the one-shot 2020-2022 holdout of the accepted rules (k 1 V2 and k 1.5 V0).
