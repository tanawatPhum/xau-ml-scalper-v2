# Volatility-scaled bounce from the swing low: results (2026-10-31)

Plan `PLAN.md` (before outcomes). Code: `code/adaptive.py`, `run.py`, `report.py`; checks
`smoke.py`, `null_full.py` (added after the first report, see Checks); descriptive `detail.py`.
Outputs in `out/`: REPORT.txt/json, NULL_FULL.txt/json, DETAIL.txt/json, RUN_META.json.
Data 2010-2019 only; holdout 2020-2022 sealed (not computed); 2023+ closed.
Money = today's dollars per 1 oz; cost $0.168 per round trip; entry and exit 1 minute late.

## Scale of k (bounce = k x sigma60, sigma60 = typical 60-minute move)
| k | bounce $ p10 / p50 / p90 | all-bounce trades per day |
|---|---|---:|
| 0.25 | 0.79 / 1.49 / 3.07 | 129.6 |
| 0.5 | 1.56 / 2.94 / 5.99 | 51.2 |
| 0.75 | 2.30 / 4.35 / 8.86 | 27.4 |
| 1 | 3.04 / 5.74 / 11.52 | 17.2 |
| 1.5 | 4.52 / 8.46 / 16.88 | 8.9 |
| 2 | 5.90 / 11.02 / 22.08 | 5.4 |
| 3 | 8.74 / 16.49 / 32.92 | 2.5 |

## Verdict (pre-registered rules 1-4): 2 of 28 cells PASS
- All bounces (cell "all"): no k is playable; net < 0 at every k in discovery (2010-16).
- The edge appears only after a LARGE leg (leg before the bounce >= 2.5 x the bounce threshold),
  on the fade side (bet that the big leg resumes):

| Cell | Disc gross (t) | Disc net | Val gross (t) | Val net | Val years > 0 | Val trades/day | Stop-3 net disc / val |
|---|---:|---:|---:|---:|---:|---:|---:|
| k 1, large leg, fade | +0.471 (5.5) | +0.303 | +0.336 (3.5) | +0.168 | 3/3 | 4.40 | +0.232 / +0.157 |
| k 1.5, large leg, fade | +0.690 (4.2) | +0.522 | +0.686 (4.0) | +0.518 | 3/3 | 2.31 | +0.439 / +0.583 |

- Neighbours: k 0.75 large (disc t 6.2, val net +0.000) and k 2 large (disc t 3.6, val +0.043
  gross) pass discovery but not validation. Small-leg cells at k >= 1.5 lean to follow (val net
  +0.17 to +0.41) but fail discovery.
- Sensitivity (net disc / val): k 1 large stop 2 theta +0.137 / +0.159, delay 2 +0.311 / +0.162;
  k 1.5 large stop 2 theta +0.377 / +0.510, delay 2 +0.528 / +0.531.

## Detail of the passing cells (stop 3 theta unless noted; not used for the verdict)
| | k 1 large | k 1.5 large |
|---|---|---|
| Bounce $ p10 / p50 / p90 | 2.69 / 5.14 / 10.78 | 3.76 / 7.07 / 14.23 |
| Leg before bounce $ p10 / p50 / p90 | 8.85 / 18.04 / 42.18 | 12.57 / 25.34 / 56.70 |
| Hold minutes p10 / p50 / p90 | 18 / 57 / 133 | 33 / 99 / 234 |
| Stop hit | 6.8% | 7.0% |
| Val win / avg win / avg loss | 65% / +2.80 / -4.75 | 66% / +3.99 / -6.00 |
| Val p1 / worst (no stop) | -20.2 / -74.0 | -30.2 / -66.7 |
| Val p1 / worst (stop 3) | -19.7 / -34.0 | -21.3 / -54.9 |
- Net per year, no stop: k 1: 2010 +0.54, 2011 +0.43, 2012 +0.47, 2013 +0.47, 2014 +0.23,
  2015 +0.02, 2016 -0.11, 2017 +0.16, 2018 +0.16, 2019 +0.18 (weakening after 2014).
  k 1.5: +0.73, +0.66, +0.91, +0.70, +0.67, -0.32, +0.19, +1.01, +0.25, +0.28.
- Sessions (UTC, stop 3, disc / val): k 1: Asia -0.05 / -0.05, London +0.55 / +0.29,
  NY +0.27 / +0.25. k 1.5: Asia +0.67 / +0.52, London +1.09 / +0.89, NY +0.04 / +0.48.
- Fixed-$ version of the large-leg cell: k 1 ($5.73 fixed): no stop +0.226 / +0.284, stop 3
  +0.144 / +0.239 (as good as adaptive); k 1.5 ($8.45 fixed): +0.308 / +0.014, stop 3
  +0.305 / -0.029 (adaptive clearly better). The leg-size condition matters more than the scaling.

## Checks
- Smoke test (2012): synthetic Gaussian walk gross -0.02 to -0.12 (|t| <= 1.2).
- run.py price null (1 draw): fade gross t up to +3.25 at k 0.5-1 (all cells) - should be ~0.
  Because of this, `null_full.py` ran 10 more draws through the full pipeline and rule: mean gross
  ~0 for every cell (e.g. k 1 all +0.007, sd 0.042) and 0 false PASS in 10 x 28 cells; the first
  draw was an extreme draw, not a bias.
- Day-level sign flips of trade P&L: 0 false passes (rules 1, 2, 4) in 20 draws.

## Reading
- Bounce size alone does not create an edge. A bounce of about 1-1.5 x the typical hourly move,
  after a leg at least 2.5 times that size, tends to fail and the big leg resumes.
- 2010-2019 has been seen (in aggregate) by earlier fixed-$ studies; these cells are new.
  The sealed 2020-2022 holdout is the next honest check; 2023+ needs the owner.
