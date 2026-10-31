# Volatility-scaled bounce from the swing low (written before any outcome of this study)

Owner 12:44 ICT, 31 Oct: a fixed $5 bounce from the low cannot fit every market state; find a
mathematical (scale-free) bounce size with an edge, then convert it back to dollars.
Earlier owner rules: keep the swing line, add factors gradually; 2023+ closed until approved.

## Idea and units
- sigma60(t): typical 60-minute move = sqrt(60 x mean of the last 60 squared 1-minute log
  returns), using returns strictly before minute t, inside the current block (>= 30 returns,
  otherwise no signal). Same mid-close series as swing-structure (y = 1e4 ln mid, blocks split at
  gaps > 30 min).
- Bounce threshold theta(t) = k x sigma60(t). Dollar value at any moment = theta(t) in bps x
  price / 1e4 (reported in today's dollars, price 4083.276).
- Random-walk anchor: the mean time between reversals of size k x sigma60 is about k^2 x 60 min.
- k grid (fixed now): 0.25, 0.5, 0.75, 1, 1.5, 2, 3.

## Events and legs
- Adaptive zigzag: a swing low (high) is confirmed when y rises (falls) theta(t) from the running
  extreme. Event = confirmation minute. Events need a previous swing point in the same block.
- Leg before the bounce B = size of the leg that ended at the confirmed extreme; B_rel = B / theta
  at confirmation. Bins fixed now from random-walk theory (~39/38/22%): small < 1.5,
  mid 1.5-2.5, large >= 2.5. Cells = 7 k x 4 (all, small, mid, large) = 28.

## Trades (as swing-fade-exec)
- Fade = against the bounce; follow = with the bounce. Entry at the close one traded minute after
  the event; exit at the next event + 1 minute (or block end); stop (if any) = s x theta at the
  event, filled at the first minute close beyond it.
- Primary: delay 1, no stop. Risk check: stop 3 theta. Sensitivity: stop 2 theta, delay 2.
- Cost $0.168 per round trip (0.4114 bps).

## Data split (2023+ never read)
- Discovery 2010-2016, validation 2017-2019, holdout 2020-2022 SEALED for this line (opened once,
  later, for the final combined rule; not computed in this study's report).

## Pass rule per cell
1. Discovery: side = sign of mean gross fade P&L (fade if > 0, else follow); |day-clustered t of
   gross| >= 3; side net > 0.
2. Validation: same side, gross t >= 2, net > 0, net > 0 in >= 2 of 3 years.
3. Risk: the side with stop 3 theta has net > 0 in discovery and in validation.
4. Every day: >= 1 trade per trading day on average in validation.

## Reported, not used for the verdict
- Dollar size of theta per k (p10 / p50 / p90 at events), events per day.
- Fixed-$ comparison: same pipeline with theta fixed at the discovery median of k x sigma60.
- Sign-flip price null (1 draw per year): gross ~ 0. Day-level sign flips of trade P&L (20 draws):
  false passes of rules 1, 2 and 4.
- Win rate, average win / loss, worst trade for any passing cell.
