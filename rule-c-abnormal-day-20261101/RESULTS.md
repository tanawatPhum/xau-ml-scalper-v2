# Prior abnormal day Rule C — not confirmed

1 November 2026. **The frozen primary passed training but failed 2017–2019 evaluation. Do not add it to the live version.** No retuning or additional candidates were tried. No2020+ prices were read. All amounts below are THB;0.1lot=10oz per rule, FX33.77, start100,000.

The idea adapts Caporale and Plastun (2021), [DOI10.1007/s11408-021-00380-w](https://doi.org/10.1007/s11408-021-00380-w). Their reported next-day gold trading evidence was weak and excluded transaction costs. Our60-day z score, data-quality rules and clock choices are local research choices, not a proven profitable formula from the paper.

The previous complete UTC+03 calendar day must have>=1000 available real quotes, a first quote within120minutes of midnight and a last quote within120minutes of day-end. Its log last/first mid return is compared with the latest60 valid returns strictly before that date, using sample SD. If |z|>2, enter opposite that day's return on the exact minute after the new date's first eligible observed quote before06:00. Missing previous dates cannot carry a Friday signal into Monday. Exit at the earlier existing16:55NY deadline or06:00UTC+3, on the first real quote. Primary has no stop/target; a fixed3scale stop is sensitivity only. [Frozen plan](PLAN.md).

| Primary, fixed spread0.168USD/oz | Training2010–2016 | Evaluation2017–2019 |
|---|---:|---:|
| Closed trades |74|37|
| Net |23,609.79|−4,419.48|
| Profit factor, after costs |1.625|0.775|
| C entries during A/B union |9/74=12.16%|1/37=2.70%|
| Maximum minute-equity DD |17,861.29(14.99%)|13,909.19(13.49%)|
| Example commission/slippage net |22,110.40|−5,169.17|
| Historical BID/ASK net |15,008.06|−6,292.36|
| A/B fixed-spread net |353,805.25|36,020.26|
| A/B+C fixed-spread net |377,415.04|31,600.78|
| A/B+C minute-equity DD |29,686.87(11.83%)|29,179.31(23.38%)|

Example costs add commission0.01 and slippage0.02USD/oz per side. PF divides gains of net-winning trades by absolute losses of net-losing trades. Combined example/historical fields in raw JSON retain fixed-cost A/B and vary C costs only; all portfolio comparisons shown here use fixed costs consistently. Training2014–2016 primary net was only **+605.83** under fixed spread, **−2.03** with example costs and **−1,680.40** with historical BID/ASK. These recent sensitivity failures are disclosed without changing the frozen gate, which required positive recent fixed-spread net and positive whole-period example-cost net.

Training passed all10 predeclared checks. Evaluation failed positive net, PF>1 and positive example-cost net; it passed minimum20 trades, overlap<=30%, positive equity, and execution safety. Recent2014–2016 is inapplicable to evaluation (the legacy metric field name is retained in JSON, but does not denote those years there). Fixed3scale stop sensitivity returned+27,674.01 training and−7,316.27 evaluation; example costs+26,174.62/−8,065.96 and historical+19,085.45/−9,171.59. It was never eligible to replace the primary.

| Year | C trades | C net | A/B+C net |
|---|---:|---:|---:|
|2010|11|6,446.36|79,332.48|
|2011|16|13,733.58|166,057.22|
|2012|7|−2,036.67|37,755.70|
|2013|10|4,860.68|46,709.14|
|2014|11|1,372.08|21,943.41|
|2015|13|−1,294.74|31,796.99|
|2016|6|528.50|−6,179.91|
|2017|10|−1,688.84|14,470.28|
|2018|14|3,114.27|6,769.03|
|2019|13|−5,844.91|10,361.48|

Post-outcome description by New York UTC offset at entry, with no selection change:

| Period / offset | Trades | C net | A/B overlap | Median hold |
|---|---:|---:|---:|---:|
|Training/winter−05|24|−1,321.42|9/24=37.50%|54min|
|Training/summer−04|50|24,931.21|0/50|298min|
|Evaluation/winter−05|13|1,371.06|1/13=7.69%|54min|
|Evaluation/summer−04|24|−5,790.54|0/24|298min|

Winter UTC+3midnight is16:00NY;24 training and13 evaluation trades closed at00:55UTC+3 before the break. Summer trades typically entered01:02 and closed06:00. Training profit was concentrated in the longer summer window and did not persist. These are distinct holding windows imposed by the unchanged A/B calendar; this result is not evidence for holding through the break or for selecting summer-only/winter-only rules.

At0.5lot per rule, DD percentages were recomputed from scaled minute equity starting100,000; they were not multiplied by5. No compounding or margin/stop-out simulation:

| Period / system | Net | DD | DD% | Minimum equity |
|---|---:|---:|---:|---:|
|Training/C|118,048.94|89,306.45|49.62%|87,200.33|
|Training/A/B|1,769,026.25|148,434.35|30.44%|96,307.25|
|Training/A/B+C|1,887,075.20|148,434.35|27.57%|96,307.25|
|Evaluation/C|−22,097.40|69,545.94|60.23%|45,924.10|
|Evaluation/A/B|180,101.32|108,677.77|49.36%|95,903.70|
|Evaluation/A/B+C|158,003.92|145,896.53|65.12%|78,133.08|

Training finalized1,938 observed dates, of which1,638 met quality; evaluation825/694. Failure reasons overlap: insufficient quotes131/52, late first quote151/67, early last quote159/73. Missing intervening dates618/268 include weekends; invalid/missing immediately previous dates skipped535/234 observed current dates. Insufficient60-day history skipped56 training dates and zero evaluation dates. Two abnormal dates in each period had no eligible quote before06:00. All74/37 signals filled. One terminal date per period remained unfinalized. Zero C market-close/session crossings, late expiry exits, >30minute gap-spanning trades or terminal positions occurred, across primary and stop sensitivity.

Evaluation began with fresh A/B positions and volatility on2017 quotes. C used61 completed valid2016 daily records solely to supply the previous-date/reference history; its eff scale also began fresh2017. The last partial2016 date was explicitly invalid. This is a fresh-period C test but the project's2017–2019 period was previously reused, so it is exploratory rather than pristine holdout evidence.

Evidence: [TRAINING](out/TRAINING.json), [VALIDATION](out/VALIDATION.json), [LOCK](out/LOCK.json) and [SHA](out/LOCK.sha256), [VERIFICATION](out/VERIFICATION.json), [descriptive splits](out/DESCRIPTIVE.json), [verification notes](VERIFICATION.md). Original pre-outcome INPUTS was preserved; INPUTS_v2 recorded a reviewer-requested cache-integrity check before any outcome. A/B sources/calendar/locks and root registry were unchanged. The failed evaluation ends this bounded experiment.
