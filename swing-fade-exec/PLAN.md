# Swing fade with realistic execution and a stop-loss (written before any outcome of this test)

Owner 11:39-11:40 ICT, 31 Oct: go ahead; 16:00 NY parked; look for an edge tradable every day;
do NOT open 2023+; keep testing on years before 2023 until the owner approves.

## Status of the data (honest framing)
- Data: Dukascopy M1 2010-2022 only (edge-map cache). 2023+ stays closed.
- 2010-2022 was already seen in `swing-structure/` (delay 0/1/2, no stop). This test adds
  execution realism and a stop; it is NOT out-of-sample. A pass means "survives realistic
  execution on seen data", the precondition for a later 2023+ test the owner may approve.

## Fixed inputs (from swing-structure, nothing new selected)
- Swings, patterns, units, cost exactly as `swing-structure/PLAN.md` (mid closes,
  y = 1e4 ln mid, theta $5 / $10 today, cost $0.168 = 0.4114 bps per round trip).
- Cells (4, fixed now): A $10 fade every swing; B $10 fade after COUNTER deep;
  C $5 fade after COUNTER deep; D $5 fade after EXPAND mild. Both directions always pooled.

## Trade rules
- Decision at the close of the confirmation minute i. Side = opposite of the new swing.
- Entry: close of the next traded minute i+1 (1-minute delay), same block, else no trade.
- Signal exit: the next swing confirmation j (same rule as swing-structure R1); exit at the
  close of j+1 (1-minute delay), or j if j+1 is in another block; block end forces exit.
- Stop-loss (resting order): first close after entry with adverse move >= k x theta from the
  entry price; exit at that close (the close beyond the level = slippage included).
- One position at a time per cell (trades end by the next confirmation + 1 minute).
- Primary stop k = 2. Sensitivity: k = 1.5 and no stop; delay 2 minutes; delay 0 reference.

## Pass rule (per cell, primary = delay 1, stop 2 theta)
1. 2017-2022 mean net per trade > 0 with day-clustered t >= 2.
2. Net > 0 in >= 4 of the 6 years 2017-2022.
3. 2010-2016 mean net per trade >= 0.
- 4 primary tests; a cell is a candidate for the 2023+ test only if it passes all three.

## Reported (not used for the verdict)
- Trades per trading day and share of days with at least one trade (the "every day" goal).
- Win rate, average win / loss, p1, worst trade, max drawdown and longest losing streak
  (2017-2022, per 1 oz), share of positive months.
- Net by session of entry (UTC 00-07 Asia, 07-13 London, 13-21 New York, 21-24 late).
- Checks: delay 0 / no stop must reproduce swing-structure/verify.py; sign-flip price null
  (3 draws per year) through the same code must give gross ~ 0 (net ~ -$0.168).
