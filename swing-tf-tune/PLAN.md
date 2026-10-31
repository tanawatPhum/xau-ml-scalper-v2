# Swing setup re-tuned for 5m / 15m / 30m / 1h (written before outcomes)

Owner 21:49 ICT, 31 Oct: the v1 values were found on 1-minute data, so running them on other
timeframes is not fair; find values that suit each timeframe with the same swing setup.

## Fixed (the v1 setup)
- Swings, signals and stops are read on the TF bar closes (bars on the clock, split at blocks).
- Signal: a swing confirmed after a leg >= 2.5 theta (and >= the cell's leg minimum); fade.
- Entry and exit at the M1 close one minute after the signal bar closes. Exit at the next swing.
- Stop 3 theta at TF closes. Trade only when theta at entry >= $2.1627.
- One position per rule; 0.1 lot; mid at the time; $0.168; 33.77 THB/USD.
- Theta = k x the v1 volatility measure (time-based, from M1):
  - type A: max(sigma60, sigma1440);
  - type B: sigma60.

## Tuned per TF (20 cells per TF)
- k: 0.5, 0.75, 1, 1.5, 2.
- Type: A or B.
- Leg minimum: 2.5 or 3.5 theta.

## Selection (2010-2016 only)
- For each TF and each type, a cell qualifies when net > 0, day-clustered t >= 2, the totals
  in 2010-13 and 2014-16 are both > 0, and it trades >= 0.3 times a day.
- Per type, pick the qualifying cell with the highest t. The TF's rule set is the chosen type-A
  cell plus the chosen type-B cell (or the one that exists).
- Family-wise null per TF: 500 day-level sign flips over its 20 cells.
- Written to out/LOCK.json before 2017-19 is read.

## Check 2017-2019 (once)
- Per TF rule set: PASS = net > 0, t >= 2 and >= 2 of 3 years positive; PARTIAL = net > 0 and
  2 of 3 years; else FAIL.
- Compare with v1 on 1m over the same years: +64,294 THB, max DD 31,291.
- Money table 2010-19, 100,000 THB start.
- 2020-22 not used (the v1 timeframe run already looked at it); 2023+ closed.
