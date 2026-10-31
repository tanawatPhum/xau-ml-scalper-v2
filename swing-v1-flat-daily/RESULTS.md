# Swing v1, always flat before the market closes (owner 22:02 ICT, 31 Oct 2026)

**What was run**
- Official audit engine (../swing-causal-execution, imported read-only). The rules, signals,
  fills and costs are unchanged.
- The only change is a per-minute schedule in New York local time (DST-aware), in flat_daily.py.
- The data confirm the gold daily break is 17:00-18:00 NY (gaps.py):
  - the last quote is at 16:59 or 17:00 NY on 2,420 of 2,800 gaps;
  - the first quote after the break is at 18:00 NY on 2,529.
- US holidays show early closes at about 13:00 / 13:45 NY.
- Settings: 0.1 lot per rule, $0.168, 100,000 THB in 2010, continuous through 2022.

**Variants**

| | Rule | Trades crossing a trading day |
|---|---|---|
| S0 | Audit default: no cutoff; trades close after gaps. Reproduces the official run exactly (613,359.55). | 1,462 |
| S1 | Flat at 16:55 NY every day; no entries 16:55-18:00 NY; other gaps close after the gap. | 14 (holiday early closes) |
| S2 | S1, plus flat in the last 5 minutes before every other gap, as if the broker's holiday schedule were known in advance. | **0** (0 span any gap) |

**Results**

| Year | S0 net THB | S2 net THB | S2 equity at year end | S2 DD in year |
|---|---|---|---|---|
| 2010 | +76,530 | +63,579 | 163,579 | 29,451 |
| 2011 | +151,251 | +164,847 | 328,426 | 42,966 |
| 2012 | +34,387 | +4,847 | 333,272 | 38,275 |
| 2013 | +58,382 | +64,694 | 397,966 | 27,218 |
| 2014 | +22,438 | +18,698 | 416,664 | 23,202 |
| 2015 | -23,774 | -13,612 | 403,052 | 26,575 |
| 2016 | -33,788 | -34,616 | 368,437 | 45,799 |
| 2017 | +41,189 | +42,308 | 410,745 | 9,917 |
| 2018 | -5,849 | -8,745 | 401,999 | 21,183 |
| 2019 | +38,444 | +31,265 | 433,264 | 25,918 |
| 2020 | +85,818 | +73,540 | 506,804 | 37,027 |
| 2021 | +34,459 | +30,682 | 537,487 | 33,518 |
| 2022 | +33,874 | +23,918 | 561,405 | 33,062 |

| | S0 | S1 | S2 |
|---|---|---|---|
| End equity 2022 | 613,360 | 564,084 | **561,405** |
| Max equity DD | 68,463 (23.0%) | 60,652 (20.9%) | **60,899 (20.9%)** |
| Trades | 9,930 | 9,803 | 9,799 |
| 2020-22 closed net | +154,150 | +130,813 | +128,141 |
| Rule A | +417,368 | +369,903 | +368,467 |
| Rule B | +95,992 | +94,181 | +92,938 |

**Reading**
- Being flat every day costs about 52,000 THB over 13 years against S0 (about -10%) and lowers the
  max DD from 68k to 61k.
- S0 also ignores swap on its 1,462 overnight trades, so the real gap between S0 and S2 is
  smaller than shown.
- S2 meets the owner's rule: no trade is held across the daily break or any market gap.
- **Exness version (owner 22:08: the broker is Exness), mode EX.**
  - Exness metals hours: Sunday 22:05 to Friday 20:58, daily break 20:58-22:01, server GMT+0
    (exness.com/commodities). That is US summer time; Exness publishes a schedule change at the
    end of US DST, so the break is 16:58-18:01 New York time all year.
  - Mode EX flattens at 16:55 NY, allows no entries until 18:01 NY (18:05 on Sunday), and keeps
    the same holiday rule as S2.
  - Result: 2010-22 end 559,263 THB, max DD 60,899 (20.9%), 9,797 trades. 2020-22 closed net
    +126,946 THB. 0 trades cross a day or a gap.
  - This is within about 2k THB of S2. Rule A +366,325, B +92,938.
- **Losing trades, Exness version (losers.py, after_exit.py; owner 22:14 and 22:17).**
  - 3,697 losers (37.7%), -3.99M THB in total, against winners +4.44M.
  - By exit type:

    | Exit | Share of losers | Share of loss | Average |
    |---|---|---|---|
    | Swing exit | 57% | 39% | -0.6 theta |
    | 3-theta stop | 14% | 43% | -3.3 theta |
    | Daily close | 29% | 18% | -0.6 theta |

  - Price after the exit, until the day's cutoff:
    - Stopped trades: 62% went 1 more theta against first; only 20% later reached a 1-theta win.
      Without the stop, the total is -1.65M vs -1.71M THB, only 2.5% end positive, and the worst
      trade becomes -17.9k. Stopped trades were mostly the wrong direction.
    - Swing-exit losers: 68% came back to the entry and 34% reached a 1-theta win. This is
      mostly noise, since the loss is only about 0.6 theta and hours remained.
- The broker's own break time should be confirmed. Typical MT5 gold breaks at 00:00-01:00
  server time (GMT+2/+3), which is the same as 17:00-18:00 NY.
