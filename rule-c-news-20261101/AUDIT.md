# Independent audit — FOMC declared-time continuation diagnostic

1 November 2026. Scope: saved announcement evidence and manifests, protocol, signal/execution/runner source, synthetic tests, frozen source/lock manifests, and reported JSON results. This reviewer opened no market cache or private result array and changed no experiment source, lock, criteria, or result.

## Verdict

No unresolved implementation blocker was found for this explicitly restricted diagnostic. It is not a qualified Rule C and must not unlock validation: eight eligible design events produced only five trades, below the frozen minimum of 20. The lock correctly selects nothing; `VALIDATION.json` contains no rows or years read.

At 0.1 lot, the five trades report fixed-spread net 2,389.06 THB, example-cost net 2,287.75 THB, historical-spread net 2,117.38 THB, after-cost PF 2.4132, equity drawdown 2,063.85 THB, and natural A/B overlap 0/5. The fixed-stop sensitivity is identical. A positive result from five 2016 trades does not establish a durable edge or representative multi-year news effect.

## Timestamp and coverage findings

- The retained 2010–2019 metadata have 82 unique event dates/URLs: 80 regular statements and two explicitly excluded other statement types. Forty-eight regular 2010–2015 rows have no release minute; they are excluded without guessing a customary release clock. The eligible regular subset is eight 2016 events plus 24 validation-metadata events.
- Independently checked the 32 eligible rows against their saved date-specific page extractions: matching official header and date, evidence-file SHA-256, unique declared UTC minute, and America/New_York EST/EDT conversion. The design file equals the eight eligible design rows. These checks validate the extraction artifacts and consistency; they are not independent original HTTP-byte archives or contemporaneous feed observations.
- Every `actual_available_at_utc` remains blank and every actual-latency flag is false. An official declared release header does **not** prove the information was actually available by entry at E+5. Therefore this is a declared-time proxy diagnostic, not a validated real-time news-availability strategy. The manifest and protocol correctly preserve that limitation instead of inventing observed timestamps.
- Other events and minutes remain unknown-news, never no-news. No quiet-news control, surprise series, or complete news classification is constructed. The design universe is not expanded after outcomes. The data audit distinguishes the six live checks of missing headers from the 42 missing-time rows not independently re-fetched.

## Signal, execution and costs

- The signal uses exactly six consecutive quotes E−1 through E+4, representing five returns, within one NY session. Its direction is the endpoint impulse sign; the threshold is fixed at absolute log return divided by `eff[E] * sqrt(5/60) >= 2`. The USD scale uses `eff[E]` and the E−1 price. Review of the inherited volatility calculation and an independent synthetic context test confirm that `eff[E]` excludes the announcement return and all later returns.
- Both supplied synthetic suites passed. Independent tests also passed prefix equality before and at the completed event window, pre-event volatility invariance when announcement-and-later prices change, and the exact scale/normalization formula. The supplied integration tests cover next-minute cancellation, E+5 entry, E+20 timed exit, delayed observed-close stop execution, costs, overlap union and forbidden-year rejection.
- The reused executor contains no A/B entry veto. Overlap uses baseline same-minute gross exposure as a binary union, so simultaneous A/B holdings count once and a same-minute completed exit does not count. All reported close/session crossings, late cutoffs, gap spans and terminal positions are zero.
- Independently reconciled every reported primary trade: signal E+4, entry E+5, exit E+20, and fixed net equal to midpoint P/L less 0.168 USD/oz at 10 oz and FX33.77. Reported trade nets sum to closed net. Aggregate example net equals fixed net less 0.06 USD/oz additional round-trip costs per trade. This is an independent check of saved accounting outputs, not a new market-data simulation.

## Freeze and qualification

Current frozen source hashes match `PRE_RUN_LOCK.json` and `LOCK.json`; both sidecar digests match, and the final lock points to the same pre-run lock. The pre-run record explicitly states that eight events cannot meet 20 trades before prices are loaded. Source/data consistency, locked baseline reproduction and an actual open-position prefix test are reported as passing. The runner permits only exact 2010–2016 design years and has no validation loader branch. No 2020+ price path is used by this runner; announcement metadata beyond 2019 in the original CSVs is separately disclosed and not confused with price access.

The code includes an additional 0.5-lot solvency gate although the protocol also describes that scale as diagnostic. This was already frozen before outcomes and is nondecisive here: it passes, while the trade-count gate fails regardless of returns. Preserve and disclose it rather than changing criteria after the run. The lower news-specific 20/8 trade thresholds were authorized on metadata before outcomes and are disclosed relative to earlier pilots; they do not rescue this five-trade diagnostic. The stop sensitivity cannot substitute for the primary. No new v1 version or registry change is supported.

## Interpretation limits

PF and `gross_wins`/`gross_losses` use after-cost trade P/L; `gross_mid_net` is the separate pre-cost midpoint amount. Combined portfolio profit is dominated by the locked profitable A/B baseline and does not validate C. All design trades occur in 2016 because earlier release minutes are unknown; zero rows for earlier years are lack of eligible timestamp coverage, not evidence that the market supplied no opportunities. Fixed 0.5-lot results are arithmetic scaling with no financing, margin, compounding or stop-out model. Hash consistency is not an operating-system record of every file access, and official declared times are not observed dissemination times.
