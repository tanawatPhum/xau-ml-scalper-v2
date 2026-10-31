# Rules A + B: better entry timing, same rules, same 0.1 lot (written before outcomes)

Owner 19:57 ICT, 31 Oct: develop A and B further; the max DD is fine now; look for entry timing
that makes more profit; no rule C; keep 0.1 lot per rule.

## Base (unchanged)
The locked portfolio from swing-cost-ratio: A (theta = 1 x max(sigma60, sigma1440)) only when
theta >= $2.16 (R >= 12.873); B (theta = 1.5 x sigma60) only when the leg >= 3.5 theta. Signal,
exit (next swing confirmation + 1 minute) and stop (3 theta from the fill, at a minute close) stay
as they are. One position per rule; money = mid at the time, $0.168 per trade, 10 oz, 33.77.
Base entry = close of the minute after the signal (E0).

## Entry policies tested (per rule, on every base signal)
- L(y, W): instead of the market, a limit at E0 + y x theta$ for a SELL (E0 - y x theta$ for a
  BUY), live for W minutes after E0 or until 2 minutes before the exit; fill when the minute's mid
  high (low) trades $0.05 through the limit; no fill = no trade. y {0.1, 0.25, 0.5};
  W {10, 30, until exit}. 9 cells.
- LF(y, W): the same, but if not filled after W minutes, enter at the market close then (if the
  exit has not come). y {0.1, 0.25, 0.5}; W {10, 30}. 6 cells.
- D(z): wait for the bounce to stall: the first close z x theta$ back from the running extreme
  since E0 (in the trade's direction), enter at the next close. z {0.1, 0.25, 0.5}. 3 cells.
- S(x): skip signals whose base entry falls in session x (UTC hour: Asia 23-06, London 07-12,
  New York 13-22). 3 cells.
Mid high/low = Dukascopy BID high/low + half the minute's closing spread.

## Measure and selection (2010-2016 only)
- Paired gain per signal: delta = policy P&L - base P&L (0 if the policy takes no trade).
  Day-clustered t of the mean delta; total delta in THB.
- A cell is a candidate when t(delta) >= 2 and total delta > 0 in both 2010-13 and 2014-16.
- Family-wise null: 500 day-level sign flips of delta applied to all 21 cells at once; p = share of
  flips whose best t >= the real best t.
- Per rule pick at most one timing cell (L / LF / D, largest total delta among candidates) and at
  most one session cell (same rule); both together if both qualify. Written to out/LOCK.json.
- Descriptive: bounce extension after E0 in theta units (survival and mean remaining extension;
  a random walk gives a flat mean remaining extension).

## Check 2017-2019 (once)
Per rule: PASS = total delta > 0 with t >= 2 and delta > 0 in at least 2 of 3 years; PARTIAL =
delta > 0 in total and 2 of 3 years but t < 2; else FAIL. A + B money table 2010-19 from
100,000 THB with base vs locked entries (end capital, max DD). 2020-22 sealed; 2023+ closed.
