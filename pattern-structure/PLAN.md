# Pattern structure of XAUUSD price paths (written before any outcome was computed)

Owner 10:37 ICT, 31 Oct: find the forms of randomness, split into groups with their occurrence
rates ("pattern structure"); then see which patterns can be played and which keep a profit
after the spread.

## Data
- Dukascopy XAUUSD M1 BID/ASK 2010-2022 (cache of `microstructure-edge-map`, both sides traded).
  2023+ protected, never read. mid = (bid + ask) / 2, forward-filled inside valid segments.
- S60 = 60-minute realized volatility of BID closes before a time point (>= 50 pairs).

## Building blocks
- Segment length L in {5, 10, 20} minutes, clock-aligned (UTC). A segment is valid when the
  prices at both ends exist (last traded minute within 2 minutes), >= 90% of its minutes traded,
  and S60 at its start exists.
- Segment move m = mid(end) - mid(start); unit sigma = S60(start) * sqrt(L/60).
- State: U if m >= +0.5 sigma, D if m <= -0.5 sigma, otherwise F (a Gaussian random walk would
  give about 31 / 38 / 31%). Secondary threshold 1.0 sigma (descriptive only).
- Pattern = states of 3 consecutive valid segments (window 3L = 15 / 30 / 60 minutes):
  27 patterns, code = 9*s1 + 3*s2 + s3.
- Families (exhaustive, mutually exclusive):
  QUIET FFF (1); IMPULSE exactly one U or D (6); TREND >= 2 moves, all the same direction
  (8: UUU UUF UFU FUU + mirrors); REVERSAL one direction change (10: UUD UDD DUU DDU UDF UFD FUD
  DUF DFU FDU); WHIPSAW two direction changes (2: UDU DUD).

## Part A - catalogue (descriptive)
- Share of each pattern and family: all years, 2010-2016, 2017-2022; 95% CI by day bootstrap.
- Random-order null: the 3L one-minute mid returns of each window permuted 10 times
  (same returns, same window total, same thresholds; only the order is random).
- A pattern/family is "structured" if real/null is outside [0.95, 1.05] in both periods in the
  same direction and the pooled CI excludes the null share.
- Transition view: P(next state | previous two states) vs the unconditional share.

## Part B - which patterns can be played (prefix -> next segment)
- At the end of segment 2 (time t) the prefix (s1, s2) is known; the trade is the next segment:
  enter at mid(t), exit at mid(t + L). Martingale null: E[m3 | prefix] = 0.
- Cells: prefix (9) x New York hour of t (24), per L; also pooled prefixes.
- Direction d = sign of the 2010-2016 mean; discovery 2010-2016 needs |t| >= 3 (clustered by
  UTC day); confirmation 2017-2022 needs d * t >= 2.
- Costs per trade: owner broker 0.411 bps of mid (about $0.05-0.07 at these prices) and the
  Dukascopy spread (mean of spreads at entry and exit).
- Playable (owner): non-random, confirmation gross edge d*E > owner cost, and net > 0 in at least
  4 of the 6 confirmation years. Same rule reported against the Dukascopy spread.
- Null: 20 day-level sign flips of m3, same pipeline; passing-cell counts reported.
- Positive control: prefixes ending exactly at 16:00 NY (the edge-map reversal) must show a
  reversal of the last segment's direction.
- Self-test: a synthetic Gaussian random walk on the real trading calendar through the same code
  must give real ~ null shares and no playable cell.
