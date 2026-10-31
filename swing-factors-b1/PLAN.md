# Swing factors, batch 1 (written before any outcome of this batch)

Owner 13:19 ICT, 31 Oct: stay with the swing strategy and improve it step by step; fixed rules
miss cases where TP should run further or SL should come earlier. Data 2010-2019 only;
holdout 2020-2022 stays sealed until a final rule exists; 2023+ closed.

## Base (from swing-adaptive-bounce, unchanged)
- Bounce threshold theta = k x sigma60, k = 1 and k = 1.5 (two bases, analysed separately).
- Events: confirmed bounce with leg before it B >= 2.5 theta ("large leg"); fade side.
- Main trade: entry 1 minute after the event, exit at the next swing confirmation + 1 minute,
  stop 3 theta (minute close), cost $0.168. Must reproduce the adaptive-bounce stop-3 numbers.

## Outcomes per trade (today's $ per oz)
- O1 net: main trade net (entry filter question).
- O2 extension: if the main trade ended by its signal (not stop, not block end), the gross P&L of
  holding on from the main exit to the following swing confirmation + 1 minute (no extra cost);
  else 0. O1 + O2 = "let TP run one more swing" (TP question).
- O3 stop: main trade hit the 3 theta stop (SL question; reported only).

## Factors (known at the event minute; groups fixed now, tercile cut points from 2010-2016)
1. legsize: B / theta (terciles within the base).
2. legtime: minutes from the previous swing point to the low (high) (terciles).
3. bouncetime: minutes from the low (high) to the confirmation (terciles).
4. volratio: sigma60 / sigma1440 (sigma1440 = same formula over the last 1440 traded minutes,
   >= 720 returns, scaled to 60 minutes) (terciles).
5. session of entry (UTC): Asia 00-07, London 07-13, New York 13-21, late 21-24.
6. htf: direction of the last confirmed k = 3 swing in the block vs the fade side: with / against
   (events without a k = 3 swing yet are left out of this factor).
7. rangepos: position of the price in the last-1440-minute close range, oriented so that 0 = at
   the extreme the leg ran to (terciles; >= 720 minutes of history).
8. structure: family of the last three legs (TREND, CONTRACT, COUNTER, EXPAND as in
   swing-structure; events without three legs left out).

## Test (per base k, factor, outcome O1 and O2: 2 x 8 x 2 = 32 tests)
- Group means with day-clustered standard errors. In 2010-2016 take the best and the worst group;
  the factor matters if |t of the difference| >= 3 in 2010-2016 and, in 2017-2019, the same two
  groups differ in the same direction with t >= 2.
- Null: 20 shuffles of the factor labels within each year; count false "matters" over 32 tests.
- Reported: per group n, O1, O1 + O2, O3, in both periods.
- Nothing here changes a trading rule yet: factors that matter go into a later, pre-registered
  combination step (built on 2010-2019, tested once on 2020-2022).
