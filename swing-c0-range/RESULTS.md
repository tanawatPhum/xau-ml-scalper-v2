# C0-style range formula for the swing strategy: results (2026-10-31)

Plan `PLAN.md` (before outcomes). Code `code/c0test.py`. Output `out/C0TEST.txt`, `out/C0TEST.json`.
Data 2010-2019; money at the gold price of the time, $0.168 spread, 0.1 lot, USD/THB 33.77.
Base check: E0 totals (A +243,796 / +35,280; B +65,299 / +41,945 THB) add up to the 2010-2019 part
of the historical-price table (+386,319 THB).

## Part 1: leg stretch z = leg / (sigma60 at the peak x sqrt(leg minutes / 60)) - no effect
- Rule A: best (high z) vs worst (mid) t +1.0 / +0.5. Rule B: t +0.1 / +0.4. Not significant;
  stop rates do not separate either.

## Part 2: exits from the 80-minute forward range - none accepted
| Rule / exit | 2010-16 total THB, max DD | 2017-19 total THB, max DD | Stop rate | Stop share of losses |
|---|---|---|---|---|
| A E0 current | +243,796, 71,559 | +35,280, 44,672 | 5% | 44% |
| A E1 C0 stop 1.645 s_H | +170,471, 97,322 | +20,320, 50,049 | 13% | 72% |
| A E2 TP 0.674 / SL 1.645 / 80 min | +23,598, 84,699 | -8,889, 47,786 | 6% | 36% |
| A E3 TP 1.645 / SL 1.645 / 80 min | +3,624, 93,571 | +10,016, 30,964 | 7% | 36% |
| B E0 current | +65,299, 74,241 | +41,945, 31,819 | 7% | 50% |
| B E1 | +47,571, 84,730 | +22,336, 39,244 | 14% | 74% |
| B E2 | -67,300, 96,749 | +25,694, 26,665 | 4% | 30% |
| B E3 | -72,793, 100,815 | +7,120, 27,738 | 5% | 30% |

## Reading
- The C0 stop "outside the 90% band" (about 1.9 sigma) is tighter than the current 3 theta: twice
  the stops and lower profit, again showing that tighter stops cut the edge.
- Fixed TP from the range (50% or 10% reach) with an 80-minute time exit loses most of the edge:
  the current trailing exit (close when price moves back theta) is better.
- The pure random-walk range describes size, not direction; it does not separate true bottoms.
