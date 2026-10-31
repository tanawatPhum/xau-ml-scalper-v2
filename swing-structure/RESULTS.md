# Swing patterns at the $1-10 scale: results (2026-10-31)

Plan `PLAN.md` (written before outcomes). Code: `swing.py`, `build.py`, `analysis.py`
(pre-registered), `verify.py` (post-hoc robustness). Outputs: `out/REPORT.json`, `SYNTH.json`,
`NULL_SIGNFLIP.json`, `VERIFY.txt`. Dukascopy M1 mid 2010-2022 (2023+ never read).
Money in today's dollars (bps x 4083.276/1e4); cost $0.168 per round trip (owner's broker).

## Scale
| Swing size | Swings per day | Median leg | Median swing time |
|---|---:|---:|---:|
| $1 | 176 | $2.53 | 4 min |
| $2 | 88 | $4.29 | 8 min |
| $3 | 54 | $6.06 | 12 min |
| $5 | 26 | $9.48 | 23 min |
| $10 | 8 | $17.96 | 56 min |

## Part A - market-structure pattern shares (real %, sign-flip null % in brackets)
| Size | TREND (HH+HL) | CONTRACT (LH+HL) | COUNTER (LH+LL) | EXPAND (HH+LL) |
|---|---:|---:|---:|---:|
| $1 | 32.8 (33.2) | 18.1 (16.8) | 33.0 (33.3) | 16.1 (16.7) |
| $2 | 33.0 (33.3) | 18.1 (16.8) | 33.1 (33.3) | 15.8 (16.7) |
| $3 | 33.1 (33.3) | 18.1 (16.8) | 33.2 (33.3) | 15.6 (16.6) |
| $5 | 33.3 (33.3) | 18.0 (16.8) | 33.3 (33.2) | 15.4 (16.8) |
| $10 | 33.3 (33.4) | 18.2 (16.7) | 33.2 (33.2) | 15.3 (16.8) |
Random-walk theory: 33.3 / 16.7 / 33.3 / 16.7.

8 patterns at $5 (real / null): TREND shallow 13.4/13.7, TREND deep 19.9/19.5, CONTRACT shallow
2.4/2.4, CONTRACT deep 15.6/14.4, COUNTER mild 13.3/13.6, COUNTER deep 20.0/19.6, EXPAND mild
8.0/8.7, EXPAND deep 7.4/8.0.
- TREND and COUNTER occur at chance. Shrinking leg sequences (CONTRACT) +1.2 to +1.5 pp and
  growing ones (EXPAND) -0.6 to -1.5 pp versus the null.
- Checks: sign-flip null trade P&L ~ $0 at every size (|mean| <= $0.02). One-year synthetic random
  walk: shares ~ theory; R1 -$0.17 (t -2.2) at $5 and -$0.52 (t -1.6) at $10, within chance for a
  one-year sample (the 13-year null is ~ 0).

## Part B - playability (pre-registered)
- R1 follow, all years, gross: negative in 36 of 40 pattern x size cells; the 4 positive cells have
  |t| <= 0.9. No follow cell is positive after cost in confirmation. R3 bracket: gross ~ 0.
- Follow losses (= fade edge) are largest when the leg before the new swing was large: $5 TREND
  deep -$0.23, COUNTER deep -$0.24, EXPAND mild -$0.37, EXPAND deep -$0.31 (t -3.7 to -4.7) vs
  TREND shallow -$0.08, CONTRACT -$0.03 / +$0.01.
- Cells passing all rules (null false passes 0/20 at every size):

| Size | Fade after | 2017-22 net per trade | Trades/yr | Years net > 0 | Win |
|---|---|---:|---:|---:|---:|
| $3 | EXPAND deep | +$0.074 | 1,071 | 5/6 | 63% |
| $5 | COUNTER deep | +$0.114 | 1,172 | 5/6 | 63% |
| $5 | EXPAND mild | +$0.204 | 488 | 5/6 | 64% |

  All three stay playable without 15:45-16:30 NY.
- Near misses (fail discovery |t| >= 3): $5 TREND deep fade +$0.122 (5/6, t_disc -2.8);
  $10 COUNTER deep fade +$0.796 (5/6, t_disc -2.8); $10 EXPAND mild fade +$0.969 (4/6, t_disc
  -2.5); $10 fade every swing +$0.478 (6/6, t_disc -1.8; 2010-16 net +$0.015).
- Fade win rates 63-66% equal the random-walk baseline 1 - e^-1 = 63.2%: the edge is in the
  average size of wins and losses, not in the hit rate.

## Post-hoc robustness (verify.py, out/VERIFY.txt): 2017-22 net per trade (simple t)
| Cell | Delay 0 | 1 min late | 2 min late | BID only | ASK only |
|---|---:|---:|---:|---:|---:|
| $3 EXPAND deep | +0.074 (1.3) | -0.031 (-0.5) | -0.061 (-1.0) | +0.086 (1.5) | +0.072 (1.2) |
| $5 COUNTER deep | +0.114 (1.5) | +0.088 (1.1) | +0.016 (0.2) | +0.175 (2.2) | +0.150 (1.9) |
| $5 EXPAND mild | +0.204 (1.7) | +0.138 (1.1) | +0.076 (0.6) | +0.247 (2.0) | +0.212 (1.8) |
| $10 COUNTER deep | +0.796 (3.0) | +0.566 (2.1) | +0.455 (1.7) | +0.696 (2.6) | +0.742 (2.8) |
| $10 every swing | +0.478 (4.0) | +0.271 (2.3) | +0.094 (0.8) | +0.488 (4.1) | +0.544 (4.6) |
- 2010-16 at delay 0: $10 COUNTER deep +$0.443 (t 2.1); $10 every swing +$0.015 (t 0.2).
- Removing NY 16:30-19:30 (rollover, wide spread) changes nothing.
- Payoff with no stop, 2017-22: $5 COUNTER deep median +$1.91, p5 -$12.70, p1 -$22.97, worst
  -$51.35; $5 EXPAND mild median +$2.01, p1 -$23.05, worst -$66.74; $3 EXPAND deep median
  +$1.28, p1 -$17.09, worst -$46.19.

## Verdict
- At $1-10 the market-structure patterns occur at random-walk rates (within 1.5 pp).
- The one directional finding: a newly confirmed swing extends less than a random walk, most of
  all after a large leg. Following new swings never pays; fading them has a small edge on paper.
- Not robustly playable: at $3 the edge is gone with a 1-minute delay, at $5 it falls to t ~ 1, the
  $10 edge is mainly 2017-2022, and the payoff has fat left tails.
- Candidates for a pre-registered next test (2023+ needs owner authorisation): $10 swing fade
  (COUNTER deep, or every swing) with 1-minute-late fills and a stop-loss rule.
- The strongest edge found so far remains the 16:00 NY close reversal (edge map).
