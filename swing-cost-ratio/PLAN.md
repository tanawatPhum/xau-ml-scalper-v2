# Rules A + B: trade only when the swing is big relative to the spread (written before outcomes)

Owner 19:43 ICT, 31 Oct: "ทดสอบต่อ" after the summary of the best swing strategy (rules A + B).

## Why this is new
Every earlier factor test (swing-factors-b1, swing-rule-v1, swing-improve-v2) measured money in
today's dollars, where the $0.168 spread is 0.41 bps. At the time's prices the spread is 0.93-1.45
bps, about 3x larger relative to the move, and the yearly results follow gold's dollar volatility
(strong 2010-13 and 2020, weak 2014-19). So the size of the swing in dollars relative to the fixed
spread was never tested as a filter.

## Rules (frozen, unchanged)
A: theta = 1 x max(sigma60, sigma1440); B: theta = 1.5 x sigma60. Signal after a leg >= 2.5 theta,
fade, entry 1 minute late, exit at the next swing + 1 minute, stop 3 theta, flat before the break.
Money: mid at the time minus $0.168 per trade; 0.1 lot per rule; 33.77 THB/USD.

## Filters (both known at entry)
- Cost ratio R = theta in dollars at entry / $0.168 (theta$ = theta_bps x mid / 1e4).
  Threshold at the 0 / 20 / 40 / 60 / 80th percentile of R among that rule's 2010-16 trades.
- Leg ratio = leg before the signal / theta: >= 2.5 (base) / 3.5 / 5.
15 cells per rule.

## Selection (2010-2016 only)
- Per rule, the cell with the highest day-clustered t of net $/oz, with >= 0.5 trades/day.
- Random-subset null: 500 random subsets of the base trades of the same size (whole days kept
  together is not needed; trades drawn at random); p = share of subsets with t >= the cell's t.
  A filter counts as real only if p < 0.05 and it beats the base cell's t.
- Descriptive: gross / theta$ (edge in theta units) by R quintile; break-even theta$ where binned
  net crosses 0.

## Check 2017-2019 (once; semi-clean: the base rules were shaped on 2010-19 in today's $)
Pass for a rule = filtered net per trade > base and filtered t >= 2, and the A + B money table
(100,000 THB start) has a better total THB / max DD ratio than the base A + B.
Dukascopy's own spread reported as a stress reference. 2020-2022 stays sealed (exam only with
the owner's go-ahead); 2023+ closed.
