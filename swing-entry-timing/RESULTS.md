# Results: entry timing for rules A + B (locked filters), 31 Oct 2026
Plan PLAN.md (before outcomes). Code: code/bid2010.py (BID high/low 2010), sim.py, select_.py.
Money: 0.1 lot per rule, at the time's price, $0.168 spread, 33.77 THB/USD. Data 2010-16 only;
nothing qualified, so 2017-19 was not opened. 2020-22 sealed; 2023+ closed.
Reproduction: base trades and net identical to swing-cost-ratio (A 6,855 / B 6,414 signals;
kept by the locked filters A 4,477 / B 2,854).

## Verdict: no entry policy beats the current entry; nothing locked
Base 2010-16 (kept signals): A 3,857 trades, +267,245 THB; B 2,045 trades, +47,911 THB.
Family-wise null (500 day sign flips over 21 cells): best t p95 2.64 (A), 2.48 (B).

| Policy family | Rule A, total change vs base (2010-16) | Rule B |
|---|---|---|
| Limit at a better price, no fill = skip (9 cells) | -160k to -249k THB, t -2.8 to -5.9 | -48k to +31k, best t +0.85 (y 0.5, until exit) |
| Limit, then market after W minutes (6 cells) | -139k to -181k, t -4.0 to -7.9 | -46k to +22k, best t +0.80 |
| Wait for the bounce to stall (3 cells) | -116k to -300k, t -4.8 to -6.5 | -42k to -0.3k |
| Skip one session (3 cells) | skip Asia +3.8k (t 0.11); skip London / NY lose | skip NY +29k (t 0.86); others lose |

Per filled trade a limit can look better (A, limit +0.5 theta within 10 min: +$0.292/oz vs
+$0.205) but it fills only 14-57% of signals and misses the best trades, so total money falls.

## Why: the bounce has momentum once it extends
Bounce extension after the base entry (theta units, closes), 2010-16:
- A: 82% extend >= 0.1; 54% >= 0.5; 32% >= 1.0. Mean remaining extension 0.91 at 0, 1.03 at
  0.5, 1.07 at 1.0, 1.29 at 2.0.
- B: 55% >= 0.5; 32% >= 1.0; mean remaining 1.06 at 0, 1.27 at 0.5, 1.49 at 1.0, 2.10 at 2.0.
A random walk gives a flat mean remaining extension. Here it grows: a bounce that keeps going
tends to become a real reversal. The edge sits in the minutes right after the signal, so the
current immediate entry is already the best of the policies tested. Waiting for a better price
or a confirmation selects exactly the bounces that turn into losses.

## Leads (not tested)
- The growing extension points to a stop based on how far the bounce extends (for example
  1-1.5 theta, mainly for B). This is a stop change, which the owner parked earlier; ask first.
- More money without a new rule: B without its leg filter (descriptive, swing-cost-ratio) ends
  2010-19 at 524,829 THB vs 479,450, but max DD 102,426 vs 58,773.
