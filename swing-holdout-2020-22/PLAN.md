# One-shot holdout exam 2020-2022 for swing rules A and B (written before any 2020-2022 outcome)

Owner 14:06 ICT, 31 Oct: "test 2020-22 first". This opens the sealed 2020-2022 years ONCE for the
frozen rule set below. 2023+ stays closed. Nothing is tuned after this exam; any later change must
be judged on data the change has not seen (2023+ with owner approval).

## Frozen rules (from swing-rule-v1 / swing-improve-v2, unchanged)
- Mid closes of Dukascopy M1, blocks split at gaps > 30 min (positions closed before the daily
  break). sigma60 and sigma1440 as before; sigma_eff = max(sigma60, sigma1440).
- Rule A: theta = 1 x sigma_eff. Rule B: theta = 1.5 x sigma60.
- Signal: confirmed swing (reversal theta from the running extreme) after a leg B >= 2.5 theta;
  trade AGAINST the bounce. Entry at the close one minute after the signal; exit at the next swing
  confirmation + 1 minute; stop 3 theta at a minute close; block end forces exit.
- Cost $0.168 per round trip; money in today's dollars (price 4083.276), per oz.
- Rule set = A and B together at equal size.

## Code check before the exam
- The exam script must reproduce 2017-2019: rule A 2034 trades, net +0.504; rule B 1791 trades,
  net +0.583 (per oz). If it does not, stop and fix before computing 2020-2022.

## Verdict (fixed now; A+B together, per oz-equivalent = 0.5 oz each)
- PASS: 2020-2022 mean net per trade > 0 with day-clustered t >= 2, AND net > 0 in >= 2 of 3 years.
- PARTIAL: mean net > 0 but t < 2 or only 1 of 3 years positive.
- FAIL: mean net <= 0.
- Drawdown check (reported, not part of the verdict): max drawdown over 2020-2022 vs the
  2010-2019 max drawdown of the same set (262.6 per oz-equivalent).
- Also reported: each rule alone, per year, trades per day, win rate, worst trade, and the
  100,000 THB view at 0.01 lot each (USD/THB 33.77).
