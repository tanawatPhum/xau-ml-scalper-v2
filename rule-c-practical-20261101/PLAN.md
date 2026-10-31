# Practical Rule C research implementation plan

User correction: no fixed daily trade quota. Seek a useful after-cost edge with
naturally recurring opportunities; report actual frequency and idle days. Keep
C entry overlap with frozen r2 A/B holding union <=30%. No new strategy version.

1. Implement24 predeclared price-path candidates in study.py; synthetic prefix and
   known-direction checks before prices. No news labels or A/B entry veto.
2. Reuse immutable causal replay and study library from rule-c-research-20261101.
   Source/data hashes and candidates recorded before outcomes. Design2010–2016,
   select at most one candidate, freeze before reused2017–2019 evaluation;2020+
   prices remain closed. No amendments after seeing outcomes.
3. Evaluate selected formula only, reconcile annual/minute equity and trade counts,
   and write RESULTS.md with all searched cells retained even if none qualifies.

Formula: two contiguous blocks of w={15,30,60} minutes within one NY trading session.
First block log-price impulse >=k={1,2} times strictly prior volatility scaled to w.
Second block is an opposite retracement of20–50% of impulse. Trade either the original
direction or its opposite (both hypotheses declared now). Emit on the first qualifying
transition, with30minute signal cooldown. Hold limit={30,90}minutes; stop1scale,target2scale,
scale=max(half the impulse converted to USD at signal,$0.50). These are24 cells.
Signals use current/past observed closes only; next-minute entry or cancel; stop/target
detected at close filled at next actual quote; existing NY16:55 calendar remains.

One hypothesis family selection, highest training net/DD then stable ID among qualifiers.
Eligibility: positive fixed and example-cost net, PF>1, overlap<=30%, no market-close/session
crossing or terminal position, positive lowest equity. At least500 training/150 validation
closed trades are sample-sufficiency guards, NOT promised business frequency. Training
2014–2016 net positive under fixed AND example costs. Report trades/session, fraction of
all observed broker sessions with entries, zero-trade sessions, annual counts and net/entry.
Denominator includes sessions on strategy holiday blackouts; not only sessions with trades.
No trades-per-day quota or entry requirement. A candidate with low frequency is explicitly
described at that frequency, never called daily-tradable merely because it passes this gate.

0.1lot per rule,100kTHB start,FX33.77,spread.168USD/oz; examplecommission.01 andslip.02peroz/side.
Historicalbidask for locked validation sensitivity. No margin or financing. Reused years and
many earlier searches mean any pass is exploratory; daily t/null statistics are diagnostic,
not proof of a deployable edge. New entries/rolling features and future-prefix equality tested.
