# Results: SELL on the bounce after a zone-to-zone run down (PLAN v2)
31 Oct 2026. Ratios searched on 2011-16 (answer key), locked automatically (out/LOCK.json,
17:50 ICT), 2017-19 run once. Money: 0.1 lot, at the time's price, $0.168 spread, 33.77 THB/USD.
Code: code/common.py (state machine), grid.py, test1719.py; descriptive after the lock:
example_days.py, owner_scale.py. code/oracle.py is the superseded v1 draft (never finished).

## 2011-16: 180 ratio cells, 4,393 sessions
- No cell beats the spread with confidence: best day-clustered t +1.12; on 5 bar-shuffled copies
  the best cell reached t +0.37 / +1.82 / +0.03 / +0.25 / -0.20. 68 of 148 eligible cells lose
  with t <= -2. Verdict per PLAN: no edge found.
- Small real tendency: mean gross over cells +$0.078/oz (shuffled copies -0.04 to +0.06). Price
  after the bounce continues slightly more than chance, but less than half the spread.
- Owner scale (run >= 1.5u, about $2-3; TP = re-test of the trough): 1.5-3 trades/day, gross
  -0.01 to +0.02 (random-walk-like), net about -$0.15/oz (t -4 to -11), roughly -30,000 THB/yr.
- Zones do not help. Tolerance $0.50: 74% of setups count as zone; zone trades -0.120 vs
  non-zone +0.022 averaged over cells; 0 cells where zone is better with t >= 2, 7 cells where it
  is worse with t <= -2. Exact touch (tol 0): 26% of setups; no significant difference.
- Ratio map (best rho/m/s): bounce 23.6% loses in every TP choice; 38-62% is positive but not
  significant. Bigger runs do better, since the spread is fixed while the move grows.
- Locked automatically: peak reversal 0.5u, run >= 4u, sell at a 38.2% bounce, TP 25% of the run
  above the trough, SL 25% of the run above the peak; filter "not at a zone" (t 2.73, both halves
  positive, n 64). Cell: 324 trades (0.21/day), net +$0.106/oz, +11,636 THB over 6 years; years
  +4,704 / +2,103 / +1,220 / +9,156 / -1,830 / -3,717.

## 2017-19 blind test (once)
- Locked (cell + not-at-zone): 7 trades in 3 years, +1,882 THB, t 1.80. FAIL (too few to judge).
- Cell without the filter: 160 trades (0.21/day), net +$0.175/oz (t 2.15), gross +0.343;
  TP 64%, SL 1%, session end 35%; +9,453 THB, max DD 2,731; years +273 / +3,283 / +5,898.
  Not the locked rule, and the 2011-16 support was weak, so this is a lead, not a result.
- 2011-19 for the cell: 484 trades, about +$0.13/oz = +44 THB per trade, about 2,300 THB/yr.

## Owner's 2017 London examples (descriptive)
At run >= 1.5u the machine trades all four: 01-18 TP +1.11, 01-24 TP +0.62, 01-20 session end
-0.02, 01-23 session end -1.81 (the owner's losing day). The locked cell (run >= 4u) takes none.
The machine sees the pattern the owner draws; over 6 years at that scale it loses the spread.

## Reading
The drawn pattern at its drawn size behaves like a random walk after the bounce: gross 0, so the
spread decides. A small edge appears only for long runs (>= 4u, about $5-9) and is worth about
44 THB per trade at 0.1 lot. B zones add nothing in this form. 2017-19 has now been used once.
