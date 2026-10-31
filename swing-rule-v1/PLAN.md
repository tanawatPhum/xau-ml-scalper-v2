# Swing rule variants v1: stop from the longer volatility, Asia filter (written before outcomes)

Owner 13:27 ICT, 31 Oct: test item 1 first. Data 2010-2019 only; 2020-2022 sealed; 2023+ closed.

## Honest status
- Both ideas come from swing-factors-b1, which looked at 2010-2019. The Asia filter was chosen
  because Asia lost in both periods there, so its 2010-2019 result is circular (in-sample). The
  stop idea came from stop RATES; its effect on P&L is not yet known, so it is a partial test.
- Only the sealed 2020-2022 holdout (one shot, owner decision) can test the accepted rule.

## Variants (bases: k = 1 and k = 1.5, fade after a leg >= 2.5 theta, entry/exit 1 minute late,
## cost $0.168; sigma_eff = max(sigma60, sigma1440), sigma1440 as in swing-factors-b1, falling back
## to sigma60 when sigma1440 is not available)
- V0 base: theta = k x sigma60, stop 3 theta (reproduces the bases).
- V1 stop from the longer scale: bounce and trailing exit from theta = k x sigma60; stop at
  3 x k x sigma_eff.
- V2 all from the longer scale: theta = k x sigma_eff for the bounce, the trailing exit, the
  large-leg test (B >= 2.5 theta) and the stop (3 theta).
- S (k = 1 only): no entries 00-07 UTC (07-14 Thai time), applied on top of V0, V1 and V2.

## Acceptance (fixed now)
- A component (V1 or V2 instead of V0; S on top) is accepted only if it raises BOTH mean net per
  trade AND net per trading day, in BOTH 2010-2016 and 2017-2019, versus the same rule without it.
  If V1 and V2 both qualify, the one with the higher 2010-2019 net per day is kept.
- The accepted rule per k is the candidate for the one-shot 2020-2022 test.

## Reported
- Per variant and period: trades per day, net per trade (day-clustered t), net per day, years > 0,
  stop rate, win rate, average win / loss, p1, worst trade, max drawdown per oz.
