# Literature-to-Rule-C pilots: NOT_CONFIRMED

Both paper-derived primary transfers failed2010–2016 training after costs. The two fixed3volatility stop sensitivities also failed. No2017–2019 validation prices were opened, and no2020+ prices were opened. A/B and version records remain unchanged.

The final protocol, two primaries and two nonselectable stop sensitivities were written before outcomes. At0.1lot(10oz), FX33.77, spread.168USD/oz, fresh100,000THB. Example costs additionally charge commission.01 and adverse slippage.02USD/oz/side. Historical quotes use both entry/exit BID/ASK spreads.

| Cell | Fixed netTHB | Example netTHB | Historical netTHB | PF | Trades | Natural overlap |2014–2016netTHB | EquityDDTHB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|C_Xu_midday_to_close|-73,091.96|-107,334.74|-208,609.78|0.805|1690|375/1690=22.19%|-40,593.06|74,710.38|
|C_Xu_midday_to_close +stop3 sensitivity|-73,137.55|-107,380.33|-208,638.83|0.805|1690|375/1690=22.19%|-40,593.06|74,755.97|
|C_Ma_night_reversal_momentum|-32,329.71|-41,305.78|-58,765.20|0.877|443|53/443=11.96%|-30,242.22|48,107.39|
|C_Ma_night_reversal_momentum +stop3 sensitivity|-30,560.84|-39,536.90|-57,040.57|0.883|443|53/443=11.96%|-29,532.37|45,863.37|

All four cells pass the overlap<=30%, minimum50trades, and calendar/terminal-position checks; all fail net>0, PF>1, positive2014–2016 and positive example-cost net. Market-close crossings, session crossings, late-cutoff exits, >30minute gap-spanning trades and terminal positions are all zero for these C cells. No A/B position veto was used. Simultaneous entries count, A/B exits on that minute do not, and A+B holding counts once.

## Exact adaptations and evidence limits

Xu,Bouri,Saeed&Wen(2020), DOI[10.1016/j.resourpol.2020.101830](https://doi.org/10.1016/j.resourpol.2020.101830): GLD11:30–12:00NY direction predicts15:30–16:00NY. Local adaptation signals15:29, fills15:30, exits16:00. Original regressionR²=.49%,OOSR²=.26%; reported sign-timing t=1.23 is weak. Mean-return units were not independently verified and are omitted. This ETF finding is not an after-cost XAUUSD claim.

Ma,Bouri,Xu&Zhou(2025), DOI[10.1016/j.gfj.2025.101084](https://doi.org/10.1016/j.gfj.2025.101084): metadata/publisher preview describes SHFE gold/silver night-session reversal followed by momentum. Full text was unavailable. Our Shanghai21:00–21:30 impulse,21:30–22:00 opposite partial retracement,22:01entry/23:00exit is a mechanism transfer, not a paper replication. Direction follows the original impulse; no optimized magnitude threshold or target.

The frozen Night eligibility used all2010–2016, even though the pre2013-07-05 period predates the SHFE night session and belongs only to a placebo regime. This is an explicit protocol limitation. It was noticed after outcomes had finished, so the failed protocol was preserved without amendment/reselection. Prelaunch observations are not evidence for a night-market mechanism; the postlaunch subset below is descriptive only.

| Night subset | Trades | Fixed netTHB | Example netTHB | Historical netTHB | Natural overlap | EquityDDTHB |
|---|---:|---:|---:|---:|---:|---:|
|Primary from2013-07-05|224|-24,248.04|-28,786.73|-33,560.29|21/224=9.38%|40,447.00|
|Stop3 sensitivity from2013-07-05|224|-23,538.20|-28,076.88|-32,880.50|21/224=9.38%|39,591.78|

Prelaunch placebo: primary219trades net-8,081.67THB; fixed-stop sensitivity219trades net-7,022.64THB. Neither regime is used to rescue selection.

## Portfolio effect and0.5lot scaling

Locked A/B baseline: net353,805.25THB, equityDD29,686.87THB,2,737trades. It reproduces the r2 lock exactly.

| Primary | A/B+C net0.1lotTHB | A/B+C DD0.1lotTHB | C net0.5lotTHB | C DD0.5lotTHB | C lowest equity0.5lotTHB |
|---|---:|---:|---:|---:|---:|
|C_Xu_midday_to_close|280,713.29|36,226.26|-365,459.78|373,551.92|-272,776.90|
|C_Ma_night_reversal_momentum|321,475.54|40,933.12|-161,648.55|240,536.96|-67,227.35|

Both additions lower A/B net and increase absolute equityDD.0.5lot uses fixed5×dollar exposure, recomputes DD% against100k, and is not executable C-only capital history once equity is nonpositive. The model has no margin call, stop-out, funding or size-dependent impact.

## Annual fixed-spread net at0.1lot

| Year | Xu primaryTHB | Xu stop3THB | Night primaryTHB | Night stop3THB |
|---|---:|---:|---:|---:|
|2010|-14,900.00|-14,945.59|12,189.62|11,714.48|
|2011|1,879.13|1,879.13|-26,523.30|-27,081.85|
|2012|-10,218.30|-10,218.30|6,287.97|7,975.63|
|2013|-9,259.73|-9,259.73|5,958.21|6,363.28|
|2014|-13,242.74|-13,242.74|6,113.89|5,968.51|
|2015|-15,648.34|-15,648.34|-12,388.52|-11,849.39|
|2016|-11,701.98|-11,701.98|-23,967.58|-23,651.49|

## Verification and scope

Eight synthetic checks pass: two-sided signal direction, DST clocks, missing anchor/window rejection, signal-prefix invariance, next-minute fills/timed exits/cost arithmetic, A/B union and forbidden-year checks. Both real-data prefix checks ended with an open position and reproduced the full historical prefix without terminal forced liquidation. An independent trade-interval reconstruction matches baseline gross exposure and both overlap counts; closed/net/yearly sums and fixed/historical fill costs reconcile. Source and2010–2016data hashes remain unchanged.

Sources: `PLAN.md`, `signals.py`, `trial.py`, `test_synthetic.py`; frozen outputs `out/TRAINING.json`, `out/LOCK.json`+SHA, `out/VALIDATION.json`; postlaunch-only descriptive accounting `out/NIGHT_POSTLAUNCH_DESCRIPTIVE.json`; checks `VERIFICATION.json`. The all-years failed selection is empty; validation status isNO_TRAINING_CANDIDATE.

The previous48structural trials and earlier clock fades make this a continuation of a large research search.2017–2019 is reused exploratory validation, not a virgin holdout. Old requested narrative summaries include2017–2022aggregates; those were inspected only for prior-test inventory, with no2020+ quote/result arrays opened by this pilot. No further recipe, opposite-direction rescue, parameter tuning or version promotion follows these failures.
