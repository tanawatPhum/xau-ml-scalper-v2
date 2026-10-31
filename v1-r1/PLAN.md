# v1-rx: owner-authorized outcome-informed tuning

Owner request: design using the2010-2016 answer key; trade simulation must never
know future data; evaluate2010-2019; develop under v1-rx and report honestly.

## Baseline and scope
Use the corrected causal execution of Swing v1, at equal0.1lot per rule (10oz),
100,000THB start, FX33.77, fixed spread0.168USD/oz. Snapshot the engine unchanged.
Do not tune by increasing exposure. Additional0.5lot numbers are linear scale
illustrations. No new reads of2020+ in this study.

Execution stays the already-audited one-minute delayed fills, delayed close stop,
post-gap exits, no retrospective closure, and minute liquidation equity.
Only causal entry rules and swing thresholds are candidates. Preserve every
confirmation for exit management even when its entry eligibility is filtered.

## Bounded search before any new2017-2019 run
1. Read2010-2016 outcomes for diagnosis (authorized answer key).
2. Coarse neighborhood search per rule, max96 cells each:
   A k={.75,1,1.25,1.5}, minUSD={1.5,2.1626934441569983,3,4},
     leg={2.5,3.5,5}; B k={1,1.25,1.5,2}, minUSD={0,1.5,2.1626934441569983,3},
     leg={2.5,3.5,5}. A uses max(sigma60,sigma1440), B sigma60.
   Include exact baseline. No outcome-conditioned runtime decisions.
3. Keep up to3 per-rule leaders on2010-2016 return/equity-DD, plus baseline.
   For these, limited causal filters: skipAsiaUTC0-6; skipNYUTC13-20;
   skipLateUTC21-23; require sigma60/sigma1440 >=.75 or >=1;
   require ratio <=1.5. Training-only diagnosis also found material direction
   differences, so add long_only and short_only before any validation access.
   Add utc_morning(0-11) and utc_london(7-11), supported in BOTH training halves
   by the diagnostic, before the policy search. Compare at most11 policies per
   seed. No further additions after this bounded set. Do not add timeouts: checkpoint diagnosis
   found continuation after60/120min adds profit despite eventual-long-hold losses.
4. Keep at most6 per-rule choices including baseline. Evaluate <=36 portfolios.
   An eligible improvement must have training net>=1.05*baseline,
   equity-DD<=.90*baseline, total closed losses<=baseline, closed trades>=50%
   baseline, nonnegative equity, and improve net in2014-2016 versus baseline.
   Rank eligible by net/equity-DD; ties prefer fewer parameter changes. Report
   worst-trade loss, annual figures and both2010-13/2014-16 subtotals as checks.
   If none qualify, lock the best net/DD candidate with explicit training FAIL;
   do not weaken the declared gate or imply improvement was guaranteed.
5. Save LOCK.json with parameters, selection metrics, source/data hashes, and
   UTC time BEFORE running2017-2019. No redesign after seeing its outcome.

## Evaluation
Run locked and baseline2010-2019 continuously; separately run2017-2019 from100k.
Report2010-16,2017-19, full2010-19 and every year, comparing net, liquidation-DD,
total closed losses, worst trade and trade count. Confirmation requires BOTH
higher2017-19 net and lowerDD/loss total than baseline (no retuning).
Use historical spread and hypothetical commission.01/slippage.02 per side only
as frozen sensitivity runs after locking, never for selection.
2017-2019 was seen in older work: this is a reused validation period, not a new
untouched holdout.2010-2016 is explicitly in-sample.

## Verification and outputs
Tests: default parity, real-signal prefix invariance, filters keep exit events,
time-of-signal feature availability, strict training/year boundary, deterministic
selection and lock integrity. Independent review before final assessment.
Keep caches/trades/curves local under *.private.*; record all candidate metrics.
No Git exists here; isolate work in this folder, preserve previous experiments.

## Progress
- [x] Snapshot baseline and build tested signal customization.
- [x] Training-only diagnosis and bounded search.
- [x] Lock selected rules before new validation run.
- [x] Evaluate frozen choice and sensitivity, verify and report.

## Disclosed secondary amendment (after initial selection)
The original search and immutable LOCK remain intact:176 single-rule variants,
36 portfolios, no candidate passing ALL original gates, fallback P01 selected.
P01 reduces risk but also profit and is NOT a successful original selection.

The training table also contains P20 with +15.27%net,-49.93%DD,-54.29%total losses,
2705trades versus5873baseline. It fails ONLY the self-imposed50%trade-count floor;
its46.06%retention and thousands of trades merit evaluation for the user's actual
profit/loss objectives. Remove ONLY this floor in a separately recorded secondary
selection; retain every other gate and the identical ranking. Independent
training-only review confirms exactly P20,P21,P22 qualify and P20 ranks first.

No new strategy search, parameter tuning or candidates. balanced.py reads the
existing2010-2016 table and freezes a separate lock before evaluating P20. The
original fallback's evaluation is already available; therefore label this
post-search amendment and its reused2017-2019 validation as exploratory, not a
preregistered or untouched holdout success. Keep both favorable and unfavorable
results. No further amendments or redesign in this study.
