# Swing (market-structure) patterns at the $1-10 scalping scale (written before any outcome)

Owner 10:53 ICT, 31 Oct: look at bigger patterns; scalping trades $1-10 moves, and small
patterns mostly do not pay the spread.

## Units
- Price series y = 1e4 * ln(mid), mid = (bid close + ask close)/2, Dukascopy M1 2010-2022
  (edge-map cache; 2023+ never read). Only minutes where both sides traded.
- "Today's dollars": bps x 4083.276 / 1e4 (the owner's quote 4083.192/4083.360). Thresholds
  theta = $1, $2, $3, $5, $10 today = 2.449 / 4.898 / 7.347 / 12.245 / 24.490 bps.
- Cost per round trip: owner's broker $0.168 today = 0.411 bps.
- Trading blocks: runs of traded minutes with gaps <= 30 minutes (daily break and weekends
  split blocks); swings and trades never cross a block boundary (forced exit at block end).

## Swings and patterns
- Directional-change zigzag on minute closes: a swing high (low) is confirmed when y falls
  (rises) theta below (above) the running extreme; the confirmation minute is the event.
- At each event k (new move direction d), with the last four swing points s_{k-3..k}:
  B = d (s_{k-1} - s_k) (the pullback just finished), A = d (s_{k-1} - s_{k-2}) (the prior leg in
  direction d), C = d (s_{k-3} - s_{k-2}). a = A / C, b = B / A.
- 8 patterns (direction-symmetric):
  0 TREND shallow (a > 1, b < 0.5)   1 TREND deep (a > 1, 0.5 <= b < 1)      [HH + HL]
  2 CONTRACT shallow (a <= 1, b < 0.5) 3 CONTRACT deep (a <= 1, 0.5 <= b < 1) [LH + HL]
  4 COUNTER mild (a <= 1, 1 <= b < 1.5) 5 COUNTER deep (a <= 1, b >= 1.5)     [LH + LL]
  6 EXPAND mild (a > 1, 1 <= b < 1.5) 7 EXPAND deep (a > 1, b >= 1.5)          [HH + LL]
  (named for a new up move; mirrored for down moves). Random-walk theory with i.i.d. legs:
  TREND 1/3, COUNTER 1/3, CONTRACT 1/6, EXPAND 1/6.

## Trades at each event (entry at the event close, all fills on minute closes)
- R1 follow with trailing stop theta: hold in direction d until the next event (or block end).
- R3 symmetric bracket: exit at the first close >= +theta or <= -theta from entry, max 240 min.
- Fade = opposite side: gross P&L is the negative of R1 / R3 (symmetric rules).
- Under any martingale price the expected gross P&L of every rule is exactly 0.

## Nulls and checks
- Sign-flip price null: per block, minute log-returns keep their size and timing, signs are
  randomized; same pipeline (5 draws) -> null pattern shares and P&L.
- Self-test: synthetic Gaussian random walk on the 2017 calendar -> shares ~ theory, P&L ~ 0.

## Playability (cells = pattern 8 x rule 2 x theta 5 = 80, plus pooled rule x theta = 10)
- Direction (follow or fade) from the 2010-2016 sign of the mean gross P&L.
- Discovery 2010-2016: |t| >= 3 (clustered by UTC day). Confirmation 2017-2022: same sign, t >= 2.
- Playable: non-random, confirmation mean net (after $0.168) > 0, and net > 0 in >= 4 of 6
  confirmation years. Robust: still playable with events confirmed 15:45-16:30 New York removed.
- 20 day-level sign flips of trade P&L give the false-pass count.
- Reported per cell: share, trades per year, gross and net in today's $, win rate, per-year net.
