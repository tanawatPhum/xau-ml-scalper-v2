# Fact-check of the ChatGPT audit of swing v1 (31 Oct 2026, owner 21:54)
Audit: ../swing-causal-execution (another session; not modified). Check: attrib.py re-runs the frozen
v1 code with each audit correction switched on alone, then all together, 2010-2019, fixed $0.168
spread, 0.1 lot per rule. Output out/ATTRIBUTION_2010_2019.csv.

## Are the audit's points true? Yes, all are real properties of the v1 simulator
| # | Audit point | In v1 code? | Effect on 2010-19 THB (alone) |
|---|---|---|---|
| 1 | theta$ filter uses the entry-minute price (1 minute ahead) | yes: `th * mid[ent]` | -895 (1 trade) |
| 2 | entry at the next available minute even if minutes are missing | yes: `ent = idx + 1` | -513 (32 trades) |
| 3 | close-based stop exits at the same close it was seen on | yes: `apply_stop` returns that close | -5,008 |
| 4 | position closed before a >30-min gap (knows the gap is coming) | yes: exit at the block's last minute | +4,240 (DD +6k) |
| 5 | volatility counts a return across missing minutes as a 1-minute return | yes: `diff(y)` over traded minutes | -18,936 (mostly B) |
| 6 | long volatility restarts each 1 January (years loaded separately) | yes | not re-run here (tiny) |
| 7 | drawdown measured on closed trades only, open positions ignored | yes (reporting) | DD only |

All five together: +352,244 THB (v1 +379,450), 7,304 trades, max DD 67,794. The audit engine:
+359,209 THB, 7,305 trades, DD 67,084. The independent re-run agrees with the audit within about 2%.
The remaining gap is mainly point 6, plus small engine details.

## What it means
- **Genuine errors:** points 1, 3 and 5 are modelling errors. Point 5 is the only one that
  matters (about -5% over 10 years).
- **Defensible choices:** points 2 and 4 can be argued either way. A broker fills at the next
  tick, and daily breaks are scheduled.
- **Corrected numbers (audit):**
  - 2010-19: +359,209 THB.
  - 2020-22: +154,150 THB (v1 reported +126,420), t 1.84.
  - 2010-22 continuous: ends at 613,360 THB (v1 605,870).
  - Max DD including open positions: 68,463 THB (v1 58,773 on closed trades).
- **Conclusions unchanged:**
  - Profitable at a $0.168 spread.
  - Loses with Dukascopy's own spread.
  - 2020-22 is still PARTIAL (t < 2).
  - The edge per trade is thin.
- Every earlier sandbox comparison used the v1 simulator, so they share these small biases.
  Relative comparisons (filters, entry timing, stops, timeframes) are unaffected in direction.
