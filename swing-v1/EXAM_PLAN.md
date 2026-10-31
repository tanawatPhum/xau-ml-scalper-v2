# Swing v1 one-shot exam on 2020-2022 (written before running; owner 20:28 ICT, 31 Oct 2026)

- Run code/swing_v1.py unchanged (parameters as frozen in SPEC.md) on 2020, 2021, 2022. No tuning
  afterwards; whatever comes out is recorded.
- Verdict (same bar as swing-holdout-2020-22): PASS = A + B net per trade > 0 with day-clustered
  t >= 2 and at least 2 of 3 years positive; PARTIAL = net > 0 but not PASS; FAIL = net <= 0.
- Reported: per year and per rule THB at 0.1 lot each (time's price, $0.168, 33.77), trades/day,
  win rate, stop rate, worst trade, max DD; 2020-22 alone from 100,000 THB and the 2010-2022
  curve continued from the 2019 end; comparison with the unfiltered A + B exam (+75,598 THB).
- 2023+ stays closed.
