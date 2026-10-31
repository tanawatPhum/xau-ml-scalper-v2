# Results: rule C search for swing v2 (31 Oct 2026)
Plan PLAN.md (before outcomes). Code: code/candidates.py (uses swing_v1.py unchanged), select_.py;
descriptive near_miss.py. Money: 0.1 lot, at the time's price, $0.168 spread, 33.77 THB/USD.
Data 2010-16 only: nothing qualified, so 2017-19 was not opened. 2020-22 not used; 2023+ closed.
Reproduction: the v1 A and B trades rebuilt here equal swing-v1 exactly (A 4,477 / B 2,854).

## Verdict: no rule C qualifies; v2 is not formed; v1 stays the best version
v1 alone, 2010-16: +315,156 THB, max DD 58,715, ratio 5.37. Family-wise null best t p95 2.68.

| Family | Cells | 2010-16 net per trade | Total THB 2010-16 | Reading |
|---|---|---|---|---|
| CL ride the big leg | 6 | -$0.35 to -$0.42 (t -2.8 to -7.4) | -140k to -881k | gross negative too |
| CF follow a failing v1 fade | 4 | -$0.49 to -$1.25 (t -2.9 to -6.1) | -91k to -275k | gross negative too |
| CP 240-minute breakout | 2 | -$0.28 / -$0.35 (t -5.3 / -2.6) | -733k / -446k | gross negative too |
| CS slower-scale fade | 4 | +$0.155 to +$0.409 | +47k to +183k | positive, not robust |

Slower-scale fade detail (none passes all rules):

| Cell | Trades/day | Net (t) | 2010-13 / 2014-16 THB | v1 + C: THB, max DD, ratio | Overlap with v1 | Daily corr | p (family) |
|---|---|---|---|---|---|---|---|
| 2 x eff | 0.65 | +$0.409 (2.13) | +161,666 / -6,714 | +470,108, 82,295, 5.71 | 11% | 0.09 | 0.20 |
| 1.5 x sigma1440 | 1.69 | +$0.186 (2.13) | +219,208 / -36,386 | +497,977, 103,018, 4.83 | 36% | 0.38 | 0.20 |
| 2 x sigma1440 | 0.86 | +$0.155 (0.91) | +82,677 / -4,818 | +393,015, 81,595, 4.82 | 28% | 0.23 | 0.88 |
| 3 x eff | 0.20 | +$0.395 (0.66) | +52,252 / -5,596 | +361,812, 79,426, 4.56 | 0% | -0.09 | 0.95 |

Per year, 2 x eff: 2010 +45,221, 2011 +71,868, 2012 +37,808, 2013 +6,769, 2014 +7,058,
2015 -14,879, 2016 +1,107 (strong in high-volatility years, flat in quiet ones, like rule A).

## Reading
- Every follow / momentum rule loses before costs (gross -$0.11 to -$1.08 per oz). At these
  scales gold mean-reverts: fading big moves is the only family with an edge. This agrees with
  swing-structure, the behavior-persistence study and the stop and entry-timing tests.
- The best near miss, fade at 2 x rule A's theta, adds money with low correlation to v1 (0.09),
  but it is flat in 2014-16 and not distinguishable from chance across the 16 cells (p 0.20).
- The strongest edge found in this project is still the 16:00 NY reversal (a fade, time-specific,
  about 40 events a year in the top 20%; edge map 2026-10-31). It was parked by the owner and was
  not tested here.
