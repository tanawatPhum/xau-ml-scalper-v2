# Swing improvement v2: volume / spread factors and drawdown control (written before outcomes)

Owner 13:54 ICT, 31 Oct: run the next improvement test (batch 2: tick volume and spread at the
bounce) and check whether max drawdown can be brought down. Data 2010-2019 only; 2020-2022
sealed; 2023+ closed. Everything here is in-sample for 2010-2016 and a repeated-use check for
2017-2019; only the sealed holdout can confirm.

## Bases (from swing-rule-v1, unchanged)
- Rule A: theta = 1 x sigma_eff (max of sigma60, sigma1440) for bounce, trailing exit, large-leg
  test (B >= 2.5 theta) and stop 3 theta. Rule B: theta = 1.5 x sigma60, same structure.
- Fade, entry and exit 1 minute late, cost $0.168, positions closed before the daily break.

## Part 1: batch-2 factors (entry filter and TP question)
Volume = Dukascopy bid + ask tick volume per minute (relative use only); spread = Dukascopy
ask - bid in bps (a liquidity / news proxy, not the owner's cost). All windows end at the event
minute. Groups = terciles cut on 2010-2016.
1. vol_bounce_leg: mean volume per minute during the bounce / during the leg before it.
2. vol_bounce_day: mean volume per minute during the bounce / over the last 1440 traded minutes.
3. vol_climax: mean volume per minute in the 5 minutes ending at the extreme / during the leg.
4. spread_rel: spread at the event minute / median spread of the last 1440 traded minutes.
Outcomes O1 (net, main trade) and O2 (extension to the next swing), O3 stop rate reported.
Test as swing-factors-b1: best vs worst group of 2010-2016, |t| >= 3 there and t >= 2 in the
same direction in 2017-2019; 2 bases x 4 factors x 2 outcomes = 16 tests; 20 label shuffles.

## Part 2: drawdown controls (each applied alone, per rule)
- R0 baseline: 1 oz per trade.
- R1 volatility sizing: size = c / theta$ at the event, capped at 3 oz; c set so the mean size
  over 2010-2016 is 1 oz (each trade risks about the same dollars).
- R2 daily brake: after 2 losing trades of the rule in the same trading day, no more entries that
  day.
- R3 equity filter: enter only if the sum of the rule's last 50 closed trades (all signals,
  tracked even when skipped) is >= 0.
- R4 portfolio: rules A and B together at 0.5 oz each (compared with A alone and B alone).
Metrics per period (2010-2016, 2017-2019): net per day, max drawdown (per oz-equivalent), Calmar =
annual net / max drawdown, worst month, longest time under water, share of positive months.
Acceptance: a control is accepted for a rule if Calmar improves in both periods AND max drawdown
falls in both periods. Accepted controls are then applied together and reported (no new
selection). Results are also shown for 100,000 THB at 0.01 lot (USD/THB 33.77).
