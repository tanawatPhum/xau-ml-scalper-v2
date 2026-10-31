# Execution ledger — docs/superpowers/plans/2026-10-31-rx-daily-close.md

- Calendar and scheduled replay:13tests RED to GREEN; study selection2tests RED
  to GREEN. Combined120tests passed before holiday clarification.
- Actual2010prefix checks:4checks passed for baseline and oldP20, including
  prefixes with open positions; no past feature/signal/trade/equity changes.
- Fresh source-only core review: no blockers; reviewer independently passed15
  daily tests and4extra synthetic edge groups, no market data accessed.
- Training scan interrupted before any lock/evaluation to fix holiday handling:
  a no-entry blackout must not discard quotes that allow an emergency exit of
  a position whose earlier cutoff was missed. Two regression tests first fail,
  then calendar availability is changed to regular session availability;
  holiday masks still prevent all new entries. Search/ranking unchanged.
- Ruling: historical holiday archive is unavailable, so use the disclosed
  conservative date-based entry blackout policy, not a fabricated exact Exness
  calendar. Cost: omitted holiday opportunities and residual calendar uncertainty.
- Ruling: an unknown outage cannot be closed before its first observable quote.
  Keep actual fills and report close-crossing exceptions. Cost: some baseline
  paths violate the no-overnight objective rather than showing impossible fills.

- Calendar clarification tests RED to GREEN; full relevant suite121passed.
- Training complete:186single-rule cells and90portfolios; selectedD058, stop2.5.
  Trainingpass: net298945.89,DD30211.15,0close/sessioncrossings.
- Lock written2026-10-31T15:37:26.410381+00:00 before newevaluation; no changes
  to locked sources/calendar/parameters afterward.
- Evaluation18runs complete: full fixedRX320730.91/DD30211.15;0of2802trades
  cross the market close/session.3late16:55cutoffs still fill before16:58.
  Validation profit21785.03 remains belowv1 56126.75: NOT_CONFIRMED vs v1.
  Against oldRX on identicalcalendar, profit+18.39%,DD-24.55% full; profit+51.98%,
  DD-22.48% validation. Total losses/worsttrade are worse than oldRX.
- Finalverification6actualprefixes and18accountingreports PASS; oldlockedsource
  hashes unchanged. Currententrypoint=current_rx.py; report=daily/RESULTS.md.
