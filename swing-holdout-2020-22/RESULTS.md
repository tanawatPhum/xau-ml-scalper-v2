# One-shot holdout exam 2020-2022: results (2026-10-31)

Plan `PLAN.md` (written before any 2020-2022 outcome). Code `code/exam.py`. Output `out/EXAM.txt`,
`out/EXAM.json`. The script first reproduced 2017-2019 exactly (A 2034 / +0.504, B 1791 / +0.583),
then ran 2020-2022 once. Today's $ per oz; cost $0.168; entry/exit 1 minute late.

## Verdict (A + B together): PARTIAL
- Net per trade +0.364 (day-clustered t +1.8, below 2); years positive 2/3
  (2020 +0.648, 2021 -0.009, 2022 +0.453). 3623 trades.
- Max drawdown per oz-equivalent 229.0, inside the 2010-2019 range (262.6).

## Each rule (reported, not the verdict)
| Rule | Trades/day | Net/trade (t) | Win | Stop | Worst | Max DD/oz | 2020 / 2021 / 2022 net/trade |
|---|---:|---:|---:|---:|---:|---:|---|
| A (k 1, sigma_eff) | 2.51 | +0.510 (2.2) | 64.0% | 5.6% | -84.2 | 220.4 | +1.026 / +0.235 / +0.263 |
| B (k 1.5, sigma60) | 2.15 | +0.193 (0.7) | 62.3% | 7.2% | -85.7 | 334.0 | +0.205 / -0.277 / +0.688 |
- Rule A held its 2017-2019 level (+0.504 -> +0.510) and was positive every year; two thirds of its
  2020-2022 profit came from 2020 (high-volatility year). Rule B weakened (+0.583 -> +0.193).
- Choosing rule A alone NOW would be a decision made after seeing the holdout; it would need 2023+
  to be confirmed.

## 100,000 THB, 0.01 lot each rule (USD/THB 33.77)
| Year | Trades | Win | Rule A | Rule B | Total | Capital |
|---|---:|---:|---:|---:|---:|---|
| 2020 | 1215 | 64% | +22,732 | +3,865 | +26,597 | 100,000 -> 126,597 |
| 2021 | 1210 | 63% | +5,017 | -5,400 | -383 | 126,597 -> 126,214 |
| 2022 | 1198 | 63% | +5,896 | +12,426 | +18,323 | 126,214 -> 144,537 |
- Max drawdown 15,466 THB (~15%); lowest capital 95,905 THB; about +14,800 THB per year
  (2017-2019 in-sample: about +23,300 per year).

## Correction 2026-10-31 14:40: money at the gold price of the time
All money above (and in every earlier swing report) is in "today's dollars": each historical move in
bps was valued at today's price 4083.276, with the $0.168 spread also at today's price (0.41 bps).
That answers "what would the same % moves earn today", not "what was earned then". Re-computed with
the real mid price at the time and a fixed $0.168 spread (code `code/historical_price.py`, output
`out/HISTORICAL_PRICE_01LOT.json`; same trades, rules A + B at 0.1 lot each, 100,000 THB, FX 33.77):
- 2010-2022: end 561,917 THB (not 3,113,934); max drawdown 126,314 THB; lowest 81,446 THB.
- Net per trade per oz at the time: 2010 +0.149, 2011 +0.307, 2012 +0.211, 2013 +0.146, 2014 +0.056,
  2015 -0.074, 2016 -0.174, 2017 +0.175, 2018 -0.030, 2019 +0.036, 2020 +0.190, 2021 -0.100,
  2022 +0.094. Exam years 2020-2022: +75,598 THB in total (+78,150 / -40,753 / +38,201).
- Why: gold was 1,160-1,800 then, so a fixed $0.168 spread was 0.9-1.45 bps, 2-3.5x today's 0.41 bps.
- With Dukascopy's own historical spread (about 2 bps) the same trades lose every year but 2011,
  2012 and 2017: the edge is thin and depends on a low spread.
- The edge in % terms: the exam years' gross per trade is about 1.3 bps, so break-even spread is
  about 1.3 bps, about $0.53 at today's price (3x the current $0.168).
