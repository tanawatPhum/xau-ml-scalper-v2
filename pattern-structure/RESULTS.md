# Pattern structure: results (2026-10-31)

Plan `PLAN.md` (written before outcomes). Code `code/`: patterns, build, analysis (pre-registered),
diag / diag2 / diag3 (post-hoc diagnostics, labelled), summary. Outputs `out/REPORT.json`,
`SYNTH_REPORT.json`, `DIAG.json`, `DIAG2.json`.

## Self-test
Synthetic Gaussian random walk on the 2017 calendar: real = random-order shares within noise
(families within 0.0-0.5 pp), next-state shares = base, pooled prefix |t| <= 2.0. Pipeline clean.

## Part A - pattern structure (30-minute windows = 3 x 10 min; median 0.5 sigma = $0.41)
Base state shares D / F / U = 27.7 / 44.5 / 27.8% (Gaussian 31 / 38 / 31).

| Family | Patterns | Real % [95% CI] | Random order % | Direction-random % (post-hoc) |
|---|---|---|---|---|
| QUIET | FFF | 9.96 [9.81-10.10] | 8.55 | 7.89 |
| IMPULSE | one move, rest flat (6) | 31.86 [31.69-32.06] | 29.20 | 29.84 |
| TREND | >= 2 moves same direction (8) | 22.42 [22.25-22.59] | 22.32 | 25.96 |
| REVERSAL | one direction change (10) | 30.84 [30.66-31.01] | 34.14 | 31.11 |
| WHIPSAW | UDU, DUD | 4.92 [4.83-5.00] | 5.80 | 5.19 |

- Same ordering at 15-minute (3 x 5) and 60-minute (3 x 20) windows; deviations grow with the
  window (QUIET ratio 1.09 / 1.16 / 1.25; REVERSAL 0.94 / 0.90 / 0.87).
- Most frequent patterns: FFF 10.0, UFF 5.5, FFD 5.4, FFU 5.4, DFF 5.3, FUF 5.2, FDF 5.1%;
  least: UUU 2.0, DDD 2.0, UDD 2.3%.
- Reading: (1) moves arrive in bursts (one active segment, the rest quiet) - volatility timing;
  (2) against a process with the same timing but random direction, TREND is 3.5 pp rarer and
  QUIET/IMPULSE more common: prices partly undo themselves (mild mean reversion).
- Transitions (10-min): after UU the next segment is D 32.3% (base 27.7), after DD it is
  U 33.6% (base 27.8); after FF it stays F 48.0% (base 44.5).

## Part B - playability (pre-registered rules; costs: owner median $0.055, Dukascopy $0.327)
- Pooled prefixes passing (non-random): L5 UU (fade +$0.025), L10 DD (+$0.045) and UU (+$0.030):
  all below the owner cost. Not playable.
- Prefix x NY hour (198 cells per L, 20 sign-flip nulls: mean 0-0.05 passing cells):
  only NY hour 16 cells pass; UU and DD at NY16 are playable vs the owner cost at every L
  (gross $0.08-0.36, positive in 4-6 of 6 confirmation years). None vs Dukascopy spread.
- Positive control (decision exactly 16:00 NY): last segment U -> next -$0.17 to -0.29,
  last D -> +$0.22 to +0.38 (t 4.5-8.7) in both periods.
- Post-hoc (diag): the NY16 edge sits at the 16:00 decision. 2017-2022 net after owner cost,
  decision at 16:00: UU sell +$0.20 / +0.25 / +0.36 and DD buy +$0.42 / +0.41 / +0.47 at
  L = 5 / 10 / 20, win 62-71%, about 20-27 trades per year per side. Other NY16 minutes ~ 0.
- Post-hoc (diag2, NY16 excluded, by volatility tercile): only DD at L10 in high volatility
  passes the rules (gross $0.081 vs cost $0.073): breakeven, one length, buy side only.
- Post-hoc (diag3, strong runs >= 1 sigma, NY16 excluded): net positive in 2-7 of 13 years.
  Not playable.

## Verdict
- Structure exists (bursty activity, mild self-cancelling, trend exhaustion after two segments),
  but its dollar size is below the owner's cost everywhere except the 16:00 NY close.
- Playable after spread: two same-direction segments into 16:00 NY, faded (the edge-map effect).
- Next: pre-registered 16:00 NY execution test with BID/ASK sides and a second data source.
