# Independent audit — prior abnormal day C

1 November 2026. Scope: protocol, signal/execution/runner source, synthetic-only tests, frozen input manifests, and reported JSON results. No market cache or private price/result array was opened by this reviewer. No experiment or baseline source, selection rule, lock, or result was changed by this reviewer.

## Verdict

No unresolved implementation defect was found. The primary passed its frozen training criteria and failed the permitted 2017–2019 evaluation. Preserve `NOT_CONFIRMED`; neither the stop sensitivity nor a seasonal subset may replace the primary after these outcomes.

| Primary, 0.1 lot | Training 2010–2016 | Evaluation 2017–2019 |
|---|---:|---:|
| Closed trades | 74 | 37 |
| Fixed-spread net, THB | 23,609.79 | -4,419.48 |
| Example-cost net, THB | 22,110.40 | -5,169.17 |
| Historical-spread net, THB | 15,008.06 | -6,292.36 |
| After-cost profit factor | 1.6250 | 0.7749 |
| C entry while A/B holds | 9/74 = 12.16% | 1/37 = 2.70% |
| C equity drawdown, THB | 17,861.29 | 13,909.19 |

Training gain in 2014–2016 was only 605.83 THB with fixed spread, -2.03 THB with example costs, and -1,680.40 THB with historical spread. The frozen recent-period gate used fixed spread, so this does not overturn the original selection; it does show cost sensitivity. Evaluation fails profitability and PF despite low natural overlap. Fixed-stop sensitivity also loses in evaluation (-7,316.27 THB fixed spread).

## Causality and execution

- A UTC+3 day is finalized only when a later observed date begins. The immediately preceding calendar date must pass the predeclared coverage rules. The latest 60 valid earlier returns explicitly exclude that preceding date. Missing dates and short weekend groups do not carry an older abnormal day into a new signal.
- The first observed eligible quote before 06:00 is the sole signal opportunity. Current-day future coverage does not gate it. Independent truncation and future-price mutation tests preserve all earlier signal, scale, expiry and z arrays. Full-history grouping affects diagnostic counters, but not earlier trade decisions.
- Direction fades the prior day's return, not its z-score sign. The scale uses available causal volatility. Entry requires the exact following minute and cancels otherwise; the absolute 06:00 deadline is not shifted by a later entry. Calendar flattening can exit earlier. Stops act on observed closes and execute at the next quote. There is no invented EOF exit or retrospective gap fill.
- Independent tests using the actual calendar confirmed winter UTC+3 entry 00:01 and exit 00:55 (NY16:55), versus summer entry 01:02 and exit 06:00, as well as the holiday block. Reported training has 24 early NY exits and 50 06:00 exits; evaluation has 13 and 24 respectively. Every reported close/session crossing, late expiry/cutoff, gap-spanning trade, and terminal position count is zero.
- The quality policy permits some missing internal minutes when count/start/end criteria still pass. This is the explicit protocol, not an independently verified full daily bar or broker holiday archive.

## Accounting and frozen scope

- Reviewed the independent equity reconstruction: each trade subtracts entry and exit spread, two commissions and two slippages, and open equity carries liquidation costs. Exposure overlap is independently reconstructed from the union of A/B half-open holding intervals (`entry <= t < exit`) and compared with same-minute gross exposure. There is no A/B entry veto. All six primary/sensitivity cost cells report matching minute equity and overlap in both periods.
- The synthetic suite passed. Additional reviewer tests passed future mutation/truncation, injected-history exclusion of the abnormal day, actual-calendar DST deadlines, holiday blocking, flat-price costs, and a mocked empty-selection branch that cannot call a loader or new-year data hashing.
- A pre-outcome review found that the initial evaluation runner did not reverify its 2016 warmup cache against the frozen training hashes. The implementer corrected this before loading outcomes and also verifies the training-result digest. Original `INPUTS.json` and its sidecar were preserved. `INPUTS_v2.json` records the amendment; only `run.py` changed, while the specification and data-hash manifest stayed identical. The reviewer checked both manifest digests and the current source hashes.
- The lock references the amended manifest and training-result digest. Current frozen source hashes and the lock digest match. Source manifests before/after training agree. Price-cache rehashing is reported by the runner, not independently repeated by this audit.
- Evaluation takes 61 completed valid daily records from 2016 solely for C history, while A/B and C volatility start fresh on 2017 quotes. The final incomplete 2016 group is asserted invalid. The saved history contains only 2016 dates. Allowed evaluation years are exactly 2017–2019; no called loader path permits 2020+.
- The stop sensitivity is never selected in place of the primary. `selected` is determined from primary fixed-spread eligibility only; validation uses that frozen primary. No new v1 version or registry change was made by this experiment.

## Reporting limits

`gross_wins`, `gross_losses` and PF refer to after-cost trade P/L, not gross midpoint returns. The inherited `net_2014_2016` key in validation holds the evaluation-period total and must not be described as an actual 2014–2016 statistic. Historical/example combined metrics keep A/B at its fixed-spread baseline while changing C costs; label that composition rather than implying all components were rerun at those costs. Fixed 0.5-lot paths are arithmetic scaling from 100,000 THB, with no margin or stop-out model. Prior use of 2017–2019 means this is reused exploratory validation. Hash consistency and reported year guards are not an operating-system record of every file access.
