# Causal execution audit (2026-10-31)

Authorized by the owner's request to implement the execution/cost/equity audit.
This is an engineering correction, not a new strategy search or holdout exam.

## Approach
Keep frozen Swing v1 untouched. Add an independent simulator with the same A/B
parameters. Patching the frozen reference would erase the comparison; replaying
saved trades alone cannot correct entry/exit decisions. The independent replay
therefore generates signals and fills them chronologically.

## Contract
- Signals and the dollar-size filter use confirmation-time information. Submit
  orders for the next minute close, never inspect that fill to decide eligibility.
- A stop is detected at a minute close and filled at the next observed quote;
  it is a close-based stop, not an intrabar broker stop.
- Missing the entry's exact next minute cancels the entry. Pending exits fill at
  the first observed quote. A gap >30 minutes resets swing state and closes an
  existing position at the first quote AFTER the gap, never before it.
- Optional UTC daily flatten cutoff is a user-supplied, known-ahead schedule;
  no broker calendar is guessed. At/after cutoff, close and block entries until
  the next UTC day. A missing cutoff quote fills at the first observed quote.
- At end of input keep positions marked open; no artificial final-bar closure.
- Volatility uses strictly prior returns. Only adjacent 1-minute quote pairs
  count; missing minutes are not silently treated as 1-minute returns. Short
  volatility stays inside the current >30-minute-gap block; long volatility
  retains history across blocks, excluding cross-gap returns.
- One position per rule. A and B may overlap. Both use 10 oz, FX 33.77, start
  capital 100,000 THB. No tuning, leverage assumptions or margin liquidation.
- Fixed synthetic spread (default round-trip $0.168/oz) OR historical bid/ask.
  Commission per side and adverse slippage per fill are explicit nonnegative
  USD/oz inputs; zero is an assumption, not measured broker execution.
- Equity marks open positions at the executable liquidation side including
  estimated exit slippage/commission. Track balance, unrealized P&L, THB and
  percentage drawdown, exposure and nonpositive equity. No intrabar risk claim.
- Default data access remains 2010-2019. Owner explicitly authorized completing
  the correction audit through2020-2022 in the next request. These years require
  --allow-2020-2022; 2023+ is always rejected before price access. Preserve all
  original exam artifacts; this audit does not create a fresh unseen holdout.
- All derived arrays/trades remain local (*.private.*); all output is new.

## Files and validation
engine.py: price validation, causal signals, fills, cost ledger, portfolio equity.
run.py: protected loader, CLI, JSON report, private trades/equity and provenance.
tests/: synthetic chronology, prefix invariance, gaps, scheduling, stop delay,
long/short costs, two-rule equity and input/output boundary tests.
Run 2010-2019 with unchanged parameters and report both fixed and historical
spread, plus an explicitly hypothetical commission/slippage scenario. Hash the
frozen v1 files before/after. No outcome-based parameter changes.
