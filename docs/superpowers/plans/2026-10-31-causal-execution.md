# Causal execution implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct execution timing and report costs and open-position equity.
**Architecture:** Separate causal replay beside the frozen Swing v1 reference.
**Tech Stack:** Python, NumPy, pandas, Numba, pytest (existing local environment).
**Spec:** swing-causal-execution/DESIGN.md

## Global constraints
- Keep frozen v1 and existing outputs untouched; no Git repository is present.
- Read cached 2010-2019 prices only; protected and previously examined years stay closed.
- No new parameter selection; missing prices must never enable retroactive fills.
- Outputs local under swing-causal-execution/out; private price-derived artifacts.

## Review focus
- Pending orders across gaps/cutoffs; exits must not disappear or fill retroactively.
- Flat/empty/short input and crossed quotes; reject invalid data, allow no trades.
- Long/short asymmetric costs and open-position liquidation equity.
- Same-minute A/B actions; aggregate before computing portfolio drawdown.
- EOF positions and prefix invariance; future data cannot rewrite past actions.

## Task 1: Chronological engine
Files: swing-causal-execution/engine.py, tests/test_engine.py.
Interface: Config, RULES, make_signals(mins,bid,ask), simulate(mins,bid,ask,signals,config).
- [x] Write failing synthetic tests for next-minute fills, stop delay, gap handling,
      cutoff, EOF, cost reconciliation, equity and prefix invariance.
- [x] Run pytest and confirm missing behavior fails.
- [x] Implement causal volatility/swing detection and a chronological per-rule
      replay; aggregate balance/unrealized/exposure minute by minute.
- [x] Run the entire new suite; expected all pass.

## Task 2: Runner and reproducible comparison
Files: swing-causal-execution/run.py, tests/test_run.py, README.md, RESULTS.md.
Interface: load_prices(cache,years), run_audit(years,config,output), main(argv).
- [x] Write failing tests for rejecting 2020+ before file access, valid/invalid
      cache loading, explicit fresh output, CLI and artifact reconciliation.
- [x] Implement safe CLI and JSON/private outputs with source hashes/config.
- [x] Run full tests and 2010-2019 engineering comparisons, not a holdout exam.
- [x] Independent code review, address substantive findings with regression tests.
- [x] Confirm frozen hashes and report numerical changes and remaining limits.

## Execution ledger
Ruling: Use a new sibling folder because this project explicitly is not a Git
repository. Do not initialize Git or change another concurrent research folder.
Ruling: Owner requested implementation of the proposed audit; proceed with
documented defaults without an additional design approval round.
Task 1 complete: 20 execution tests passed after initial19 RED tests; corrected a
test fixture whose too-small theta unintentionally triggered the genuine stop.
Task 2 runner:9 boundary/artifact tests RED then GREEN. Temp directories are
explicitly workspace-local because the host temp path was inaccessible.
Final review fix: open entry commissions must reduce realized cash immediately,
including across year boundaries. Two regressions failed as expected before fix.
Final review: independent read-only reviewer found no other important execution
defects. Both commission regressions GREEN; complete suite33/33.
Final minor (documented limitation): exit_delay_minutes reports stop/swing-reason
request latency only; forced exits use0. Not a complete broker latency measure.
Verification: initial workspace-wide pytest collected an archived UTF-16 log as
a doctest and failed before tests. Excluding research output directories gives
33/33; original archive was not modified. XML retained for both invocations.
Verification: all12 frozen v1 hashes unchanged; final three scenario source
hashes match; all trade costs, minute equity, yearly totals reconcile.
Results and instructions: swing-causal-execution/RESULTS.md and README.md.
