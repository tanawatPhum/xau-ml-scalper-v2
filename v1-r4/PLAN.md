# v1-r4 plan (written 2026-11-01 ~02:20 ICT, before any v1-r4 outcome)

Owner (02:09 ICT): go ahead with lot sizing plus risk analysis. Use real-trading lots: 0.1-0.5 lot per trade, at a risk that is acceptable.

## Base
- **Entries and exits are exactly v1-r2:**
  - v1-r1 D058 rules plus the v1-r2 per-session overrides;
  - stop 2.5 theta;
  - flat at 16:55 NY;
  - fixed $0.168 spread; USD/THB 33.77; money at the time's price.
- **Only position size changes.** The set and timing of trades is identical to v1-r2, which the code asserts.
- **Capital:** start at 100,000 THB, as in all earlier reports.
- **Years:**
  - 2010-16: selection;
  - 2017-19: check (reused, so exploratory);
  - 2020-22: descriptive;
  - 2023+: closed.

## Sizing candidates
Every lot is in [0.1, 0.5], rounded down to 0.01. The rule is the same for A and B, but each trade is sized by its own leg and theta$.

| Code | Rule |
|---|---|
| Z0-L | Fixed lot L ∈ {0.1, 0.2, 0.3, 0.4, 0.5}. The risk table. |
| Z1 | Lot by prior-leg tier: leg/theta in [rule minimum, 3.5), [3.5, 5), [5, ∞). Tiers (0.1,0.2,0.3), (0.1,0.2,0.5), (0.1,0.3,0.5), (0.2,0.3,0.5). Motivation: the v1-r3 audit showed the next pullback is shorter after longer legs. |
| Z2 | Lot by theta$ tier: trailing-365-day terciles of that rule's eligible theta$, at least 60 events, else the low tier. Tiers (0.1,0.2,0.3), (0.1,0.3,0.5). Motivation: profit per unit of risk rises with theta$. |
| Z3-r | Equity risk. Lot = r × equity ÷ (loss at the stop per 1.0 lot), with that loss = 2.5 · theta$ · 100 oz · 33.77, clamped to [0.1, 0.5]. Equity is measured at the signal close. r ∈ {2%, 3%, 4%, 5%}. |
| Z4-r | As Z3, but r is multiplied by (1, 1.5, 2) by Z1's leg tier. r ∈ {2%, 3%, 4%}. |

That gives **18 candidates**. Note that 0.1 lot already risks about 2-6% of 100,000 THB at the stop, so Z3 / Z4 sit at the 0.1 floor until equity grows.

## "Acceptable" risk (proposed by Claude; the owner can choose other limits)
1. Max equity drawdown ≤ 20%. Equity is minute-level liquidation equity, measured from its running peak.
2. Block-bootstrap 95th-percentile max DD ≤ 30%.
   - Method: stationary bootstrap of daily % equity returns; mean block 5 days; 2,000 paths; seed 20261101.
   - It uses daily closes only, so it misses intraday dips. This is an approximation.
3. Worst single trade ≤ 6% of equity at entry.
4. Lowest equity ≥ 80,000 THB (80% of start).

## Selection (2010-16)
- **Check:** with fixed 0.1 lot the sized replay must reproduce v1-r2 2010-16 exactly: every trade, and net 353,805.25 / DD 29,686.87.
- **Pick:** among candidates meeting all four limits, the highest net. A tie goes to the simpler code order (Z0 < Z1 < Z2 < Z3 < Z4).
- **Lock:** `out/LOCK.json` + sha256 before any 2017+ run.

## Evaluation
- **Runs:** 2017-19 standalone from 100,000 THB, and 2010-19 continuous, both at the fixed spread. The other cost cases are reported for the pick.
- **PASS** on 2017-19, all of:
  - limits 1-4 hold;
  - net > v1-r2 at 0.1 lot;
  - net / max DD (THB) ≥ v1-r2 at 0.1 lot. More money, no worse efficiency, acceptable risk.
- **2020-22:** descriptive, continuous 2010-22.
- **Also reported (descriptive):**
  - **Fixed-lot capital table:** for each fixed lot 0.1-0.5, the smallest starting capital that keeps the max DD within 20% and the bootstrap 95th percentile within 30%, over 2010-19 and 2010-22.
  - **Lot mix:** the distribution of lots used.
  - **Parameter sensitivity on 2010-16 at 0.1 lot:** v1-r2 with one parameter moved one step at a time (A k ±0.1, B k ±0.25, A/B leg ±0.5, stop ±0.25). This checks the current version's stability; it is not used to select anything.
- **Not modelled:** margin, swap, broker lot limits. Exness margin for 0.5 lot is small next to these equities, but it is not checked here.

## Amendment A (implementation notes; written after the 0.1-lot check passed and before any candidate was run)
- **Float ties.** Fixed lots scale net and DD exactly, so net/DD at 0.2-0.5 equals 0.1 up to float noise. The PASS test "net/DD ≥ v1-r2 at 0.1" therefore uses a relative tolerance of 1e-9. This avoids a repeat of the v1-r3 DD-tie caveat.
- **Capital table.** It is computed exactly, not on a grid. For a fixed-lot P&L path p (with p0 = 0) and running max M, max DD% ≤ x holds exactly when capital ≥ max_t[(M_t − p_t)/x − M_t].
  - Historical: the minute-equity path, x = 20%.
  - Bootstrap: the same stationary bootstrap (2,000 paths, mean block 5, seed 20261101) of daily THB P&L, x = 30%. The required capital is the 95th percentile of the per-path values.
  - Values are rounded up to 1,000 THB.
  - It is also reported for 2010-16, for information only.
