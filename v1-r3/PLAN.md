# v1-r3 plan (written 2026-11-01 ICT, before any v1-r3 outcome is computed)

Owner (00:35 ICT): open v1-r3 and allow downloading all new data needed for the experiments.
Motivation: `lit-review-v1r2/REVIEW.md`, ideas 1-3 plus the three extra-data ideas.

## Base, data, years
- **Base = v1-r2**, locked and unchanged:
  - v1-r1 rules (D058) plus the v1-r2 per-session overrides (`v1-r2/out/LOCK.json`, sha 9523319b...);
  - stop 2.5 theta;
  - v1-r1 daily-close engine and calendar (flat at 16:55 NY);
  - fixed spread $0.168; 0.1 lot per rule; money at the time's price.
- **Code:** v1-r1, v1-r2 and their files are imported read-only.
- **Years:**
  - 2010-16: design / selection;
  - 2017-19: check (reused, so exploratory);
  - 2020-22: descriptive only;
  - 2023+: never read.
- **External data** (owner-approved downloads, all truncated at 2022-12-31; `data-ext/`):
  - GVZ daily close (CBOE);
  - release dates of NFP and CPI (BLS archive pages), GDP (BEA listing), all at 08:30 ET;
  - FOMC statement dates and times (federalreserve.gov). For 2010-15 statements whose pages show no time:
    - *Amended 01:30 ICT, before any outcome:* times follow the Fed's schedule practice: 12:30 ET on the 2011-12 press-conference days, 14:15 ET through Jan 2013, and 14:00 ET from Mar 2013.
    - The originally planned gold-spike rule (largest |1-min return| among {12:30, 14:00, 14:15}) is kept only as a corroborating check. It agreed on most dates but misassigned days with weak reactions.
    - Neither rule uses trade outcomes.
  - NFP / CPI dates come from the BLS archive pages and GDP dates from ALFRED GDP vintage dates; all were captured via WebFetch because bls.gov and FRED block this device.
  - S&P 500 CFD 1-minute bid (Dukascopy USA500IDXUSD). It has real ticks only from early 2012, so F8 cannot fire before that.
- **During design,** gold and all external series are read only up to 2016-12-31.

## Trade direction (correction to the literature brief)
- The engine trades side = -(event direction).
- After a leg of at least L·theta and a theta counter-move, the trade is in the direction of the prior leg: it fades the counter-move. For example, after an up-leg and a theta dip, it buys.
- The take-profit is the next swing event (about +theta at best). The loss runs up to the 2.5-theta stop when the counter-move grows into a reversal.
- Hypotheses below are stated in terms of this side `s`. `dir` is the event direction, so `s = -dir`.

## Candidate families (each is an entry filter on top of v1-r2, except F4)
All features are causal: known at the signal close, or earlier.
- **F1 Deadline admission.** Block if (session deadline - signal minute) < N, N ∈ {15, 30, 60} min.
- **F2 Settlement veto.** Block if the signal is in 13:00-13:30 NY and s · (y_signal - y_session_open) < 0, meaning the trade is against the day's move. Market intraday momentum into the futures close is the reason.
- **F3 Leg jump concentration.** J = max r² / Σ r² over the leg's adjacent-minute returns (previous pivot to extreme). The cutoff is a trailing 180-day quantile over that rule's eligible events, needing at least 60 events; otherwise the filter is inactive.
  - Variants: block J above the 0.8 quantile (jumpy legs); block J below the 0.2 quantile (smooth legs).
  - The direction is not known in advance: news legs continue (good for s), no-news jumps reverse (bad).
- **F3n No-news jump.** Block if J is above the 0.8 quantile and no scheduled release (NFP / CPI / GDP / FOMC) falls in [leg start - 5 min, signal].
- **F4 Seasonal theta.**
  - s(b)² = mean r² in 15-min NY time-of-day bin b over the prior 60 session days, divided by the all-bin mean (s = 1 until 60 days exist).
  - σ60_seas = σ̃60 · s(b_t), where σ̃60 is the v1-r1 60-minute estimator applied to r / s(b).
  - Rule A uses max(σ60_seas, σ1440); rule B uses σ60_seas. Overrides, floors, legs and policies are unchanged.
  - Variants: `seas` (sum of squares); `seas_bp` (bipower, π/2 · mean |r̃_j||r̃_j-1|).
- **F5 Volatility surprise.**
  - u = σ60 / E60, with E60 = σ̄ · sqrt(mean s(b)² over the same 60-minute window) and σ̄ = the deseasonalised level over the prior 60 days.
  - Block if u > q, q ∈ {1.5, 2, 3}.
- **F6 Calendar.**
  - (a) Block if a release time τ falls in [leg start - 5 min, signal].
  - (b) Block if 0 ≤ signal - τ ≤ 60 min.
- **F7 GVZ regime.** Use the percentile of the previous US trading day's GVZ close within the trailing 252 observations.
  - Variants: block below 1/3; block above 2/3.
- **F8 Flight to gold.** Block short-gold trades (s = -1) if an S&P 5-minute log return at or below the 1st percentile of the prior 60 calendar days occurred in (signal - 60 min, signal].

Each variant can apply to rule A or rule B: 17 variants × 2 rules = **34 cells**. This is the multiple-testing ledger.

## Amendment A (01:30 ICT, before any outcome; after the corrected Consensus follow-up)
The corrected brief (trade = fade of the first pullback, with the prior leg) changed several hypotheses. This amendment replaces the family list above.

- **F1 Deadline admission:** unchanged, N ∈ {15, 30, 60}.
- **F2:**
  - `settle`: the 13:00-13:30 NY rule as above.
  - `glds`: in 15:30-16:00 NY, block if side · (y 12:00 NY - y 11:30 NY of that NY date) ≤ 0. This follows Xu, Bouri & Saeed 2020: in GLD, the 11:30-12:00 half-hour predicts the last half-hour. If either price is missing, the trade is kept.
- **F3 Jump concentration,** measured separately for the prior leg (previous pivot → extreme) and the pullback (extreme → signal). Cut-offs are duration-matched: the trailing 180 days of that rule's eligible events with n_j in [n/1.5, 1.5n], at least 30 events.
  - Variants: `leg_high`, `leg_low`, `pb_high`, `pb_low`. Each blocks values above the 0.8 quantile or below the 0.2 quantile.
- **F3n:**
  - `jump_norel`: block a prior leg with high J and no release in [leg start - 5, extreme].
  - `jump_rel`: block a prior leg with high J and a release in that window.
  - This makes the family two-sided.
- **F4 Seasonal theta:** unchanged (`seas`, `seas_bp`).
- **F5 Volatility surprise:** q ∈ {2, 3}; the sign is ambiguous. A descriptive GVZ × surprise table is added (no selection).
- **F6:**
  - `leg_release`: a release in [leg start - 5, extreme];
  - `pb_release`: a release in [extreme - 5, signal];
  - `window`: the signal falls within [τ - 5, τ + 15] of a release.
- **F7 GVZ:** unchanged (`low`, `high`).
- **F8:** block short-gold trades if an S&P 5-minute return at or below the clock-matched 1st percentile occurred in the last E minutes.
  - The percentile is computed within the same 30-minute NY bin over the prior 60 days, with at least 300 values.
  - E ∈ {15, 60}.
- **F9 Round-number rejection** (new; `reject`):
  - Up-legs are blocked if the leg high is in [K - 0.1θ$, K + 0.5θ$] for some $10 multiple K and the signal price is below K.
  - Down-legs are the mirror case.
  - Osler: take-profit orders clustered at round numbers turn the prior leg back.
- **Ledger:** 23 variants × 2 rules = **46 cells**.
- **Descriptive diagnostics** (no selection):
  - Overshoot audit on v1-r2 trades over 2010-16. O/θ is the adverse pullback extension after entry. Report P(O < θ), mean O/θ, and the share of trades reaching the stop, by prior-leg bins 2.5-3.5, 3.5-5 and > 5 θ.
  - The GVZ (vs. its trailing median) × surprise (u above/below 2) table.

## Selection (2010-16 only)
- **Check.** With no filter and raw volatility, signals equal v1-r2's exactly and 2010-16 metrics reproduce v1-r2's lock (net 353,805.25 / DD 29,686.87 / 2,737 trades).
- **Stage 1.** Each cell is run alone. It is eligible if, against v1-r2 over 2010-16:
  - net ≥ base;
  - DD ≤ base;
  - net/DD > base;
  - 0 market-close and session crossings;
  - day-clustered t of the daily P&L difference ≥ 1.0.
- **Pick.** Per (rule, family) keep the eligible variant with the best net/DD.
- **Random-block null** for each pick: 20 draws, each blocking the same number of that rule's eligible signals uniformly at random. A pick is kept only if its net/DD beats at least 19 of the 20 draws.
  - F4 changes theta rather than blocking signals, so it has no block null. An F4 pick needs a stage-1 t ≥ 1.5 instead.
- **Stage 2 (same procedure as v1-r2).**
  - Combine all kept picks.
  - Accept the combination if net > base, DD < base, recent (2014-16) ≥ base, lowest equity > 0, trades ≥ 500 and 0 crossings.
  - Otherwise add picks greedily in order of stage-1 net/DD. A pick stays only if the running set has net ≥ base, DD ≤ base and an improved net/DD. The final set must pass the same acceptance rule.
  - If nothing passes, v1-r3 = NOT_CONFIRMED and v1-r2 stays current.
- **Lock.** Write `out/LOCK.json` and its sha256 before any 2017+ data is read.

## Evaluation
- **Runs:** 2017-19 standalone from 100,000 THB, and 2010-19 continuous, each under three cost cases (fixed, cost example, historical bid/ask). External features in the standalone run use their own warm-up, exactly like θ.
- **PASS** = on 2017-19 at the fixed spread, v1-r3 net > v1-r2 net, DD ≤ v1-r2 DD, and 0 crossings. This is the owner's bar: better than the current version on both profit and DD.
- **Also reported:**
  - day-clustered t of the daily difference;
  - leave-one-out attribution per selected filter;
  - results by session and by year at 0.1 lot;
  - a diagnostic: theta at exit ÷ theta at entry for stop-outs.
- **2020-22:** descriptive, continuous 2010-22.
- **If PASS:** v1-r3 becomes current (VERSIONS.json and README); next is v1-r4.
