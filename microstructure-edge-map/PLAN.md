# Microstructure edge map, steps 0-1 (written before any outcome was computed)

Owner 10:13-10:18 ICT, 31 Oct: study where XAUUSD is random and where it carries an edge that
is predictable or computable for scalping; start with the edge map.

## Data
- Dukascopy XAUUSD M1 BID and ASK CSV, `D:\xau-ml-scalper\data\raw\dukascopy\xauusd\m1\csv`,
  2010-2022 only (2023+ protected, never read).
- A minute is used only when both sides traded (volume > 0 or high > low on each side).
- mid = (bid close + ask close) / 2; spread = ask close - bid close.
- S60 = 60-minute realized volatility of BID closes (consecutive traded minutes), as in the
  anytime-range study. Volatility terciles: cut points from 2010-2016 only.
- Time of day: New York local hour (DST-aware), which tracks the US session and data releases.

## Step 0 - cost map (descriptive)
- Spread in USD and in bps of mid, by year, by NY half-hour slot, by weekday, by S60 tercile:
  median and p90.
- Reference cost of the owner's broker: $0.168 at mid 4083.276 = 0.411 bps, i.e. scaled to the
  price of the day (about $0.05-0.08 at 2010-2022 prices).

## Step 1 - random-walk deviation scan
- Horizons h = 1, 5, 15, 30, 60 minutes. Non-overlapping clock-aligned blocks (UTC); a block
  boundary t is used when [t-h, t+h) has >= 90% traded minutes and mid exists at t-h, t, t+h
  (nearest traded minute at or before each point, within 2 minutes).
- r_prev = mid(t) - mid(t-h), r_next = mid(t+h) - mid(t).
- Cells: h x NY hour (24) x S60 tercile (3) = 360 cells, plus pooled rows per h and per h x hour.
- Per cell and period:
  (a) rho = corr(r_prev, r_next).
  (b) Strong-move edge E = mean(sign(r_prev) * r_next) over |r_prev| >= the cell's 80th
      percentile (threshold fixed on 2010-2016). E > 0 momentum, E < 0 reversal, in USD.
  (c) t-statistic of E clustered by trading day (daily sums of signed outcomes / daily counts).
  (d) Cost: median spread at t in the cell (Dukascopy) and the owner-broker reference.
- Secondary: jump bucket |z| >= 2.5 with z = r_prev / (S60 * sqrt(h/60)), per h x hour.

## Decision rules (fixed now)
- Discovery 2010-2016, confirmation 2017-2022, each period read once.
- Non-random cell: |t_disc| >= 3 and the confirmation edge has the same sign with
  t_conf >= 2 in that direction.
- Tradable cell: non-random and the confirmation edge in the discovered direction exceeds the
  cell's median Dukascopy spread (and, reported separately, the owner-broker reference).
- Null: 20 sign-flip permutations (the sign of r_prev flipped per trading day at random),
  same pipeline; the count of passing cells under the null is reported next to the real count.
- Nothing here is a strategy. Passing cells become step-2 hypotheses only.
