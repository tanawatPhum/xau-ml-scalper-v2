# v1-r2: per-session formulas for rules A and B (written before outcomes)

Owner 23:39 ICT, 31 Oct: test per-session formulas for A and B as v1-r2.
Base = **v1-r1** (D058, ../v1-r1, the current revision). Its code, calendar and lock are imported
read-only and are not modified.

## Base v1-r1 (D058)
- **Rule A:** theta = 1 x max(sigma60, sigma1440), theta$ >= $3, leg >= 2.5 theta, no signals
  21:00-23:59 UTC (skip_late).
- **Rule B:** theta = 2 x sigma60, theta$ >= $3, leg >= 3.5 theta, sigma60/sigma1440 <= 1.5
  (vol_le15).
- **Stop:** 2.5 theta.
- **Engine:** the v1-r1 daily-close engine: NY 16:55 flatten, 16:58 close, 18:01 reopen
  (Sunday 18:05), DST-aware, conservative holiday blackouts; fills one minute later.
- **Money:** 0.1 lot per rule, $0.168, 33.77 THB/USD, 100,000 THB start.

## What v1-r2 changes
Each rule gets its own formula per session. The session is that of the minute, in New York
local time:

| Session | NY time |
|---|---|
| Asia | 18:00-03:00 |
| London | 03:00-08:00 |
| NY morning | 08:00-12:00 |
| NY afternoon | 12:00-18:00 |

Per rule and session, these can change:
- **k (theta = k x the rule's volatility):** the zigzag threshold switches with the session, so
  each rule is still one swing stream and one position.
- **Minimum theta$.**
- **Minimum leg.**
- **On / off:** whether signals in that session may enter.

Fixed: the rest of v1-r1, including the volatility measures, the A skip_late and B vol_le15
policies, the stop of 2.5 theta, exits, the calendar and costs.

**Grid per (rule, session)**

| Rule | k | Minimum theta$ | Leg | Cells |
|---|---|---|---|---|
| A | {0.75, 1, 1.25, 1.5} | {2.1627, 3, 4} | {2.5, 3.5} | 24, plus "off" = 25 |
| B | {1.5, 2, 2.5} | {2.1627, 3, 4} | {2.5, 3.5} | 18, plus "off" = 19 |

## Design (2010-2016 only), automatic

**Check first.** With no overrides, the builder must reproduce v1-r1's signals and its 2010-16
training metrics exactly.

**Stage 1.** For each rule and session, try every cell with all other sessions and the other rule
at base, as a full A + B portfolio run.
- A cell qualifies only if:
  - net >= base net;
  - DD <= base DD;
  - net/DD > base net/DD;
  - zero market-close or session crossings.
- Pick the qualifying cell with the highest net/DD; with none, the session stays at base.

**Stage 2.** Combine all stage-1 picks. Accept the combination if:
- net > base net;
- DD < base DD;
- 2014-16 net >= base;
- lowest equity > 0;
- >= 500 trades;
- zero crossings.

If it fails, add picks greedily in order of their stage-1 net/DD, keeping a pick only if the
running set stays at net >= base and DD <= base and its net/DD improves. The final set must pass
the same acceptance rule. If nothing passes, v1-r2 = NOT_CONFIRMED and v1-r1 stays current.

**Lock.** The result is locked (LOCK.json + sha256) before any 2017+ run.

## Evaluation
- **2010-2019 and 2017-19.** Run continuous 2010-2019, and 2017-19 standalone from 100,000 THB,
  under three costs: fixed $0.168, the cost example (+$0.01 commission and $0.02 slippage per
  side), and historical bid/ask. 2017-19 was seen in earlier work, so the check is exploratory.
- **PASS** = on 2017-19 at the fixed spread, v1-r2 net > v1-r1 net, DD <= v1-r1 DD, and zero
  crossings.
- **Status if PASS:** v1-r2 becomes the current version (VERSIONS.json, README).
- **Status if not PASS:** v1-r2 is recorded as NOT_CONFIRMED.
- **2020-2022.** Descriptive only, under the owner's earlier authorization for v1-r1. 2023+
  stays closed.
- **Also reported:** results by session for both versions.
