# Local feasibility and the Rule C literature bridge

## What data and execution are actually available?

### Takeaway
The established research cache contains only UTC minute BID/ASK closes, not OHLC, volume, order flow, trades, depth, futures, or options. The original raw CSVs do contain OHLC and a volume field, but none of these new experiments needs to read the original prices or rebuild the cache.

### Cited Findings
- Direct inspection of `M1_2010.private.npz` found exactly `base` (scalar int64), `bid`, and `ask` (525,600-element float64 vectors). The cache builder keeps only close values and requires each side to be active by volume>0 or high>low. Raw 2010 BID CSV header is `timestamp_utc,open,high,low,close,volume`. — [cache builder](D:/xau-ml-scalper-claude/microstructure-edge-map/code/load.py)
- The safe loader rejects invalid/unsorted/duplicate years before opening files; design permits only 2010–2016, evaluate only 2010–2019. It validates finite positive noncrossed quote pairs and reconstructs UTC minutes from each year's base. — [safe loader](D:/xau-ml-scalper-claude/v1-r1/study.py)
- `v1_r2` imports `extend_2022` as code, but does not call its loader on import; the new experiment calls only the restricted `study.load_prices` via `run_study.load`. The new study never calls `extend`, opts into its loader, or opens 2020+ cache files. — [v1-r2 source](D:/xau-ml-scalper-claude/v1-r2/v1_r2.py), [restricted context loader](D:/xau-ml-scalper-claude/v1-r1/daily/run_study.py)
- The existing causal research replay enters only at the exact following minute, cancels a missing entry minute, detects stop/target from observed closes, exits at the subsequent observed quote, and does not invent an end-of-data liquidation. A >30-minute observed gap forces exit at the first actual quote. — [research replay](D:/xau-ml-scalper-claude/rule-c-research-20261101/replay.py)
- Calendar timestamps use `America/New_York`: flatten16:55, close16:58, reopen18:01, Sunday18:05; deterministic holiday blackouts forbid new risk. These are conservative policy dates, not a complete verified broker holiday archive. — [calendar](D:/xau-ml-scalper-claude/v1-r1/daily/calendar_rules.py)

### Inferences
- Minute-close timing transfers are feasible. Tick-level liquidity, order-book imbalance, signed futures order flow, inventory, precise auction fills, OHLC barrier ordering, options hedging, and realized macroeconomic surprise models cannot be honestly reconstructed from this cache.
- Exact local-time anchors must be converted from UTC with a timezone database. London and New York DST changes differ for several weeks each year, so fixed UTC shifts are invalid.
- Require exact anchor quotes and contiguous signal windows; do not forward-fill an unavailable anchor. Fixed next-minute entry and delayed close-based stop exits bound what execution claims can be made.

### Gaps
- The raw `volume` field's economic meaning and comparability are not verified. It is not a known consolidated traded-volume series.
- No independent broker/futures cross-source confirmation or historical release-calendar dataset is available in these local hooks.
- Old requested microstructure/pattern narrative summaries include historical 2017–2022 aggregates. They were read for the prior-test inventory; no 2020+ quotes or result arrays were opened for this new study. Their aggregate outcomes are not new validation evidence.

## Which previous tests make a proposed idea already explored?

### Takeaway
The failed48-cell search does not exhaust economic mechanisms, but scheduled-clock fades and NY16:00 reversal are already examined. Merely attaching literature to one of those same fades would be a repeat; an earlier-window-to-late-window directional signal is materially different.

### Cited Findings
- The latest24+24 search covered failed-breakout reclaims, rolling-mean reentry reversals, and compression breakouts, then reversed all directions after seeing training failures. Windows30/60/240, thresholds, and holds30/90 formed bounded grids; the sole selected continuation candidate lost711.70THB at0.1lot on reused2017–2019, despite natural entry overlap1.94%. — [first plan](D:/xau-ml-scalper-claude/rule-c-research-20261101/PLAN.md), [adaptive follow-up plan](D:/xau-ml-scalper-claude/rule-c-research-20261101/continuation/PLAN.md), [results](D:/xau-ml-scalper-claude/rule-c-research-20261101/RESULTS.md)
- Earlier Rule C round2 already faded strong moves into LBMA10:30/15:00 London, US08:30data, NY09:30equityopen, and COMEX13:30NY. It pooled five slots at15/30-minute horizons and reported per-slot descriptives. Both pooled cells failed2010–2016; the AM30-minute positive descriptive was explicitly labeled selected after the fact. — [round2 plan](D:/xau-ml-scalper-claude/swing-v2-ruleC-r2/PLAN.md), [round2 training results](D:/xau-ml-scalper-claude/swing-v2-ruleC-r2/RESULTS.md)
- NY16:00 fade, two same-direction segments into16:00, prefix/hour/volatility patterns, and broad hour-conditioned strong-move momentum/reversal were already mapped. The exact16:00 hypothesis was subsequently parked in earlier Rule C plans. — [edge-map plan](D:/xau-ml-scalper-claude/microstructure-edge-map/PLAN.md), [pattern plan](D:/xau-ml-scalper-claude/pattern-structure/PLAN.md), [parked scope](D:/xau-ml-scalper-claude/swing-v2-ruleC-r2/PLAN.md)

### Inferences
- A GLD11:30–12:00 to15:30–16:00 momentum transfer is distinct from fading the immediately preceding15/30-minute move into a clock slot. It shares a closing-window clock with old work, so it is a transfer pilot rather than a new discovery of the16:00 anomaly.
- Exact dated macro release surprises, auction imbalance, intermarket lead-lag, and signed volume remain potential information additions, but the local close-only cache cannot supply those variables.
- No claim is made that a positive trial would erase the prior adaptive search history or produce a virgin holdout.

### Gaps
- Broader prior work includes additional swing/follow/stop families beyond the latest48. Their existence reduces novelty and increases the effective research search size; no global multiple-testing count is reconstructed here.

## What protocol can bridge verified literature into a bounded local trial?

### Takeaway
Use at most two economically distinct paper-derived primary specifications and report a single fixed3-volatility stop sensitivity for each; do not choose whichever exit works. Freeze all candidate rules, eligibility, code and2010–2016 selection before opening2017–2019.

### Cited Findings
- The inherited baseline is locked v1-r2 D058-S1 at0.1lot per rule. Its training lock records2,737trades, net353,805.25THB, equityDD29,686.87THB and zero market-close/session crossings. Only its locked source, lock, and original restricted loader are used; no version or registry change is authorized. — [r2 lock](D:/xau-ml-scalper-claude/v1-r2/out/LOCK.json), [r2 plan](D:/xau-ml-scalper-claude/v1-r2/PLAN.md)
- Root's verified Scite evidence supplied Xu, Bouri, Saeed and Wen(2020), DOI10.1016/j.resourpol.2020.101830: GLD minute data2004-11-08–2019-05-30;11:30–12:00NY predicts15:30–16:00NY, coefficient.0436,t3.03,R².49%, OOSR².26%. Reported sign timing t1.23,success53% is weak gross evidence and does not establish after-cost XAUUSD profitability. The mean-return unit was not verified and is omitted. — [paper DOI](https://doi.org/10.1016/j.resourpol.2020.101830) (primary verification performed by literature researcher; this local branch does not independently browse)
- Root supplied Ma,Bouri,Xu&Zhou(2025), DOI10.1016/j.gfj.2025.101084: Scite metadata/publisher preview describes SHFE minute gold/silver night opening, reversal followed by momentum and liquidity/anchoring interpretation. Full text is unavailable. Shanghai21:00–21:30 impulse,21:30–22:00 partial opposite retracement,22:01–23:00 original-direction trade is our explicit transfer specification, not a claimed paper replication. Pre2013-07-05 data is a placebo regime because it predates SHFE night sessions. — [paper DOI](https://doi.org/10.1016/j.gfj.2025.101084)
- The existing replay and baseline post-execution gross exposure let overlap count the union of A/B once per C entry, include simultaneous entries, ignore direction, and exclude A/B positions exited in that same minute. — [replay](D:/xau-ml-scalper-claude/rule-c-research-20261101/replay.py), [baseline execution](D:/xau-ml-scalper-claude/v1-r1/daily/execution.py)
- Completed local pilots: Xu primary net−73,091.96THB, PF.805,1,690trades,375entry overlaps(22.19%); Night primary net−32,329.71THB, PF.877,443trades,53entry overlaps(11.96%). Both fixed3vol stop sensitivities also lose. Every C close/session/gap/late/terminal count is zero. Both fail fixed/example profitability and2014–2016profitability; locked selection is empty and2017–2019validation was not opened. — [trial results](D:/xau-ml-scalper-claude/rule-c-literature-20261101/RESULTS.md), [training](D:/xau-ml-scalper-claude/rule-c-literature-20261101/out/TRAINING.json), [no-validation status](D:/xau-ml-scalper-claude/rule-c-literature-20261101/out/VALIDATION.json)
- Night postlaunch2013-07-05–2016 descriptive subset:224trades, net−24,248.04THB, example-cost net−28,786.73THB, historical net−33,560.29THB,21overlaps(9.375%), equityDD40,447.00THB. Prelaunch placebo219trades net−8,081.67THB. Original all2010–2016 eligibility was preserved after the prelaunch-regime caveat was noticed after outcomes; no reselection or amended hypothesis followed. — [postlaunch descriptive accounting](D:/xau-ml-scalper-claude/rule-c-literature-20261101/out/NIGHT_POSTLAUNCH_DESCRIPTIVE.json), [failed protocol and caveat](D:/xau-ml-scalper-claude/rule-c-literature-20261101/RESULTS.md)
- Eight synthetic tests and both real-prefix checks pass. Independent A/B trade-interval reconstruction matches both overlap counts; fixed/historical fill arithmetic and closed/yearly totals reconcile. Baseline training metrics reproduce exactly; locked source and2010–2016data hashes remain unchanged. — [verification](D:/xau-ml-scalper-claude/rule-c-literature-20261101/VERIFICATION.json)

### Inferences
- Minimum counts50training/20validation, positive2014–2016 net, profit factor>1, positive fixed/example-cost net, natural entry overlap<=30%, and zero close/session crossings/terminal positions are explicit local implementer criteria, not findings claimed from the paper.
- Fixed spread.168USD/oz; example commission.01+slippage.02USD/oz/side; FX33.77;10oz=0.1lot; fresh100,000THB per study period. Historical bid/ask is a sensitivity, never selection.0.5lot reporting multiplies fixed-lot profit by5 and recomputes equityDD percentages from the100k start.
- New outputs belong only to `rule-c-literature-20261101`. `NUMBA_CACHE_DIR` points there and Python runs with `-B`, so imports do not change locked source folders.
- Paper claims are hypothesis-generating. ETF-to-CFD transfer, tiny forecastR², uncertain full trading costs, reused validation and previous searches all limit any apparent pass.

### Gaps
- Both primary specifications and fixed3vol stop sensitivities are now recorded in the final protocol before any new market-outcome test: exactly4cells. The second source's detailed formulas/effect sizes are unavailable; the pilot is a mechanism transfer with that limitation disclosed.
