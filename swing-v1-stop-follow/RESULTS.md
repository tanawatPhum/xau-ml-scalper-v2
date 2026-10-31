# Results: follow the move after a v1 stop-out (31 Oct 2026, owner 22:24)
- Plan: PLAN.md, written before outcomes. Code: follow.py.
- Source: v1 Exness version (audit engine, flat at 16:55 NY), with 510 stop-outs over 2010-22
  (A 298, B 212).
- Money: 0.1 lot, $0.168 spread, 33.77 THB/USD.
- 2017-19 and 2020-22 are shown descriptively only, because no variant qualified on 2010-16.

## Verdict: no variant qualifies; after a stop the next move is a coin flip

| Variant | 2010-16 net (t) | 2017-19 | 2020-22 | 2010-22 total | Win | Median hold |
|---|---|---|---|---|---|---|
| E0 hold to the daily cutoff | +$0.627 (0.80) | +17,625 | -36,885 | +39,814 THB | 49% | 504 min |
| E1 trail 1 theta | -$0.415 (-2.08) | -12,871 | -26,793 | -80,322 THB | 34% | 28 min |
| E2 trail 2 theta | -$0.353 (-0.84) | +2,940 | -27,834 | -59,457 THB | 36% | 124 min |
| E3 +1 / -1 theta | -$0.270 (-1.16) | -3,270 | -4,100 | -33,786 THB | 45% | 28 min |
| E4 +2 / -1 theta | -$0.178 (-0.60) | -1,673 | +2,065 | -17,061 THB | 35% | 49 min |

- **Brackets:** they hit the target about as often as a random walk would (E3 44.9% vs 50%,
  E4 35.5% vs 33%). Gross per trade is about 0 (-$0.03 / +$0.07), so the spread decides.
- **Trailing exits:** they lose. The move after a stop is choppy, and a 1-theta trail is hit
  quickly.
- **E0 (hold to the daily cutoff):** positive on average, but t is only 0.4-0.8 and the years
  swing widely: 2013 +48,183, 2014 -26,512, 2020 -60,535, 2022 +21,776. It cannot be told apart
  from luck.
- **v1 + E0 (descriptive):** ends at 599,077 THB against 559,263 for v1 alone, but the max DD
  (closed trades) rises from 59,354 to 68,690. Not recommended.

## Reading
The stopped trades were the wrong direction, but that is known only after the fact. At the moment
of the stop, the future move is close to random. Following it adds spread costs without a
reliable edge. This matches swing-v2-ruleC (follow a failing fade at 1-1.5 theta lost) and the
earlier finding that momentum rules lose at these scales.
