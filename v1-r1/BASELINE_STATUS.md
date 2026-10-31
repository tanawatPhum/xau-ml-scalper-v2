# Baseline correction after reading the latest v1

**Resolved for current RX:** the user subsequently authorized the daily-close
repair and retuning. See `daily/RESULTS.md` and `current_rx.py`. New D058 has
zero observed market-close/session crossings in2010-2019; conservative holiday
entry blackouts and missing-quote limitations remain explicitly disclosed.
The original review and older experiment below are historical records.

The owner clarified that current v1 must not hold positions across the trading
day. The latest specification points to `../swing-v1-flat-daily/flat_daily.py`,
mode `EX`, not the default `swing-causal-execution` configuration used here.

## Latest intended schedule

- Flatten at16:55 America/New_York, with DST conversion.
- Block entries until18:01 NY; Sunday reopening restriction extends to18:05 NY.
- Close before announced early holiday closes using a schedule available before
  trading. Trading-day boundaries are broker sessions, not Thai midnight.
- Original A/B signal rules and0.1lot per rule remain unchanged.

These are the settings in the local latest specification, not a fresh external
verification of present-day broker hours.

## Status of the existing v1-rx results

Both immutable locks have `flat_minute_utc: null`; the runner uses the original
engine with no daily cutoff. Consequently the existing RESULTS.md compares
P20 against the old overnight-capable baseline, NOT the latest flat-daily v1.
Its numbers remain historical results under their original assumptions; they
do not settle the requested comparison against the latest v1.

The saved2010-2019 trades confirm the mismatch:1,080 of7,305 old-baseline trades
and530 of3,132 P20 trades cross the NY trading-day boundary, counted using the
same session-date convention as flat_daily.py. No strategy or locked result has
been overwritten in this review, and no revised flat-daily tuning run is claimed.

## Causality issue in the latest implementation

`flat_daily.py:120-124` does not consume an advance holiday calendar. Modes S2/EX
find the next observed gap via `np.diff(mins)` and backfill its last quote time,
then flatten/block the preceding five minutes. They also treat the dataset end
as a known future gap. This includes unannounced outages and future data limits.

A synthetic check of the extracted schedule function (without importing the
module's top-level2010-2022 backtest) keeps quotes15:00-15:09UTC identical and
changes only whether the next quote arrives at15:10 or16:00. EX/S2 change the
earlier decisions at15:05-15:09. Truncating the same data also changes those
earlier decisions. S0/S1 pass the same checks.

Evidence: `research/LATEST_V1_SCHEDULE_REVIEW.json`.

For a valid subsequent comparison, both baseline and RX must use the same
known-in-advance daily/holiday calendar. Unknown outages cannot be guaranteed
flat beforehand without future information; they must be handled at the first
observable quote and separately reported. The current zero-gap-crossing claim
does not prove that the EX backtest is causal.
