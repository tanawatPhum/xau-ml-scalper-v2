# Swing fade with realistic execution and a stop: results (2026-10-31)

Plan `PLAN.md` (written before this test's outcomes). Code: `code/fade_exec.py`, `run.py`,
`report.py`; post-hoc `peek_nostop.py`. Outputs: `out/REPORT.txt`, `out/REPORT.json`,
`out/TRADING_DAYS.json`. Data 2010-2022 only (2023+ closed by owner instruction 11:40 ICT).

## Correction after the first run (planned check)
- First run defined cell A as every swing including the first three swings of each block (no
  pattern yet). The planned reconciliation with swing-structure/verify.py failed for A only
  (+0.234 vs +0.478 at delay 0, no stop). A was corrected to the swing-structure cell (every
  patterned swing); the old definition is kept as A0. After the fix all cells reproduce verify.py
  exactly (delay 0/1/2, no stop).

## Pre-registered verdict (delay 1 minute, stop 2 theta): all four cells FAIL
| Cell | 2010-16 net (t) | 2017-22 net (t) | Years > 0 | Stop rate | Pass |
|---|---:|---:|---:|---:|---|
| A $10 every swing | -0.031 (-0.4) | +0.116 (+1.1) | 5/6 | 13.4% | no |
| B $10 COUNTER deep | +0.271 (+1.3) | +0.313 (+1.3) | 4/6 | 13.1% | no |
| C $5 COUNTER deep | -0.010 (-0.2) | -0.011 (-0.1) | 2/6 | 16.7% | no |
| D $5 EXPAND mild | +0.040 (+0.4) | +0.071 (+0.6) | 4/6 | 15.6% | no |
(A0, unpatterned included: -0.147 / -0.035, 3/6.)

## Sensitivity, 2017-22 net (t) [2010-16 net]
| Cell | Delay | No stop | Stop 2 theta | Stop 1.5 theta |
|---|---|---:|---:|---:|
| A | 1 | +0.271 (2.3) [+0.009] | +0.116 (1.1) [-0.031] | +0.080 (0.8) [-0.113] |
| A | 2 | +0.094 (0.8) [-0.059] | -0.086 (-0.8) | -0.107 (-1.0) |
| B | 1 | +0.566 (2.2) [+0.411] | +0.313 (1.3) [+0.271] | +0.206 (0.9) [+0.042] |
| B | 2 | +0.455 (1.7) [+0.250] | +0.229 (0.9) | +0.060 (0.2) |
| C | 1 | +0.088 (1.1) [+0.081] | -0.011 (-0.1) | -0.077 (-1.1) |
| D | 1 | +0.138 (1.2) [+0.149] | +0.071 (0.6) | -0.017 (-0.2) |
- Every stop lowers the result. Post-hoc: with no stop, A and B at delay 1 would meet the
  numeric rule (A 4/6 years, B 5/6), but that is the variant already seen in swing-structure, not
  the pre-registered one, and B's worst trade without a stop is -$85.71 per oz (p1 -$35.45).
- Why the stop hurts (B): 13.1% of trades hit the 2 theta stop and lose -$21.90 on average; the
  same trades without a stop end at -$19.97, and 69% of them end better than the stop. A loss of
  ~$2 on 13% of trades removes ~$0.25 per trade, most of the edge. The edge is the recovery of
  large adverse moves, i.e. it cannot be separated from the tail risk.

## Every-day view (primary, 2017-22, per 1 oz)
| Cell | Trades/day | Days with a trade | Win | Avg win / loss | Worst | Max DD | Months > 0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 5.7 | 83% | 62.3% | +6.76 / -10.88 | -59.74 | 714.9 | 56% |
| B | 1.1 | 52% | 61.9% | +6.98 / -10.51 | -34.20 | 264.1 | 56% |
| C | 4.5 | 95% | 61.7% | +3.94 / -6.37 | -37.98 | 537.6 | 47% |
| D | 1.9 | 75% | 62.8% | +3.79 / -6.20 | -26.76 | 336.9 | 51% |
(Worst can exceed the stop because the stop fills at a minute close and at block ends.)

## Checks
- Sign-flip price null through the same code: gross -$0.05 to +$0.03 per trade, |t| <= 1.0.
- Delay 0 / no stop reproduces swing-structure/verify.py for A-D.

## Verdict
- The swing fade does not survive realistic execution with risk control on 2010-2022.
  No candidate for the 2023+ test from this line. Swing-pattern work is closed unless the
  owner decides otherwise.
