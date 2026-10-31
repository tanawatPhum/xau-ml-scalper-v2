# Results: stop at s x theta from the entry, rules A + B (locked filters), 31 Oct 2026
Plan PLAN.md (before outcomes). Code: code/stops.py, select_.py. Money: 0.1 lot per rule, at the
time's price, $0.168 spread, 33.77 THB/USD. 2010-16 only: nothing qualified, so 2017-19 was not
opened and the intrabar sensitivity was not needed. 2020-22 sealed; 2023+ closed.
Reproduction: the 3 theta cell equals the base exactly (A 6,855 / B 6,414 signals).

## Verdict: every tighter stop loses money; keep 3 theta (out/LOCK.json)
| Stop | A total THB 2010-16 (change, t) | A stopped | B total THB (change, t) | B stopped |
|---|---|---|---|---|
| 3.0 (base) | +267,245 | 4.7% | +47,911 | 6.6% |
| 2.5 | +249,166 (-18,080, t -1.1) | 7.1% | +34,140 (-13,770, t -1.1) | 8.9% |
| 2.0 | +226,247 (-40,999, t -1.5) | 11.2% | +224 (-47,687, t -2.4) | 13.1% |
| 1.5 | +182,321 (-84,925, t -2.3) | 18.3% | -47,261 (-95,171, t -3.8) | 20.2% |
| 1.25 | +98,272 (-168,973, t -3.9) | 24.4% | -38,701 (-86,612, t -3.3) | 24.2% |
| 1.0 | +41,178 (-226,067, t -4.5) | 31.9% | -87,937 (-135,847, t -4.3) | 32.3% |
Both halves (2010-13, 2014-16) lose for every cell. Win rate falls as the stop tightens
(B 61% -> 54% at 1 theta): many trades that go 1-2 theta against the entry still end positive.

## Why the extension data misled
The trailing exit is not fixed at entry: the next swing needs a drop of theta measured at that
moment, and theta grows when a bounce extends with rising volatility, so an extended trade can
still exit at a profit. A fixed stop cuts those trades. The current exit plus 3 theta stop is
better than any tighter stop tested.

## Leads (not tested)
- Wider stop (4-5 theta or none): the trend points that way; swing-adaptive-bounce saw more
  money without a stop in today's dollars, with a much worse worst trade (-74 vs -34 $/oz).
- B without its leg filter: more money with more drawdown (descriptive, swing-cost-ratio).
