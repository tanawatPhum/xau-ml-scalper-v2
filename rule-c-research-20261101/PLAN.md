# Rule C research spike — 2026-11-01

User authorizes local experimental research only; no new v1 revision or registry update.
Base is frozen v1-r2 D058-S1. User confirms overlap means C enters while A or B
holds, <=30% of C trades. Count the union, including simultaneous entries, ignoring direction.
No AB entry veto: measure C's naturally occurring trades, not force overlap to zero.

Scope: design 2010–2016; freeze code/candidate selection before reused exploratory
2017–2019 evaluation. 2020+ not read in this study. Prior research has already seen
these years; no claim of virgin holdout. This is an authorized throwaway research spike.

24 predeclared cells: 8 failed-breakout reclaims (window60/240, buffer0/.25 volatility,
hold30/90); 8 mean-deviation reversals (window60/240, threshold1.5/2.5, hold30/90);
8 compression breakouts (window30/60, range1/1.5 volatility, hold30/90).
Each uses strictly prior contiguous close windows, excludes future quotes, resets at
missing minutes/session change. Scale=max(eff volatility in dollars at signal, $0.5).
Stop and target both1.5scale; timed exit at entry+hold minutes; no optimized exit grid.
Signals at minute close, entry exact next minute or cancel; stop/target observed at
close exit at next actual quote, never assumed intrabar fill. No terminal forced exit.
Existing daily calendar, fixed NY16:55 liquidation and conservative holiday policy.

0.1lot=10oz per rule, FX33.77, start100kTHB. Fixed spread .168USD/oz.
Separate sensitivity adds commission .01 and slippage .02USD/oz per side.
Historical bid/ask also evaluated for frozen candidates, never used to select.
Equity includes liquidation costs and open-position P/L each available minute.

Training eligibility: net>0, profit factor>1, overlap<=30%, >=100closed trades,
2014–2016 equity gain>0, positive net with the additional example costs, and zero
market-close/session crossings or terminal position. Select at most one per family,
rank by daily-return t then net/DD then stable ID. Freeze even if no candidate passes.
Validation on fresh2017–2019: same net/PF/overlap/close requirements, >=20trades and
positive example-cost net. Report failures, all training cells and annual detail.
Daily t and common-day sign-flip max-t null across24 cells are descriptive diagnostics;
large search and reused years preclude claiming proof of a durable edge.
Report combined AB+C net/DD and overlap time, in addition to C-only profitability.

Implementer choices: v1-r2 baseline; periods and minimum counts as above. No changes
to source versions, no live orders. Alternative C approaches tried earlier are documented
in swing-v2-ruleC and swing-v2-ruleC-r2; no claim that failed searches exhaust possibilities.
