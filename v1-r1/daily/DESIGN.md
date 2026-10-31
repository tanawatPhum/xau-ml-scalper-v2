# RX daily-close revision

Owner request: tune RX, close positions before market closure, remove the
future-gap leak, report results. Authorized scope remains design2010-2016 and
evaluation2010-2019, equal0.1lot per rule and100kTHB start. Prior2017-2019 results
are already known: all validation here is reused/exploratory.

The new revision lives under v1-rx/daily; original frozen outputs remain intact.
Both v1 and RX use the same revised execution and calendar. No quote-derived
calendar, next-gap backfill, last-observation exit or forced EOF liquidation.

## Calendar, fixed before looking at price results
- NY local time with historical DST conversion; daily flatten16:55, regular
  market close16:58, reopen18:01; Sunday reopen18:05; closed over the weekend.
- Retain quotes only inside the declared market window. This prevents simulated
  fills on vendor quotes when the configured broker would be closed.
- Historical Exness holiday notices are not fully available locally. Use a
  deliberately conservative, deterministic no-trading-session calendar:
  US federal holidays valid in2010-2019, Good Friday, day after Thanksgiving,
  July3, business day before observed July4, and Dec24 throughJan2. This is a
  strategy blackout policy, NOT a reconstructed authoritative broker archive.
- Session date is the NY date of its upcoming close. Blackouts start at the
  previous evening's reopen; the preceding ordinary session closes normally.
- Blackouts forbid entries but retain observed regular-session quotes for
  emergency exits and feature history. They are strategy policy, not a claim
  that the broker is closed for the whole holiday. Missing quotes still cannot
  be replaced by invented fills.
- If the cutoff quote is missing, close at the next observed tradable quote;
  record missed cutoff and market-close/session-crossing exceptions. Never
  invent a pre-gap fill. Unannounced outages cannot be guaranteed flat in advance.
- Emit daily calendar manifest and proof that removing/adding future quotes
  never changes past schedule, signals, orders or liquidation equity.

Sources consulted: Exness instrument-hours help (holiday notices by email and
DST-dependent hours), CME2019 metals guide (standard18:00-17:00 NY sessions).
These do not certify the exact Exness holiday hours for all historical years.

## Bounded tuning (no amendments after selection)
Original A/B parameters plus the previously locked P20 are explicit candidates.
Coarse search: A k(.75,1,1.25,1.5), floor(1.5,2.1626934441569983,3,4),
leg(2.5,3.5,5); B k(1,1.25,1.5,2), floor(0,1.5,2.1626934441569983,3),
same legs. Use the existing11 causal policies. Per rule, policy seeds include
top3net/DD, top2net, baseline and prior P20 (<=7seeds, <=118unique cells).
Shortlist baseline/P20 plus top3net and top3net/DD, deduplicated (<=8per rule).
Evaluate all pairs with stop multipliers2,2.5,3 (<=192portfolios).

Eligibility: net>baseline, DD<baseline, gross closed losses<=baseline,
recent2014-16 net>=baseline, lowest equity>0, >=500closed trades,
and zero market-close/session crossings. Choose highest net/DD; tie-break by
fewer changes then stable ID. If none qualify, retain baseline3theta and report
tuning NOT_CONFIRMED. Do not choose a lower-profit low-frequency fallback.

Lock source/data/calendar hashes and parameters before new2017-2019 runs.
Evaluate continuously2010-2019 and standalone2017-2019, with fixed spread.168,
additional commission.01/slippage.02 peroz/side, and historical bid/ask. Never
select from sensitivity or validation results. Report baseline, old P20 with
the corrected calendar, and selected RX; annual profit, DD, losses, worst trade,
exposure/close exceptions, plus0.5lot scaling with recalculated equity DD%.

## Implementation and review
calendar_rules.py owns calendar; execution.py owns schedule-aware delayed replay;
run_study.py owns bounded search/lock/evaluation; report_daily.py owns artifacts.
Reuse immutable parent baseline_engine, strategy and data-validation helpers.
Test DST, weekend, holiday eve, missing cutoff, future gaps, EOF, delayed stops,
signal-prefix and trade/equity-prefix invariance, cost accounting and lock integrity.
