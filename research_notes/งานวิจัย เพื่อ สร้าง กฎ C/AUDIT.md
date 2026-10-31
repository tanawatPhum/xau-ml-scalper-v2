# Independent implementation audit — Rule C literature transfer pilots

Audit date: 1 November 2026. Scope: frozen `rule-c-literature-20261101` plan, signal/execution code, synthetic tests, price-free JSON outputs, and `local_feasibility.md`. This audit made no literature claims beyond supplied notes, opened no market cache or private result arrays, and changed no experiment/baseline source, criteria, locks, or results.

## Verdict

No causal, execution, overlap, or selection defect was found that requires rerunning this frozen experiment. Both primary specifications fail their original training requirements. Keep the failures and empty selection; do not read validation prices, replace primaries with stop sensitivities, or revise the eligibility period after observing outcomes.

| Primary, 0.1 lot | Closed trades | Fixed-spread net, THB | Example-cost net, THB | 2014–2016 net, THB | Natural A/B overlap |
|---|---:|---:|---:|---:|---:|
| Xu midday-to-close transfer | 1,690 | -73,091.96 | -107,334.74 | -40,593.06 | 375/1,690 = 22.19% |
| Ma Shanghai night-clock adaptation | 443 | -32,329.71 | -41,305.78 | -30,242.22 | 53/443 = 11.96% |

All four reported primary/sensitivity cells have negative fixed-spread and example-cost net. Fixed 3-scale stop net is -73,137.55 THB for Xu and -30,560.84 THB for Ma. Primary close crossings, session crossings, late cutoff exits, >30-minute gap-spanning positions, and terminal positions are all zero in the JSON outputs. These are reported outcome checks, not an independent market-data rerun.

## Verified behavior

- Signals use exact same-local-date anchors and contiguous observed minute windows. Xu uses 11:30–12:00 New York, submits at 15:29, and fills only at the exact following 15:30 quote. Ma requires the opposite partial 21:30–22:00 Shanghai retracement after a nonzero 21:00–21:30 impulse; submits at 22:00 and fills at 22:01 in the impulse direction. Source prices and volatility scale are available at signal time.
- UTC timestamps convert through named timezones. New York DST shifts preserve the local signal clock; Shanghai uses its local clock. Timed exits are based on actual entry timestamp: Xu +30 minutes, Ma +59 minutes. Missing next-minute entry cancels. A delayed timed exit uses the first actual observed quote; close-based stop decisions execute at a later observed quote. No end-of-file liquidation is invented.
- The inherited New York calendar applies timestamp-only daily cutoffs, weekends and conservative holiday blackouts. A/B overlap is measured after same-minute processing from nonzero aggregate gross exposure, counts A and B only once, includes simultaneous entries, and excludes already-exited positions. Signals and execution contain no A/B entry veto.
- Fixed spread is 0.168 USD/oz per round trip. The example adds 0.02 USD/oz commission and 0.04 USD/oz slippage per round trip. Synthetic flat-price trades reproduce these costs at 10 oz and FX 33.77. Historical BID/ASK is a sensitivity. The 0.5-lot figures are arithmetic 5x fixed-lot scaling with drawdown percentages recomputed from 100,000 THB, without margin or stop-out simulation.
- Current hashes of all 16 recorded source/lock inputs match `out/LOCK.json`; the lock digest matches `LOCK.sha256`. `RUN_INPUTS.json` and `LOCK.json` contain identical source and 2010–2016 data-hash manifests. The audit did not rehash price caches. This supports file consistency, not independent proof of when the preregistration was authored.
- Training JSON reproduces the locked A/B reference: 2,737 trades, net 353,805.25 THB and equity drawdown 29,686.87 THB. The loader asserts these metrics in design. The audit did not rerun the baseline on market data.
- Selection is empty. `VALIDATION.json` records `NO_TRAINING_CANDIDATE`, no rows and `years_read: []`. Static control flow returns before 2017–2019 data hashing/loading; a synthetic mocked branch test also passed with both operations set to fail if called. The restricted loader guards years before opening caches. No 2020+ quote path is called by this study.

## Required reporting clarifications and limits

1. `gross_wins`/`gross_losses` and `profit_factor` in `trial.metrics` use the sum of positive/negative **after-cost trade P/L** (`trades[:,5]`). This is the usual trading profit factor, not pre-cost midpoint P/L (`trades[:,4]`). Label it explicitly as after-cost PF in the report. The checks PF>1 and net>0 are algebraically redundant for these fully closed trades; that redundancy does not invalidate selection. Do not describe the output field as a verified pre-cost profit factor.
2. Ma's original whole-period training eligibility includes 219 pre-2013-07-05 trades, before the supplied introduction date for the source mechanism. They are a clock-pattern placebo, not evidence of SHFE night-opening behavior. Report that original inclusion prominently and retain the frozen decision. The descriptive pre-introduction net is -8,081.67 THB and post-introduction net is -24,248.04 THB; 2014–2016 is also negative. Do not silently rerun selection on the post-introduction subset.
3. The inherited calendar is a conservative New York strategy policy, not a verified historical broker or SHFE holiday archive. In particular this adaptation does not independently enforce China's exchange trading calendar. A Shanghai-clock XAUUSD result cannot validate a futures liquidity/volume mechanism. Exact paper formulas/effect sizes for Ma were unavailable in supplied notes; the custom clock/formula is explicitly an adaptation.
4. Xu transfers ETF evidence to XAUUSD and Ma transfers futures behavior to quote-only XAUUSD. No volume, order flow, auction fills, depth, or independent cross-market series is present in the local experiment. These limits are disclosed in the plan and feasibility note.
5. Daily t-statistics are descriptive unadjusted statistics, without an autocorrelation-robust inference procedure or multiple-testing correction. Previous adaptive searches and already-reused 2017–2019 prevent treating any future use of those years as a fresh holdout. Positive A/B+C combined profit comes from the profitable A/B baseline and is not evidence that a negative C adds value.
6. Standalone 0.5-lot arithmetic paths fall below zero equity and can show drawdown over 100%. These are scaling illustrations, not executable-account survival or margin simulations.

## Verification performed

`D:/xau-ml-scalper/.venv/Scripts/python.exe -B -m unittest test_synthetic -v`: all 8 tests passed. Additional synthetic-only checks passed for missing-next-minute cancellation, delayed observed timed exit, New York DST cutoff conversion, weekend/holiday/cutoff blocks, and the empty-selection no-data-read evaluation branch. An initial temporary-file version of the branch check hit the environment's temporary-directory permissions; the completed replacement used fully mocked paths and performed no file writes.

The audit validates the implementation and reported control flow within this scope. It does not independently certify historical quote accuracy, exchange-calendar completeness, bibliography, or an operating-system-level record of every file read by earlier runs.
