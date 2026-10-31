# Results: rules A + B, trade only when the swing is big relative to the spread (31 Oct 2026)
Plan PLAN.md (before outcomes). Code: code/build.py, grid.py (2010-16, writes out/LOCK.json),
check.py (2017-19, once); descriptive after the check: variant_a_only.py. Money: 0.1 lot per rule,
at the time's price, $0.168 spread, 33.77 THB/USD. 2020-22 sealed; 2023+ closed.
Reproduction: 2017-19 trades A 2034 / B 1791, same as the frozen rules.

## 2010-16 (selection)
- Rule A: dropping trades with theta < $2.16 (the lowest 20% of the cost ratio) raises net from
  +$0.150 to +$0.205/oz (t 2.95 -> 3.36), with 2.1 instead of 2.7 trades/day and more money
  (+267k vs +244k THB). Random-subset null p 0.068: borderline, below the plan's bar.
- Rule B: no cell helps (best: leg >= 3.5 theta, t 0.90 vs base 0.79, p 0.33). At the time's
  price, B is weak in 2010-16 (+$0.042/oz, t 0.79).
- Edge in theta units by cost-ratio quintile: A 0.045 / 0.117 / 0.104 / 0.059 / 0.118, so only
  the smallest swings are bad; B 0.150 / 0.136 / 0.031 / 0.061 / 0.042, falling with size.

## 2017-19 check (once)
| | Base | Locked filter |
|---|---|---|
| A | 2,034 trades, +$0.051 (t 1.05), +35,280 THB | 620 (0.8/day), +$0.240 (t 2.23), +50,341 THB: PASS |
| B | 1,791, +$0.069 (t 1.35), +41,945 THB | 809, +$0.051 (t 0.67), +13,953 THB: FAIL |
| A + B | +77,224 THB, DD 73,476 | +64,294 THB, DD 31,291: return/DD 2.05 vs 1.05, PASS |

Money table, 100,000 THB start, 2010-19: base ends 486,319 (max DD 126,314); locked ends 479,450
(max DD 58,773). Dukascopy-spread stress: base -469,676, locked -87,822 (still a loss).

## Descriptive: A filtered + B unfiltered (not pre-registered)
2010-19 ends 524,829 (max DD 102,426); 2017-19 +92,285 THB, DD 43,131.

## Reading
Removing rule A's smallest swings (theta < about $2.2, where the spread eats the move) keeps the
money and halves the drawdown. The 2010-16 support is borderline (p 0.068), and 2017-19 is only
semi-clean (the base rules were shaped on 2010-19 in today's dollars). B's filter does not work.
The honest next check is the one-shot 2020-22 exam, with the owner's go-ahead.
