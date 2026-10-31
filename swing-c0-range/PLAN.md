# C0-style range formula for the swing strategy (written before any outcome)

Owner 17:06 ICT, 31 Oct: test the two uses of the C0 fixed range formula drawn at 17:03 - (1) is the
leg stretched beyond its normal range from the peak, (2) TP / SL from the forward x-minute range.
No ML. Data 2010-2019 only; 2020-2022 = occasional exam (not used); 2023-2026 locked.
Money: real price differences at the time, fixed $0.168 spread, 0.1 lot (10 oz), USD/THB 33.77.

## Base (frozen rules A and B)
Rule A theta = 1 x max(sigma60, sigma1440); rule B theta = 1.5 x sigma60; fade the confirmed bounce
after a leg >= 2.5 theta; entry at the close one minute after the signal; flat before the daily
break; one open position per rule.

## Formula (pure random-walk range, no fitting)
- Range scale over t minutes: s(t) = sigma x sqrt(t / 60) (sigma = typical 60-minute move, bps).
- Reflection principle: P(max excursion within t >= m) = 2 (1 - Phi(m / s(t))). Reached with
  probability ~50% at m = 0.674 s(t); ~10% at m = 1.645 s(t).

## Part 1 - stretch of the leg (entry question)
- z = leg size / s(T_leg), with sigma = sigma60 measured at the peak (before the leg) and T_leg =
  minutes from the peak to the low. Groups = terciles cut on 2010-2016 per rule.
- Outcome: net per trade of the current exit (E0). Test: best vs worst tercile of 2010-2016,
  |day-clustered t| >= 3, and in 2017-2019 the same direction with t >= 2 (2 tests). SL-hit rate
  per tercile reported.

## Part 2 - exits from the forward range (H = 80 minutes, the typical holding time)
s_H = sigma_eff x sqrt(80 / 60) at the signal minute (sigma_eff = max(sigma60, sigma1440)).
- E0 current: exit when price moves back theta from the best price (+1 minute), stop 3 theta.
- E1 C0 stop only: as E0 but stop at entry + 1.645 s_H (outside the 90% upper band).
- E2 C0 bracket, near TP: TP at entry - 0.674 s_H (~50% reach), stop at entry + 1.645 s_H, time
  exit at 80 minutes.
- E3 C0 bracket, far TP: TP at entry - 1.645 s_H (~10% reach), stop at entry + 1.645 s_H, time
  exit at 80 minutes.
TP / stop fill at the first minute close beyond the level; time exit at the close of the first
minute >= 80 minutes after entry; block end forces exit. Signals arriving while a position is
open are skipped.

## Acceptance (per rule, vs E0, in BOTH 2010-2016 and 2017-2019)
An exit variant is accepted if its total net (THB) is higher AND its max drawdown (THB, closed
trades) is lower than E0 in both periods. If several qualify, the one with the higher 2010-2019
total net is kept.

## Reported
Per rule x variant x period: trades/day, net per trade ($/oz at the time), total THB, max drawdown,
win rate, stop-hit rate and its share of all losses, worst trade.
