# Swing v1 (frozen 31 Oct 2026, owner 20:25 ICT)

The best swing version so far, frozen as version 1. Sandbox only: not in the main project, not
live, no real orders. Reference code: code/swing_v1.py (self-contained; reproduces the numbers
below). Built from: swing-adaptive-bounce -> swing-rule-v1 -> swing-holdout-2020-22 ->
swing-cost-ratio. Tests that did not change v1: swing-entry-timing (entry), swing-ext-stop (stop),
swing-c0-range, swing-factors-b1, swing-improve-v2, swing-ml-wf.

## Data and units
- 1-minute mid closes, (bid + ask) / 2, minutes with data only.
- A gap > 30 minutes starts a new block. No position is held across a block (flat before the
  daily break and the weekend).
- y = 1e4 x ln(mid), so distances are in bps.
- sigma60 = sqrt(60 x mean squared 1-minute return), over the last <= 60 returns strictly before
  the minute, inside the block (>= 30 returns).
- sigma1440 = the same over the last 1440 traded minutes (>= 720 returns), scaled to 60 minutes.

## Two rules, the same mechanics, different theta

| | Rule A | Rule B |
|---|---|---|
| theta | 1 x max(sigma60, sigma1440) | 1.5 x sigma60 |
| Extra condition (v1 filter) | theta at entry >= $2.1627 (theta_bps x entry mid / 1e4) | leg before the signal >= 3.5 theta |

## Mechanics (both rules)

**1. Swings**
- An adaptive zigzag runs on closes with theta of the minute.
- A swing low is confirmed when close - running low >= theta.
- A swing high is confirmed when running high - close >= theta.

**2. Signal**
- A swing is confirmed and the leg from the previous swing (same block) is >= 2.5 theta, where
  theta is measured at the confirmation.
- Swing low confirmed (after a big down leg, price bounced up theta) -> SELL.
- Swing high confirmed -> BUY.
- This fades the bounce, betting that the big leg resumes.

**3. Entry**
- At the market, at the close of the minute after the confirmation.
- No limit orders and no waiting: tested and worse, see swing-entry-timing.

**4. Exit**
- At the close of the minute after the next swing confirmation. For a SELL this is when price
  falls theta from its high after the entry.
- If no further swing comes in the block, at the block's last minute.

**5. Stop**
- 3 theta (theta from the signal) against the entry, checked at minute closes, exit at that close.
- Tighter stops lose money (swing-ext-stop).

**6. Position and money**
- One position per rule; trades of one rule never overlap. A and B can be open at the same time.
- Size: 0.1 lot (10 oz) per rule.
- Cost: $0.168 per oz per round trip (the owner's broker).
- Money at the time's price: net = side x (exit mid - entry mid) - 0.168; THB at 33.77 per USD.

## Backtest 2010-2019 (100,000 THB start, A + B at 0.1 lot each)

| Year | Trades (A) | A THB | B THB | Win | Year net | End capital | DD in year |
|---|---|---|---|---|---|---|---|
| 2010 | 931 (630) | +59,497 | +21,225 | 65% | +80,722 | 180,722 | 25,982 |
| 2011 | 1,061 (736) | +137,038 | +22,501 | 66% | +159,540 | 340,262 | 51,581 |
| 2012 | 995 (672) | +49,787 | -9,086 | 64% | +40,701 | 380,963 | 35,128 |
| 2013 | 873 (591) | +40,518 | +20,643 | 63% | +61,161 | 442,124 | 27,233 |
| 2014 | 665 (398) | +19,059 | +1,829 | 61% | +20,888 | 463,012 | 21,134 |
| 2015 | 625 (359) | +7,368 | -17,950 | 58% | -10,582 | 452,430 | 23,894 |
| 2016 | 752 (471) | -46,023 | +8,748 | 60% | -37,274 | 415,156 | 46,237 |
| 2017 | 420 (168) | +27,920 | +14,018 | 67% | +41,937 | 457,093 | 9,962 |
| 2018 | 418 (152) | -6,154 | -1,894 | 60% | -8,048 | 449,045 | 19,294 |
| 2019 | 591 (300) | +28,575 | +1,830 | 64% | +30,404 | 479,450 | 21,991 |

**Whole period**
- End capital 479,450 THB.
- Max DD 58,773 THB (2 Feb 2015 to 11 Jan 2017).
- Lowest capital 92,204 THB (early 2010).

**Per rule**

| | Rule A | Rule B |
|---|---|---|
| Trades | 4,477 (1.9/day) | 2,854 (1.2/day) |
| Win rate | 64% | 61% |
| Average win | +741 THB | +556 THB |
| Average loss | -1,126 THB | -828 THB |
| Stop hit | 4.5% of trades | 6.5% of trades |
| Worst trade | -13,571 THB | -10,990 THB |
| Net per trade | +$0.21/oz | +$0.06/oz |
| Median hold | 79 min | 98 min |
| Median theta | $3.10 | $2.25 |

## Status and limits
- **Design periods:** 2010-16 chose the filter; 2017-19 checked it once (semi-clean, since the
  base rules were shaped on 2010-19 in today's dollars).
- **Filter evidence:** the A filter's 2010-16 support was borderline (random-subset p 0.068).
  The B filter failed its own check but kept the portfolio's return/DD better.
- **2020-22:** examined once on 31 Oct 2026 (EXAM_PLAN.md): PARTIAL, see the section below.
  Do not tune on these years.
- **2023+:** closed until the owner unlocks it.
- **Spread sensitivity:** with Dukascopy's own spread (wider than $0.168), v1 loses (-87,822 THB
  over 2010-19). The result depends on a broker spread near $0.17.
- **Variant not chosen:** A filtered + B unfiltered ends 2010-19 at 524,829 THB with max DD
  102,426 THB.

## Exam 2020-2022 (one shot, 31 Oct 2026, code/exam_2020_22.py, out/V1_EXAM_2020_2022.json)

**Verdict: PARTIAL.** The net was positive in all 3 years, but t was below 2.
- 2,620 trades (3.5/day), +$0.143/oz per trade (t 1.51).
- The bar for PASS was net > 0, t >= 2 and 2 of 3 years positive.

**By year** (100,000 THB start, A + B at 0.1 lot each)

| Year | Trades | Win | A THB | B THB | Net | End capital | DD in year |
|---|---|---|---|---|---|---|---|
| 2020 | 853 | 63% | +76,497 | +2,644 | +79,141 | 179,141 | 30,980 |
| 2021 | 889 | 62% | +2,345 | +23,194 | +25,539 | 204,680 | 37,542 |
| 2022 | 878 | 62% | +7,734 | +14,006 | +21,740 | 226,420 | 32,843 |

- End capital 226,420 THB.
- Max DD 37,542 THB (12 Apr to 3 Nov 2021).
- Lowest capital 81,711 THB (2020).

**By rule**

| | Rule A | Rule B |
|---|---|---|
| Trades | 1,876 (2.5/day) | 744 (1.0/day) |
| Net per trade | +$0.137/oz (t 1.29) | +$0.159/oz (t 1.04) |
| Win rate | 63% | 60% |
| Average win / loss | +917 / -1,450 THB | +829 / -1,120 THB |
| Stop hit | 5.5% | 6.0% |
| Worst trade | -13,273 THB | -12,261 THB |
| Total | +86,577 THB | +39,844 THB |

**Against the unfiltered A + B on the same years:** +126,420 vs +75,598 THB. The unfiltered B
lost about 9,300 THB here, while v1's B made +39,844 THB.

**Continued from 2010** (100,000 THB in 2010): 2020-22 adds +126,420 THB.
- End capital 2022: 605,870 THB.
- The max DD over 2010-2022 is still 58,773 THB (2015-17).

## Timeframe check (owner 21:41, 31 Oct 2026; descriptive, code/tf_run.py, out/V1_TIMEFRAMES.csv)

**Setup**
- The same v1 parameters, with swings, signals and stops read on 5m / 15m / 30m / 1h closes.
- Theta is still the v1 volatility measure, taken at the bar's last minute.
- Entry and exit happen one minute after the signal bar closes.
- TF 1m reproduces v1 exactly.
- Money: 100,000 THB start, 0.1 lot per rule.

| TF | 2010-19 THB | 2020-22 THB | 2010-22 end capital | Max DD 2010-22 | Trades/day | Win | Years positive (13) |
|---|---|---|---|---|---|---|---|
| 1m (v1) | +379,450 | +126,420 | 605,870 | 58,773 | 3.2 | 63% | 10 |
| 5m | +129,032 | -93,535 | 135,498 | 178,573 | 2.8 | 61% | 7 |
| 15m | +207,974 | -59,308 | 248,666 | 228,342 | 2.4 | 60% | 7 |
| 30m | +278,453 | +27,810 | 406,264 | 157,592 | 2.2 | 59% | 8 |
| 1h | +195,453 | -863 | 294,589 | 144,913 | 1.9 | 59% | 8 |

**Reading**
- 1m is best on every measure.
- Higher timeframes see the bounce later, so the entry comes after part of the edge is gone. This
  matches swing-entry-timing: the edge sits in the first minutes after the signal.
- Higher timeframes also check the stop less often, which means larger losses and 2-4x the DD.
- v1 stays on 1m.

## Execution audit (31 Oct 2026; ../swing-causal-execution by another session, fact-checked in ../swing-v1-audit-check)

**The audit found real simulator issues in v1. All of them are small.**

| Issue | Effect on 2010-19 (THB) |
|---|---|
| Volatility counted returns across missing minutes as 1-minute returns | -18,936 |
| The close-based stop filled at the same close it was seen on | -5,008 |
| The theta$ filter used the entry-minute price | -895 |
| Entry at the next available minute, even when minutes are missing | -513 |
| Trades closed before a >30-minute gap | +4,240 |

- The drawdown counted closed trades only.
- The independent re-run with all fixes gives +352,244 THB. The audit engine gives +359,209.

**Corrected figures (audit engine, $0.168 spread)**

| Period | Corrected result | v1 as reported |
|---|---|---|
| 2010-19 | +359,209 THB | +379,450 THB |
| 2020-22 | +154,150 THB (t 1.84) | +126,420 THB |
| 2010-22, continuous | ends at 613,360 THB | ends at 605,870 THB |
| Max DD | 68,463 THB, including open positions | 58,773 THB, closed trades |

- The rules are unchanged, and no conclusion changes.

## OFFICIAL FIGURES (owner 21:58 ICT, 31 Oct 2026: follow the ChatGPT audit)

From now on, the official v1 numbers come from the audit engine
../swing-causal-execution (out/verified-2020-2022/continued/fixed/REPORT.json). Rules and
parameters are unchanged. The figures above, from code/swing_v1.py, are kept for history only.

**Setup:** 0.1 lot per rule, $0.168 fixed spread, no commission or slippage, 100,000 THB start
in 2010, continuous through 2022.

| Year | Closed trades | Net THB | Equity at year end | Max equity DD in year |
|---|---|---|---|---|
| 2010 | 922 | +76,530 | 176,530 | 28,097 |
| 2011 | 1,052 | +151,251 | 327,496 | 51,467 |
| 2012 | 981 | +34,387 | 362,116 | 33,737 |
| 2013 | 876 | +58,382 | 419,028 | 29,094 |
| 2014 | 665 | +22,438 | 442,988 | 24,080 |
| 2015 | 626 | -23,774 | 419,214 | 36,040 |
| 2016 | 751 | -33,788 | 385,803 | 46,592 |
| 2017 | 421 | +41,189 | 426,626 | 10,511 |
| 2018 | 421 | -5,849 | 420,765 | 18,064 |
| 2019 | 590 | +38,444 | 459,209 | 26,862 |
| 2020 | 855 | +85,818 | 545,218 | 36,449 |
| 2021 | 889 | +34,459 | 579,724 | 33,296 |
| 2022 | 881 | +33,874 | 613,360 | 31,236 |

**Whole period**
- 9,930 trades.
- End equity 613,360 THB.
- Max equity DD 68,463 THB (23.0%).
- Lowest equity 96,040 THB.

**Per rule**

| | Rule A | Rule B |
|---|---|---|
| Trades | 6,351 | 3,579 |
| Net | +417,368 THB | +95,992 THB |
| Win rate | 64.1% | 61.6% |

**Exam view of 2020-22 (fresh 100,000 THB):** +154,150 THB, t 1.84. Still PARTIAL by the
original bar.

**Note on gaps:** the audit engine's default does not flatten before the daily break. 1,154 of
the 9,930 trades close at the first quote after a >30-minute gap. Swap/funding is not modelled.
v1's design intent is flat before the break. For live use, set the broker's daily cutoff
(run.py --flat-utc, broker calendar and DST needed) or budget for swap.

## Always flat before the market closes (owner 22:02 ICT; ../swing-v1-flat-daily)
Audit engine plus a DST-aware schedule:
- close everything at 16:55 New York time;
- no entries until the 18:00 NY reopen;
- on holiday early closes, close in the last 5 minutes before the close (needs the broker's
  holiday schedule).

No trade is held across a trading day or any gap.

Result (0.1 lot per rule, $0.168, 100,000 THB in 2010, continuous through 2022):
- End equity 561,405 THB.
- Max equity DD 60,899 THB (20.9%).
- 9,799 trades.
- 2020-22 closed net: +128,141 THB.

| Year | Net (THB) |
|---|---|
| 2010 | +63,579 |
| 2011 | +164,847 |
| 2012 | +4,847 |
| 2013 | +64,694 |
| 2014 | +18,698 |
| 2015 | -13,612 |
| 2016 | -34,616 |
| 2017 | +42,308 |
| 2018 | -8,745 |
| 2019 | +31,265 |
| 2020 | +73,540 |
| 2021 | +30,682 |
| 2022 | +23,918 |

For comparison, the audit default (holds through breaks, swap not modelled) ends at 613,360 THB
with max DD 68,463 THB.

**Exness schedule (the owner's broker)**
- Exness metals break: 20:58-22:01 server GMT+0 in US summer time, which is 16:58-18:01 NY all
  year. The weekly open is Sunday 18:05 NY.
- The schedule: flat at 16:55 NY, entries from 18:01 NY, holiday early closes as above.
- In Thai time:
  - US summer: flat at 03:55 ICT, break 03:58-05:01 ICT;
  - US winter: flat at 04:55 ICT, break 04:58-06:01 ICT.
- Result: 2010-22 end 559,263 THB, max DD 60,899 THB, 9,797 trades, 2020-22 closed net
  +126,946 THB.
- This is the version to use with Exness.
