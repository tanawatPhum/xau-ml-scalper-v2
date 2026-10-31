# FOMC declared-release-time diagnostic — 1 November 2026

The fixed diagnostic is positive on five trades but does not qualify: 5 trades are below the prespecified 20-trade design minimum. There were only 8 eligible events before prices were read. No candidate was selected and no 2017–2019 validation prices were read. Actual news delivery latency is unverified; this is a declared-release-time proxy, not validated real-time news-conditioned execution.

Design prices: 2010–2016. Every eligible event is in 2016; earlier regular statements lack verified release minutes and were excluded. Five of eight events reached the fixed 2-sigma threshold; three did not. No missing-window event was silently treated as no-news.

| Design result | Primary timed exit | Fixed 3-vol stop sensitivity |
|---|---:|---:|
| Closed trades |5|5|
| Fixed-spread net, 0.1 lot (THB) |2,389.06|2,389.06|
| Example-cost net (THB) |2,287.75|2,287.75|
| Historical-spread net (THB) |2,117.38|2,117.38|
| Gross midpoint net (THB) |2,672.73|2,672.73|
| Profit factor on fixed-cost trades |2.413|2.413|
| C liquidation-equity DD (THB / %) |2,063.85 / 2.008%|2,063.85 / 2.008%|
| Natural A/B union overlap |0/5 (0%)|0%|

The stop sensitivity is identical because no 3-scale stop fired. It cannot replace primary selection. All five primary trades entered exactly E+5 and exited E+20. Market-close/session crossings, late-cutoff exits, data-gap spans and terminal positions are all zero. The only failed qualification check is minimum_trades; the extra conservative 0.5 lot solvency check also passes and does not affect rejection.

Locked A/B baseline design net is 353,805.25 THB. Adding C gives 356,194.31 THB with combined DD 29,755.25 THB (12.475%). This is a historical sum of separately sized rules, not evidence that the new rule is deployable.

At fixed 0.5 lot scaling, C net is 11,945.29 THB, C DD 10,319.27 THB (9.053%), and minimum equity 99,066.26 THB. Scaled combined net is 1,780,971.55 THB with DD 148,776.27 THB (30.445%). Start equity is 100,000 THB; no compounding, margin, financing or stop-out model.

| Event date | Jump ratio J | Outcome |
|---|---:|---|
|2016-01-27|1.967|below_fixed_jump_threshold|
|2016-03-16|19.935|signal|
|2016-04-27|2.673|signal|
|2016-06-15|8.490|signal|
|2016-07-27|6.635|signal|
|2016-09-21|1.334|below_fixed_jump_threshold|
|2016-11-02|0.427|below_fixed_jump_threshold|
|2016-12-14|6.211|signal|

| Entry UTC | Exit UTC | Side | Fixed net THB |
|---|---|---|---:|
|2016-03-16 18:05|2016-03-16 18:20|Buy|645.51|
|2016-04-27 18:05|2016-04-27 18:20|Sell|1,235.31|
|2016-06-15 18:05|2016-06-15 18:20|Buy|915.50|
|2016-07-27 18:05|2016-07-27 18:20|Sell|-1,690.53|
|2016-12-14 19:05|2016-12-14 19:20|Sell|1,283.26|

Source evidence and exclusions are in DATA_AUDIT.md and event_manifest.json. PRE_RUN_LOCK freezes protocol, code, event inputs and allowed design-cache hashes before price loading. Synthetic checks cover direction, exact five-minute response, missing quote/entry cancellation, pre-event scale, DST, costs, next-minute fills, stop delay, overlap union and forbidden years. Real-data prefix invariance passed with an open trade at cutoff; locked baseline training metrics reproduced. Original metadata, source and allowed design-cache hashes remained unchanged. No GVZ, US500 or 2020+ prices were read.

No trading specification or execution code was changed after market outcomes.

Decision: retain as a data-limited research observation only. More trustworthy contemporaneous release timing and substantially more eligible design events would be needed before a fresh, separately prespecified test; do not backfill this frozen trial in response to its positive P/L.
