# Causal execution audit

Engineering correction of Swing v1 execution, not a strategy search, formal main
project experiment, new holdout exam or approval to trade. See [DESIGN.md](DESIGN.md)
and [RESULTS.md](RESULTS.md). Frozen `../swing-v1` is not modified.

## Run

Python 3.12 with the versions in requirements.txt. The existing local environment
used for verification is `D:\xau-ml-scalper\.venv\Scripts\python.exe`.
From this folder, using an environment with these dependencies:

```powershell
python run.py --output out/my-fixed-run
python run.py --cost-mode historical --output out/my-historical-run
python run.py --commission 0.01 --slippage 0.02 --output out/my-cost-example
python run.py --years 2010 --output out/my-2010-run
python run.py --years 2020 2021 2022 --allow-2020-2022 --output out/my-2020-2022-audit
python -m pytest tests -q --basetemp .test-temp-my-run
```

Outputs must use a new directory; the runner refuses to overwrite. Default
access permits2010-2019 only. The owner subsequently authorized the correction
audit through2020-2022; these years require --allow-2020-2022. Even with that flag,
2023+ is rejected before price access. There is no connection to live orders.
Cache paths are relative to this project by default, with --cache override.
See [RESULTS_2020_2022.md](RESULTS_2020_2022.md) for the authorized extension.

## Behavior

1. Confirm swings using observed M1 closes and strictly prior volatility. Count
   only adjacent one-minute returns; retain long-vol history across blocks and
   across years. Short vol restarts after an observed gap >30 minutes.
2. Freeze the dollar filter at the confirmation close. Send a market-at-next-close
   instruction for the exact next minute; if its quote is absent, cancel entry.
   This is a model of precommitted execution, not a guarantee of a broker fill.
3. On the next swing or a close-based 3-theta stop, exit at the next observed
   quote. A gap closes open trades AFTER the gap at the first available quote.
   Stops can therefore lose more than 3 theta. A and B each hold at most one trade.
4. No broker schedule is assumed. `--flat-utc HH:MM` optionally supplies a daily
   known-ahead cutoff: flatten at/after it and forbid entries until the next UTC
   day. It does not infer DST or holidays. Default replay may carry positions
   through gaps. Calibrate a broker-specific calendar separately if required.
5. No terminal-bar forced close. Unclosed trades remain in OPEN_POSITIONS and
   contribute to estimated liquidation equity. Pending actions are counted.

## Costs and accounting

- `fixed`: synthetic bid/ask around mid, default round-trip spread $0.168/oz.
- `historical`: buy at observed ask / sell at observed bid; `--spread` unused.
- `--commission`: USD/oz per side, charged at entry and exit.
- `--slippage`: adverse USD/oz on each fill, including estimated exit liquidation.
- Zero commission/slippage is an explicit assumption, not broker evidence.
- Default size is 10 oz per rule (0.1 lot each), fixed FX 33.77, starting 100,000 THB.
- Balance includes entry commission immediately; equity = balance + executable
  liquidation P&L on open positions (with estimated exit commission and slippage).
- `realized_net_thb` is balance change; `closed_trade_net_thb` is the sum of closed
  trades. They differ by paid entry commission while trades are open.
- Summary gross/spread/slippage/`commission_thb` totals cover CLOSED trades.
  `commission_paid_thb` additionally includes entry commissions on open trades.
- Drawdown is computed after aggregating A+B actions at each observed minute,
  from the initial capital and subsequent equity peaks. THB and % maxima can occur
  at different times. Missing-minute and intraminute paths cannot be measured.
- No margin liquidation, swap/funding, variable FX or intrabar high/low fills.
  Nonpositive equity is flagged. A negative-equity stress path is mathematical;
  it is not a viable funded account trajectory.
- `exit_delay_minutes` measures request-to-fill time only for stop/swing-reason
  exits. Forced gap/scheduled exits use zero by convention; do not use that field
  as a complete broker latency measure.

## Artifacts

- REPORT.json: configuration, assumptions, totals, per-year cash/equity, rules,
  source SHA-256 and package versions. Reports declare no PASS/FAIL strategy verdict.
- TRADES.private.csv: fills, directions, reasons, gross and separate costs.
- EQUITY.private.npz: UTC minute, balance, unrealized, equity, gross/net oz.
- OPEN_POSITIONS.private.json: unclosed positions and entry commissions.
- FROZEN_V1_HASHES.json: before-work hashes of original v1 files, excluding caches.

All price-derived files stay local. `out/verified/` contains the2010-2019 runs;
earlier `out/*-2010-2019/` runs predate a reporting correction and are retained
only as intermediate audit records.

`out/verified-2020-2022/standalone/` contains fresh100k replay of2020-2022 and
`continued/` the continuous2010-2022 path, each in the same three cost scenarios.
COMPARISON.json verifies the development prefix is unchanged, all six cost/equity
ledgers reconcile and2020-2022 trades match between standalone/continued runs.
`provenance/run_before_2020_extension.py` preserves the exact runner hashed in the
prior development reports; it is an archive, not the supported entry point.
