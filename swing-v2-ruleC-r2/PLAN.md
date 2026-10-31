# Rule C search, round 2 (written before outcomes)

Owner 22:33 ICT, 31 Oct: continue the search for rule C.

## What earlier rounds established
- Round 1 (swing-v2-ruleC): 0 of 16 cells qualified.
- Every follow / momentum rule lost before costs.
- Following after a stop-out (swing-v1-stop-follow) was a coin flip.
- Only fades have shown an edge.
- The 16:00 NY reversal stays parked by the owner and is not tested here.

Round 2 tests two new fade families.

## Common rules
- **Base.** v1 Exness version (audit engine, flat at 16:55 NY, holiday closes, no entries until
  18:01 NY).
- **Execution.**
  - Every decision is made at a minute close; every fill is at the next minute's close
    (mid +/- $0.084).
  - No entries in blocked minutes; forced flat at the cutoff.
- **Costs and money.** $0.168 per trade, 0.1 lot, 33.77 THB/USD.
- **Positions.** One position at a time per cell.
- **Volatility.** The audit engine's volatility function (adjacent minutes, continuous across
  years).

## R1: fade the extended leg (12 cells)
The mirror of round 1's "ride the big leg", which lost before costs.
- **Trigger.** Using an adaptive zigzag (theta type A = 1 x max(sigma60, sigma1440), or type B
  = 1.5 x sigma60), the close moves m x theta(t) beyond the last confirmed swing extreme, while
  the leg is still running.
- **Entry.** Fade the leg at the next close. Only when theta$ at the trigger >= $2.1627.
- **Exit.** At the next swing confirmation (a pullback of theta(t) from the leg's extreme),
  filled at the next close.
- **Stop.** s x theta (theta at the trigger) against the entry, close-based, filled at the next
  close.
- **Grid.** type {A, B} x m {2.5, 3.5, 5} x s {2, 3}.

## R3: fade big moves into scheduled times (2 selectable cells)
- **Slots (local time, DST-aware).**
  - LBMA AM auction 10:30 London;
  - LBMA PM auction 15:00 London;
  - US data 08:30 New York;
  - US equity open 09:30 New York;
  - COMEX settlement 13:30 New York.
- **Trigger.** The move over the h minutes into the slot is in the top 20% of that slot's
  previous 250 moves (causal rolling threshold, at least 100 past moves).
- **Entry and exit.** Fade at the close one minute after the slot. Exit h minutes later, filled
  at the next close. No other stop.
- **Selectable cells.** All 5 slots pooled into one rule; h {15, 30}.
- **Descriptive only.** Per-slot results.

## Selection (2010-2016 only), as in round 1
A cell qualifies only when all of these hold:
- net per trade > 0 and day-clustered t >= 2;
- totals > 0 in both 2010-13 and 2014-16;
- >= 0.3 trades per day;
- v1 + C has a closed-trade total THB / max DD over 2010-16 that is >= v1's.

**Choice.** The qualifying cell with the largest v1 + C total.

**Family-wise null.** 500 day-level sign flips over the 14 selectable cells; report p for the
chosen cell.

## Check 2017-2019 (once, only if a cell qualifies)
- PASS = net > 0, t >= 2 and >= 2 of 3 years positive.
- PARTIAL = net > 0 and 2 of 3 years positive.
- Otherwise FAIL.
- 2020-22 is descriptive only; 2023+ stays closed.
