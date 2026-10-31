# Results: rule C search, round 2 (31 Oct 2026, owner 22:33)
- Plan: PLAN.md, written before outcomes. Code: candidates.py, select_.py.
- Setup: audit-engine data and volatility, Exness schedule, fills at the next minute's close,
  $0.168, 0.1 lot.
- Data: 2010-16 only. Nothing qualified, so 2017-19 was not opened.

## Verdict: 0 of 14 cells qualify; no rule C
- v1 Exness version, 2010-16: +267,489 THB, closed-trade DD 59,234, ratio 4.52.
- Family-wise null: the best t reaches 2.64 at p95.

**R1: fade the extended leg** (12 cells)

| Cell | Trades/day | Net per trade (t) | 2010-13 / 2014-16 THB |
|---|---|---|---|
| Best: A, m 5, stop 2 theta | 0.25 | +$0.178 (1.01) | +40,471 / -14,209 |
| A, m 3.5 | 0.96 | -$0.007 / -$0.046 | |
| A, m 2.5 | 2.5 | -$0.04 to -$0.07 | |
| B, all cells | | -$0.04 to -$0.32 | |

- Win rates are 61-65%, but the losses are larger than the wins.
- Fading a leg at 2.5-5 theta earns gross less than the spread.

**R3: fade big moves into scheduled times** (2 pooled cells)

| Cell | Trades/day | Net per trade (t) | 2010-16 THB |
|---|---|---|---|
| h 15 | 0.99 | -$0.129 (-1.62) | -73,980 |
| h 30 | 0.93 | -$0.138 (-1.38) | -75,002 |

- Per slot, descriptive only: every slot loses except the LBMA AM auction at h 30 (341 trades,
  +$0.258/oz, +29,678 THB, 50% win). This is one positive slot out of 10, picked after the fact,
  so it is not evidence.

## Reading
- Rounds 1 and 2 together cover 30 pre-registered cells, plus the stop-follow test. On 1-minute
  gold prices alone, no second rule adds a reliable edge to v1.
- The two rules in v1 already capture the one structural effect found: a bounce after a large
  leg tends to fail.
- Candidates that remain need the owner's decision or new information:
  1. the 16:00 NY reversal (strongest, parked by the owner);
  2. news / calendar information (e.g. scheduled releases), which is not in the price data.
