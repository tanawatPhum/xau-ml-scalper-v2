# Swing strategy on Model B zones: peaks made by a B-zone rejection (written before any outcome)

Owner 17:23 ICT, 31 Oct: apply the swing strategy to the real project in a sandbox first. On the
1-minute chart, look for a clear prior peak formed by touching a Model B zone and bouncing back,
then the strategy's leg and bounce entry. Use the latest B (E68 A2, predictions from 2011);
test 2011-2019; report. (Owner data rules: 2020-2022 occasional exam, 2023-2026 locked.)

## Inputs (read-only)
- B zones: E68 A2 `SELECTED_ZONES.private.csv.gz` (delivered zones, 4 per session, $0.50 wide) and
  session windows [lock_minute, end_minute) (240 minutes) from `EVENTS.private.csv.gz`, status
  ISSUED, under C:\Users\ASUS\Documents\Codex\2026-10-30\task-6\deliverables\e68-a2-2011-2022.
- Prices: Dukascopy M1 2011-2019; mid closes for the strategy (as before); BID high/low/close for
  the zone touch (the owner's chart is BID).

## Strategy (frozen rules A and B, unchanged)
Rule A theta = 1 x max(sigma60, sigma1440); rule B theta = 1.5 x sigma60. A confirmed bounce of
theta after a leg >= 2.5 theta -> fade it at the close one minute later; exit when price moves back
theta from the best price (+1 minute); stop 3 theta; flat before the daily break.
Population: trades whose PEAK (the swing point where the leg started) and ENTRY are both inside the
same ISSUED B session window.

## Zone-peak condition (Z)
For a Sell (leg down from a swing high): over the peak minute +-2 minutes, the BID high reaches the
zone (high >= lower) and the BID close at the peak minute is at or below the zone top (close <=
upper), for at least one delivered zone of that session = touched and rejected. Buy mirrored
(low <= upper and close >= lower). N = the rest of the population.

## Variants for Z
- Z-3theta: current stop 3 theta.
- Z-peak: stop just beyond the peak = max(peak BID high, touched zone top) for a Sell (min(low,
  zone bottom) for a Buy), converted to mid, filled at the first minute close beyond it.

## Test (pre-registered)
- Primary: net per trade (USD/oz at the time's price, $0.168 spread) of Z-3theta minus N, rules A
  and B pooled, 2011-2019: day-clustered t >= 2, and the same sign in 2011-2016 and 2017-2019.
- Reported: Z alone (net, t, win, stop rate), Z-peak vs Z-3theta, each rule, per year money at
  0.1 lot (10 oz, USD/THB 33.77), trades per day, breakdown by zone side and global rank.
