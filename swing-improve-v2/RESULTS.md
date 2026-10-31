# Swing improvement v2: results (2026-10-31)

Plan `PLAN.md` (before outcomes). Code: `code/load_vol.py`, `build.py`, `factors.py`, `risk.py`.
Outputs: `out/FACTORS.txt/json`, `out/RISK.txt/json`. Data 2010-2019 only; 2020-2022 sealed.
Bases reproduce swing-rule-v1 exactly (rule A 4821 / +0.727 and 2034 / +0.504; rule B 4623 /
+0.439 and 1791 / +0.583). Today's $ per oz; cost $0.168; entry/exit 1 minute late.

## Part 1: volume / spread factors - 0 of 16 pass (shuffle null 0 false passes in 20 draws)
Closest leads (same direction in both periods, below the bar):
- Rule A, volume of the bounce vs the leg: bounces with heavier volume than the leg (high tercile)
  are the weakest (O1 +0.282 / +0.221 vs mid +1.166 / +0.661; t +2.2 / +1.1) and hit the stop
  more (6.7% / 6.9% vs 3.7% / 2.6% for the low tercile): a heavy bounce looks more like a real turn.
- Rule A, volume climax at the extreme (high tercile) also weaker (+0.568 / +0.157).
- Spread at the bounce: no consistent effect.

## Part 2: drawdown controls (per oz-equivalent; Calmar = annual net / max drawdown)
| Rule / control | 2010-16 net/day, max DD, Calmar | 2017-19 net/day, max DD, Calmar | Accepted |
|---|---|---|---|
| A R0 base | +1.93, 378.5, 1.32 | +1.32, 224.0, 1.53 | base |
| A R1 vol sizing | +1.55, 409.2, 0.98 | +1.74, 299.8, 1.50 | no |
| A R2 daily 2-loss brake | +1.57, 319.5, 1.27 | +1.21, 179.9, 1.74 | no (Calmar 2010-16) |
| A R3 equity filter | +1.42, 306.4, 1.20 | +1.08, 148.4, 1.87 | no (Calmar 2010-16) |
| B R0 base | +1.12, 369.4, 0.79 | +1.35, 171.2, 2.03 | base |
| B R1 vol sizing | +1.07, 211.4, 1.32 | +1.54, 178.7, 2.22 | no (DD 2017-19 +4%) |
| B R2 daily brake | +1.04, 333.4, 0.81 | +1.26, 165.6, 1.97 | no |
| B R3 equity filter | +0.35, 516.0, 0.18 | +1.11, 156.8, 1.83 | no |
| A+B R4 (0.5 oz each) | +1.52, 262.6, 1.51 | +1.34, 130.5, 2.64 | YES |

Full 2010-2019 path (1 oz-equivalent exposure): A max DD 378.5, longest under water 707 days,
worst month -116; B 369.4 / 365 days / -160; A+B half each 262.6 / 330 days / -78, net/day +1.47,
72% of months positive, Calmar 1.45 (A 1.20, B 0.83).

## Reading
- New information (volume, spread) did not pass the bar; one consistent lead: heavy-volume bounces
  fail less often (worse for the fade) in rule A.
- The only accepted drawdown control is running both rules together: about 30% lower max
  drawdown than either rule alone at the same total exposure, shorter time under water, half the
  worst month. The daily 2-loss brake (rule A) and volatility sizing (rule B) are near misses.
- Drawdowns are on closed trades; open-trade swings inside a position are not included.
- 100,000 THB view (USD/THB 33.77): A and B at 0.01 lot each (2 oz total) -> historical max
  drawdown about 17,700 THB (~18%), about +25,700 THB per year on average 2010-2019 (in-sample).
