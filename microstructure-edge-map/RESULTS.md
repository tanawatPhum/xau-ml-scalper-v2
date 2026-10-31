# Microstructure edge map, steps 0-1: results (2026-10-31)

Plan: `PLAN.md` (written before outcomes). Code: `code/` (load, step0_spread, step1_build,
step1_scan, verify16, verify16b). Outputs: `out/STEP0_SPREAD.json`, `out/STEP1_SCAN.json`.
Data: Dukascopy XAUUSD M1 BID+ASK 2010-2022, minutes where both sides traded.

## Step 0 - cost
- Dukascopy spread median $0.24-0.51 by year = 1.9-4.2 bps; p90 2.3-5.3 bps.
- Almost flat through the day (1.9-2.1 bps, 2017-2022); widens only around the daily break,
  NY 16:30-19:30 (2.2-2.5 bps median, p90 up to 3.7).
- Owner broker reference 0.411 bps = $0.05-0.07 at 2010-2022 prices: about 5x cheaper than the
  Dukascopy spread. Tradability below is judged against both.

## Step 1 - random-walk deviation scan (strong moves = top 20% |r_prev| per cell)
| h | pooled E 2010-16 | pooled E 2017-22 | hour x vol cells non-random (null mean/max) | tradable vs owner | vs Dukascopy |
|---|---|---|---|---|---|
| 1 | +0.003 | -0.011 (t -9.2) | 12 / 72 (0 / 0) | 0 | 0 |
| 5 | -0.011 | -0.049 (t -10.0) | 3 / 72 (0 / 0) | 2 (NY 16h) | 0 |
| 15 | -0.017 | -0.050 (t -3.8) | 3 / 72 (0 / 0) | 3 (NY 16h) | 0 |
| 30 | -0.024 | -0.055 (t -2.1) | 2 / 72 (0 / 0) | 2 (NY 16h) | 0 |
| 60 | +0.046 | -0.056 (t -1.0) | 2 / 71 (0 / 0) | 2 (NY 16h) | 2 (NY 16h) |

- 1 minute: broad small reversal, $0.007-0.017 per strong move: noise-level, far below any cost.
- 5-30 minutes pooled: a weak reversal that appears only in 2017-2022 (about -$0.05), below the
  owner cost (~$0.063) and absent in 2010-2016.
- Jumps (|z| >= 2.5): small reversal at 1-5 min ($0.02-0.05), noise elsewhere.
- The only cell that passes at every horizon >= 5 min is NY hour 16.

## Verification of NY 16h
- Same on BID only, ASK only and mid (h=15: -0.192 / -0.180 / -0.186), so not a spread artefact.
- Concentrated at the 16:00 NY start (the move into 16:00 reverses afterwards); exit spread
  normal ($0.36-0.38). 16:00 NY = US equity close (hypothesis for the mechanism).
- Fade of strong moves into 16:00 (2017-2022): +$0.64 (5 min), +$0.73 (15), +$0.90 (30);
  win 71-77%; positive in 13/13 years at every horizon; medians match means; symmetric for up
  and down moves; trimmed means unchanged.
- Control: the same test at every other on-the-hour NY time shows no stable effect
  (largest t outside 16:00 is 3.4 and flips sign between periods).
- Entry one minute late (signal at 16:00, entry at the 16:00 close): +$0.15 / +$0.32 / +$0.55
  (2017-2022); at 15 and 30 min positive in 13/13 years. Most of the move happens in the first
  minute, so execution speed matters.
- About 40 strong events per year (top 20% moves into 16:00).

## Limits
- One data source (Dukascopy). A real-broker or futures check is needed before any trading use.
- M1 closes: intra-minute order of ticks is unknown; the 1-minute-late entry is the realistic
  lower bound used here.
- 2023+ not used (protected).
