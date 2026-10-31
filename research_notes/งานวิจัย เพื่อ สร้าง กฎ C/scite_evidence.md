# Scite evidence for a complementary intraday gold Rule C

Research date: 1 November 2026. This branch used Scite literature search, paginated full text, two forward citation graphs with Smart Citation context, and primary publisher/author-repository pages when Scite access was incomplete. It did not inspect local market prices, run trials, edit project code, or read 2020+ local price data. Raw retrievals and all screened metadata are in [scite_sources.json](scite_sources.json) and [rawdata/scite_raw.json](rawdata/scite_raw.json).

The coordinator's task constraints are treated as requirements, not literature findings: r2 A/B are pullback-continuation; C must be profitable after costs; no more than 30% of C entries may occur while A or B is holding; no A/B veto may be used to manufacture that result. The earlier 48-rule failures and previously tested fixing/session fades are supplied project history. These notes do not claim any candidate passes those requirements.

## Which primary findings actually support price-only, same-day gold experiments?

### Takeaway

The most specific usable finding is delayed GLD return predictability, but its own gross trading evidence is weak. A newer SHFE paper motivates a reversal-then-momentum sequence, with materially incomplete access. Neither establishes an executable after-cost XAUUSD M1 edge. [Xu et al., 2020](https://doi.org/10.1016/j.resourpol.2020.101830); [Ma et al., 2025](https://doi.org/10.1016/j.gfj.2025.101084).

### Cited Findings

**1. Xu, Bouri, Saeed, and Wen (2020): delayed GLD signal.** Full Scite body read in six pages. GLD sample: 8 November 2004–30 May 2019; Reuters 1-minute input aggregated to 13 US half-hours. The fifth return predicts the last: beta 0.0436, Newey–West t = 3.03, R² = 0.49%, 3,532 observations. The first return is insignificant. The expanding-window, second-half evaluation reports GLD OOS R² = 0.26%; however, predictors were selected by in-sample significance. High first-half-hour realized volatility strengthens the reported relation. Table 8's GLD timing t = 1.23 and success rate = 53% temper the broad economic-value language. Displayed mean = 0.81 has an unresolved scaling legend; do not call it 0.81 bp without verification. Explicit transaction-cost deductions were not established in the served text. Exact excerpt, 12 words: “the fifth half-hour returns exhibit significant and positive predictive power”. [Paper](https://doi.org/10.1016/j.resourpol.2020.101830).

**2. Ma, Bouri, Xu, and Zhou (2025): reversal followed by momentum after a session opening.** Scite metadata verified; Scite fulltext returned no readable text. Publisher abstract/introduction/section preview describes SHFE gold/silver 1-minute data aggregated into half-hour returns. After introduction of night trading, the first night half-hour becomes the predictor, replacing the first daytime half-hour. Subsequent reversal is followed by momentum; the authors interpret this as uninformed liquidity oversupply/anchoring rather than a permanently wrong initial price. Benchmark outperformance is reported, but exact predictive half-hours, sample bounds, OOS design, transaction costs, and numerical net returns were unavailable. Exact excerpt, 5 words: “intraday momentum following intraday reversals”. [Paper and primary publisher preview](https://www.sciencedirect.com/science/article/pii/S1044028325000110).

**3. Caporale and Plastun (2021): large-day continuation and next-day reversal.** Entire readable Scite body read. Methods use MetaQuotes daily/hourly gold and oil, 1 January 2009–31 March 2020, GMT+3; introduction gives inconsistent earlier end dates. Abnormal-day classification uses a dynamic two-standard-deviation threshold. Gold shows same abnormal-day continuation and next-day contrarian behaviour; after positive abnormal days, the latter is most pronounced by 06:00 GMT+3. Crucially, next-day gold simulation is not statistically different from random, costs are excluded, timing is estimated from the sample, and expected returns in CAR are calculated over the whole sample. Some tables/formulas are lost in text extraction. Exact excerpt, 8 words: “Our analysis does not incorporate transaction costs”. [Paper](https://doi.org/10.1007/s11408-021-00380-w).

**4. Caminschi and Heaney (2014): fixing start matters; informed sign is not causal for outsiders.** Scite first 16,000 body characters read, plus metadata and publisher/repository crosscheck. GC/GLD 1-minute OHLC/volume, XAU= pre-fix spot reference, 2007–2012; end-time subsample 18 August 2011–2012. Around 15:00 London, reported informed advantage is about 10 bp in the first four minutes; activity rises before publication. Directional returns are signed using eventual fixing price versus pre-fix spot, an unavailable future outcome at trade entry. Exact excerpt, 14 words: “However, we find no significant returns following the end of the fixing.” The claim concerns an opaque old auction, not a modern public price-only strategy. Cite issue year 2014; Scite indexes online year 2013. [Paper](https://doi.org/10.1002/fut.21636); [author repository](https://research-repository.uwa.edu.au/en/publications/fixing-a-leaky-fixing-short-term-market-reactions-to-the-london-p/).

**5. Aspris, Foley, and O’Neill (2020): auction reform changes costs.** First 24,000 Scite body characters read. Five-second futures/ETF trade and quote data cover 14 February 2012–30 June 2015; gold's transparent auction begins 20 March 2015. Quoted/effective spreads decline and depth improves after reform. The authors corroborate old-regime leakage but interpret new-regime price discovery as compatible with real-time public imbalance disclosure; how prices incorporate information is not significantly changed. It is a market-quality study, not validation of a retail trading rule. Exact excerpt, 17 words: “observe no significant change in terms of how information is impounded into prices”. [Paper](https://doi.org/10.1002/fut.22120).

**6. Batten, Lucey, McGroarty, Peat, and Urquhart (2017): session patterns and costs are unstable.** First 24,000 Scite body characters read. Wholesale precious-metal spot prices/quotes, 5-minute intervals, May 2000–April 2015, three five-year subsamples. The paper documents periodicity in activity, returns, volatility and spreads. Gold bid–ask spread is generally steady intraday but rises around 22:00 GMT reopening; several distributional features change across subsamples. It does not validate net trading PnL. Exact excerpt, 12 words: “the behaviour of precious metals has changed substantially over time”. [Paper](https://doi.org/10.1371/journal.pone.0174232).

**7. Blose, Gondhalekar, and Kort (2018): overnight/day asymmetry, limited exact-rule access.** Scite has metadata but no readable body/abstract; primary Springer abstract and notes were read. It reports positive overnight and negative day returns across COMEX front futures, London Fix spot, stocks and gold funds, in up and down gold markets, with economic importance after costs. The exact common sample, trading boundaries and cost assumptions could not be inspected. The main overnight leg does not meet same-day-flat constraints, and London fixing returns are not M1 broker quotes. Exact excerpt, 11 words: “The results are economically important even with transaction costs.” Use issue year 2018; Scite indexes 2017 online publication. [Primary publisher](https://link.springer.com/article/10.1007/s12197-017-9403-0).

**8. Xiao, Yin, and Zhao (2020): why a jump alone does not identify a trade direction.** First 8,000 Scite body characters read. In 205 US broad-equity ETFs over 2002–2016, 57% of identified jumps have no matched news; those are followed by reversals lasting at least 60 minutes. News jumps initially continue for 15 minutes; scheduled versus unscheduled news also have different dynamics. This is equity evidence and requires a news database. Price-only XAUUSD cannot reproduce those labels. Exact excerpt, 8 words: “subsequent returns after no‐news jumps reverse strongly”. [Paper](https://doi.org/10.1111/jfir.12223).

**9. Hauptfleisch, Putniņš, and Lucey (2016): price discovery is not directional edge.** Metadata, excerpts and inbound context show intraday London OTC/New York gold data described as 1997–2014/17 years, with New York futures the larger average price-discovery contributor despite London's higher turnover. This cross-venue result does not supply a one-series, same-day directional rule. [Paper](https://doi.org/10.1002/fut.21775).

### Inferences

- **Rank 1: delayed noon-to-close transmission.** This is the cleanest paper-specified pair of disjoint signal/holding windows. Its economic prior is weak enough that a negative after-cost pilot would be unsurprising.
- **Rank 2: session impulse, temporary counterpressure, then original-direction recovery.** The SHFE finding suggests a sequence rather than simply fading or buying the latest move. Whether that mechanism transfers to global XAUUSD is unknown; Shanghai futures have different participants, opening restrictions and liquidity.
- **Rank 3, future falsification only: previous complete-day extreme followed by early next-day reversal.** This differs from fading a local pre-clock move but is downgraded by the original gold strategy's insignificant result.
- Mere increased volatility at a clock time, a causal economic story, higher prediction accuracy, and a statistically significant regression slope are each insufficient to demonstrate net C profit.
- Prior fixing/open/close fades already tested locally should not be relaunched under new names. The fixing evidence also provides no support for assuming post-publication drift.

### Gaps

No retrieved primary study jointly demonstrated executable XAUUSD broker bid/ask M1 after-cost profit, same-day liquidation, independence from A/B holdings, and the required 30% overlap ceiling. Complete SHFE methods and Table 8's GLD scaling remain unresolved.

## How should the coordinator translate the evidence into limited, causal trials?

### Takeaway

The two selected experimental families are transfers designed by this research team. Their price rules and clocks must be reported as hypotheses, not attributed to the papers as replicated trading algorithms. No more trials are proposed for the current request beyond the coordinator's four cells.

### Cited Findings

The source-specific rationale is the delayed predictor in GLD and the first-night-return reversal/momentum sequence in SHFE. Their empirical instruments and session structures differ from XAUUSD. [Xu et al., 2020](https://doi.org/10.1016/j.resourpol.2020.101830); [Ma et al., 2025](https://doi.org/10.1016/j.gfj.2025.101084).

### Inferences

**Trial family 1 — coordinator-selected exact transfer, not verified profitable.**

1. Compute completed New York 11:30–12:00 log-price return.
2. Freeze its sign by 15:29. Enter at the next executable 15:30 quote in that sign; close at 16:00 New York.
3. Use local timestamp conventions to choose exact M1 endpoints without peeking at the entry bar's final close.
4. Run the paper-motivated high-opening-volatility sensitivity only as the separately labelled extra cell. The source's first-half-hour RV includes ETF overnight information; a local XAUUSD proxy with prior-only rolling normalization is our adaptation.
5. Do not retime a failing signal across nearby half-hours. If the frozen after-cost test fails, record the failure.

**Trial family 2 — coordinator-selected sequence transfer, all exact conditions ours.**

1. Shanghai 21:00–21:30 gives initial sign.
2. Shanghai 21:30–22:00 must counter that sign with a partial pullback rather than complete erasure.
3. Enter original sign at 22:01, using only completed information; close 23:00 Shanghai.
4. Apply only the coordinator's one volatility sensitivity, with past-only threshold construction.
5. Report pre-night-trading history as a placebo/transfer test, not a replication of SHFE's post-reform result. Exact launch date and actual paper sample were not recovered from accessible content.
6. Compare with the prior simple-reclaim/continuation catalogue before treating this as novel. A new clock condition alone does not establish a new mechanism.

**Future idea 3 — not an additional trial in this request.** Define yesterday's complete-day return using a fixed GMT+3 boundary and standardize against only prior days. On a rare two-standard-deviation extreme, take the opposite sign early next day and flatten after a fixed six hours. A 60-day normalization window and symmetric six-hour holding period would be our choices, not recovered paper parameters. Skip rollover spread shocks and missing quotes using predeclared executable-data criteria, not outcome-dependent exclusions. This is only a low-confidence falsification target given the original negative significance check.

**Shared implementation/acceptance logic.** Compute features from mid or a fixed bid/ask convention and realize buys at ask/sells at bid, with fees/slippage and next-bar availability. Audit stale/missing quotes, timestamp offsets and DST. Keep every attempted cell in the experiment ledger. Count C entries with an A/B holding at the entry instant and divide by all C entries; evaluate every raw signal without an A/B veto. Report net expectancy, uncertainty, trade count, holding time, turnover, worst losses and overlap. Passing overlap without positive net expectancy does not qualify C.

### Gaps

These notes deliberately contain no local pilot results. The local-feasibility branch owns executable prices, numerical filters, baseline holdings and trial outcomes. Literature cannot determine overlap or broker execution costs.

## How strong is the citation support, and what prevents overclaiming?

### Takeaway

Scite coverage is useful for locating relevant criticism and methodology, but a supporting classification is not replication, and zero contrasting citations is not proof of a robust edge. The largest risks here are instrument/session transfer, ex-post pattern selection, incomplete fulltext, omitted costs and repeated reuse of local validation history.

### Cited Findings

- The first forward graph has 72 edges, is untruncated, and has direct seed coverage of 34 for fixing, 27 for GLD predictability and 11 for abnormal returns. Only two supporting-classified contexts were returned: the benchmark-reform paper's old-fix comparison and a 2026 preprint's qualitative profit-taking discussion. The latter is not a new causal trading validation. GLD's accessible inbound contexts mostly describe, cite, or broaden its result; no direct net-XAUUSD replication was recovered. [Scite seeds: fixing](https://doi.org/10.1002/fut.21636), [GLD](https://doi.org/10.1016/j.resourpol.2020.101830), [abnormal returns](https://doi.org/10.1007/s11408-021-00380-w).
- In the benchmark-reform Smart Citation, the authors describe old-regime agreement while also distinguishing real-time public disclosure under the new regime. Thus “supporting” does not mean old informed-trader profits survive unchanged for outsiders. [Aspris et al., 2020](https://doi.org/10.1002/fut.22120).
- A second graph includes price discovery, stylized facts, reform, jumps and overnight/day seeds; it hits its 130-edge cap. The overnight/day paper has only one resolved citer and is explicitly flagged low coverage. Do not read missing contrasting contexts as a complete dissent survey. A supporting price-discovery context warns that greater turnover alone does not establish leadership and discusses different conclusions across estimators. [Hauptfleisch et al., 2016](https://doi.org/10.1002/fut.21775).
- EditorialNotices fields were absent in returned selected-paper records. Four additional DOI-filtered searches for retraction/correction/erratum/concern returned zero hits. The tool's generic zero-hit message incorrectly says these already-retrieved DOIs are “not present” in the index. Record only “no notices returned by Scite”; do not claim definitive editorial clearance. Raw responses are preserved.
- White's Reality Check tests the best model encountered against a benchmark while accounting for specification search. Scite served its abstract, not full text. [White, 2000](https://doi.org/10.1111/1468-0262.00152).
- Hansen's SPA uses studentization and a sample-dependent null to reduce sensitivity to poor/irrelevant alternatives; only abstract read. Exact excerpt, 11 words: “more powerful and less sensitive to poor and irrelevant alternatives”. [Hansen, 2005](https://doi.org/10.1198/073500105000000063).
- Sullivan, Timmermann, and White evaluate trading rules relative to the full searched universe rather than just the reported winner. Scite omits Sullivan from metadata/bibliography, corrected using the primary Wiley page. Exact excerpt, 12 words: “the full universe from which the trading rules were drawn”. [Primary paper](https://onlinelibrary.wiley.com/doi/full/10.1111/0022-1082.00163).

### Inferences

Use frozen chronological evaluation and block-level uncertainty that respects serial dependence and same-day clustering. A family-wide Reality Check/SPA or a conservatively adjusted family-level test is more informative than the winning cell's ordinary t statistic. Include earlier attempted variants wherever daily net returns are retained; if not retained, acknowledge that selection correction is incomplete. New validation on already-inspected 2017–2019 data is exploratory and cannot erase the previous 48-rule search.

Daily price-level ML predictions, low RMSE, volatility forecasts, price discovery and descriptive session averages do not establish causal executable M1 return predictability. A failed-cost or insignificant result is useful counterevidence even when the abstract describes a profitable anomaly.

### Gaps

Accessible Smart Citation contexts contain little direct formal contradiction of the two selected hypotheses. This is an evidence gap, not independent replication. Exact benchmark return scaling and closed-paper sample/method details could not be settled without further primary access. No literature claim should be upgraded to “proven C” on that basis.

### References

Aspris, A., Foley, S., & O’Neill, P. (2020). Benchmarks in the spotlight: The impact on exchange traded markets. *Journal of Futures Markets, 40*(11), 1691–1710. https://doi.org/10.1002/fut.22120

Batten, J. A., Lucey, B. M., McGroarty, F., Peat, M., & Urquhart, A. (2017). Stylized facts of intraday precious metals. *PLOS ONE, 12*(4), e0174232. https://doi.org/10.1371/journal.pone.0174232

Blose, L. E., Gondhalekar, V., & Kort, A. (2018). Overnight versus day returns in gold and gold related assets. *Journal of Economics and Finance, 42*(3), 526–549. https://doi.org/10.1007/s12197-017-9403-0

Caminschi, A., & Heaney, R. (2014). Fixing a leaky fixing: Short-term market reactions to the London PM gold price fixing. *Journal of Futures Markets, 34*(11), 1003–1039. https://doi.org/10.1002/fut.21636

Caporale, G. M., & Plastun, A. (2021). Gold and oil prices: Abnormal returns, momentum and contrarian effects. *Financial Markets and Portfolio Management, 35*(3), 353–368. https://doi.org/10.1007/s11408-021-00380-w

Hansen, P. R. (2005). A test for superior predictive ability. *Journal of Business & Economic Statistics, 23*(4), 365–380. https://doi.org/10.1198/073500105000000063

Hauptfleisch, M., Putniņš, T. J., & Lucey, B. M. (2016). Who sets the price of gold? London or New York. *Journal of Futures Markets, 36*(6), 564–586. https://doi.org/10.1002/fut.21775

Ma, G., Bouri, E. I., Xu, Y., & Zhou, Z. I. (2025). The “night effect” of intraday trading: Evidence from Chinese gold and silver futures markets. *Global Finance Journal, 64*, 101084. https://doi.org/10.1016/j.gfj.2025.101084

Sullivan, R., Timmermann, A., & White, H. (1999). Data-snooping, technical trading rule performance, and the bootstrap. *The Journal of Finance, 54*(5), 1647–1691. https://doi.org/10.1111/0022-1082.00163

White, H. (2000). A reality check for data snooping. *Econometrica, 68*(5), 1097–1126. https://doi.org/10.1111/1468-0262.00152

Xiao, Y., Yin, X., & Zhao, J. (2020). Jumps, news, and subsequent return dynamics: An intraday study. *The Journal of Financial Research, 43*(3), 705–731. https://doi.org/10.1111/jfir.12223

Xu, Y., Bouri, E. I., Saeed, T., & Wen, Z. (2020). Intraday return predictability: Evidence from commodity ETFs and their related volatility indices. *Resources Policy, 69*, 101830. https://doi.org/10.1016/j.resourpol.2020.101830

