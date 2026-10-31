# Follow the trend after a v1 stop-out (written before outcomes)

Owner 22:24 ICT, 31 Oct: build a setup for the stopped trades (the group that is truly the wrong
direction): after the stop, trade with the move (follow), then report.

**Base.** Swing v1, Exness version (../swing-v1-flat-daily, mode EX):
- audit engine;
- flat at 16:55 NY and before holiday closes;
- 0.1 lot per rule; $0.168 spread.

**Trigger.** A v1 trade (rule A or B) exits by its 3-theta stop.

**Entry.** In the opposite direction to the stopped trade (with the move). The order is sent at
the stop close and filled at the same next-minute close that fills the stop.
- No entry if the fill minute is inside the daily cutoff window.
- One follow position per source rule at a time. Size 0.1 lot. theta = the stopped trade's theta.

**Exits** (checked at minute closes, filled at the next close; the daily cutoff closes
everything at 16:55 NY):

| Variant | Exit rule |
|---|---|
| E0 | Hold to the daily cutoff. |
| E1 | Trailing 1 theta from the best close since entry. |
| E2 | Trailing 2 theta. |
| E3 | Target +1 theta, stop -1 theta from entry. |
| E4 | Target +2 theta, stop -1 theta. |

**Money.** net = direction x (exit mid - entry mid) - $0.168; 10 oz; 33.77 THB/USD. Random-walk
reference: expected gross 0. For a bracket, the chance of reaching the target first is
stop / (stop + target).

**Selection on 2010-16.** Pick the variant with the highest day-clustered t of net. It counts
only if t >= 2 and the totals in 2010-13 and 2014-16 are both > 0.

**Check 2017-19, once.** PASS = net > 0, t >= 2 and >= 2 of 3 years positive; PARTIAL = net > 0
and 2 of 3 years positive; else FAIL.

**Other reporting.** 2020-22 is shown descriptively; those years were already used. 2023+ is
closed. Also reported: the v1 + follow money table, 2010-22.
