# Swing v2: search for a rule C to add to v1 (A + B) (written before outcomes)

Owner 20:36 ICT, 31 Oct: develop version 2 by finding a playing rule C.
v1 (swing-v1/SPEC.md) stays frozen; C is a separate rule at 0.1 lot with one position at a time.
Money: mid at the time, $0.168 per trade, 10 oz, 33.77 THB/USD. Every C family also uses the v1
cost lesson: trade only when its theta at entry >= $2.1627.
Years: 2010-16 select; 2017-19 check once; 2020-22 not used (spent on the v1 exam); 2023+ closed.
Not included: the 16:00 NY reversal (parked by the owner), session-direction rules (the edge map
found session direction random).

## Candidate families (16 cells)
Theta definitions: s60 = sigma60, eff = max(sigma60, sigma1440), d = sigma1440 (all from
swing_v1.py, unchanged).
- **CS: slower-scale fade** = the v1 mechanics (signal after a leg >= 2.5 theta, fade at the next
  close, exit at the next swing + 1 minute, stop 3 theta) with a bigger theta:
  2 x eff, 3 x eff, 1.5 x d, 2 x d. 4 cells.
- **CL: ride the big leg** = follow the leg once it reaches m x theta from the last swing extreme
  (enter at the next close), exit at the next swing confirmation + 1 minute (the point where
  v1 would fade), stop 3 theta. Theta 1 x eff (A's) or 1.5 x s60 (B's); m {2.0, 2.5, 3.5}.
  6 cells.
- **CF: follow a failing v1 fade** = after a v1 trade of rule A (or B), when price has gone
  x x theta against it (close), enter the other way at the next close; exit when the close
  retraces 1 theta (the signal's theta, fixed) from the best close since entry (next close), or
  at the block end; stop: back to the v1 entry price (x theta). Source {A, B}; x {1.0, 1.5}. 4 cells.
- **CP: 240-minute breakout** = a close above the highest (below the lowest) close of the
  previous 240 traded minutes in the block; follow at the next close; exit when the close
  retraces f x theta (1 x eff at entry, fixed) from the best close (next close); stop 3 theta.
  f {1, 2}. 2 cells.

## Selection (2010-2016 only, automatic, written to out/LOCK.json)
A cell qualifies when all hold:
1. Standalone: net per trade > 0, day-clustered t >= 2, total > 0 in 2010-13 and in 2014-16,
   and >= 0.3 trades per day.
2. Portfolio: v1 + C (100,000 THB start in 2010, ordered by exit time) has total THB / max DD over
   2010-16 >= that of v1 alone.
Pick the qualifying cell with the largest portfolio total THB over 2010-16. Family-wise null:
500 day-level sign flips of each cell's daily P&L, the same signs for all cells; report p for the
chosen cell's t (real if p < 0.05). Also reported: overlap with v1 (same side, entry within 10
minutes of an A or B entry) and the daily P&L correlation with v1.

## Check 2017-2019 (once)
C standalone: PASS = net > 0 with t >= 2 and >= 2 of 3 years positive; PARTIAL = net > 0 and
2 of 3 years positive; else FAIL. v2 = v1 + C money table 2010-19 vs v1 (end, max DD).
If nothing qualifies on 2010-16, 2017-19 is not opened.
