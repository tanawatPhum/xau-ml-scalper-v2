# xau-ml-scalper-claude

Owner rule (2026-10-31 10:18 ICT): any experiment code that has not been opened as an experiment
in the main project lives under this folder.

- Research workspace, published to `https://github.com/tanawatPhum/xau-ml-scalper-v2`.
  Publication does not promote any experiment to a Stable artefact.
- `v1-r3/` is included in Git with owner authorization (2026-11-01); its research status
  remains as documented below.
- `v1-rx/` is a local compatibility junction to `v1-r1/` and is not included in Git.
- Read-only on `D:\xau-ml-scalper\data\raw\...`; protected years 2023+ are never read.
- `cache/` and `*.private.*` files hold price-derived arrays and stay local.

Current revision: **v1-r2** (v1-r1 + per-session formulas, 2026-10-31). Previous: **v1-r1** (formerly v1-rx).
v1-r3 (literature filters, 2026-11-01) = NOT_CONFIRMED. Next developments: **v1-r4, v1-r5, …**.
See [version policy](VERSIONING.md) and `VERSIONS.json`.

| Folder | Topic | Status |
|---|---|---|
| `v1-r2/` | **Current v1-r2** (D058-S1): v1-r1 + per-session formulas (A Asia theta$ >= 2.16; B London k 2.5, theta$ >= 4; B NY afternoon theta$ >= 4, leg 2.5); entrypoint v1_r2.py | PASS 2026-10-31 on reused 2017-19 at 0.1 lot: +36,020 THB / DD 21,736 vs v1-r1 +21,785 / 22,878; 2010-22 +526,466 / DD 43,478 vs +408,699 / 57,247; daily-difference t 1.8 (2017-19), 1.67 (2020-22); see RESULTS.md |
| `v1-r3/` | v1-r3: 46 literature-driven entry-filter cells on v1-r2 (deadline, settlement, jumps, news, seasonal theta, vol surprise, GVZ, S&P flight-to-gold, round numbers); select 2010-16 | NOT_CONFIRMED 2026-11-01: only B settlement veto survived the random-block null (+7,154 THB on 7 trades) but DD unchanged; most filters cut profit; 2017+ not opened; see RESULTS.md |
| `data-ext/` | Owner-approved external downloads (2026-11-01), truncated at 2022-12-31: GVZ (CBOE), NFP/CPI/GDP dates, FOMC times, Dukascopy US500 M1 (2012+) | see README.md; US500 files are private |
| `lit-review-v1r2/` | Literature review (Consensus deep, 100 papers; Scite checks) for improving v1-r2; ranked price-only experiments | done 2026-11-01; see REVIEW.md (top: deadline admission / settlement window, jump-concentration filter, seasonal jump-robust theta; extra-data ideas need approval) |
| `v1-r1/` | Previous revision v1-r1, daily-close D058; entrypoint v1_r1.py | renamed from v1-rx; report daily/RESULTS_2010_2022_LOT05.md.0.5lot per rule2010–2022 net2,043,493THB;0/4,482 trades cross configured close. Next revision v1-r2; v1-rx remains a compatibility alias |
| `microstructure-edge-map/` | Step 0 spread map + step 1 random-walk deviation scan, 2010-2022 | done 2026-10-31; see RESULTS.md (16:00 NY reversal = step-2 hypothesis) |
| `pattern-structure/` | 27 three-segment patterns (5 families), rates vs random nulls, playability after spread | done 2026-10-31; see RESULTS.md (only 16:00 NY playable) |
| `swing-structure/` | $1-10 (today's $) zigzag swings, 8 market-structure patterns, follow/fade after owner cost | done 2026-10-31; see RESULTS.md (fade edge small, not robust) |
| `swing-fade-exec/` | Swing fade with 1-min delayed fills and a stop-loss, 2010-2022 only | done 2026-10-31; see RESULTS.md (all 4 cells fail) |
| `swing-adaptive-bounce/` | Bounce = k x sigma60 (volatility-scaled), by leg size, 2010-2019; 2020-22 sealed | done 2026-10-31; see RESULTS.md (k 1 and 1.5 after a large leg pass disc + val) |
| `swing-factors-b1/` | 8 price factors on the two adaptive cells: entry, TP-extension, stop risk | done 2026-10-31; see RESULTS.md (0/32 pass; leads: session, stop vs sigma1440) |
| `swing-rule-v1/` | Variants: theta/stop from max(sigma60, sigma1440), Asia filter, 2010-2019 | done 2026-10-31; see RESULTS.md (k 1 V2 accepted; k 1.5 stays base; Asia rejected) |
| `swing-improve-v2/` | Volume/spread factors (batch 2) and drawdown controls for rules A and B, 2010-2019 | done 2026-10-31; see RESULTS.md (0/16 factors; A+B half size accepted, max DD -30%) |
| `swing-holdout-2020-22/` | One-shot exam of frozen rules A + B on 2020-2022 (owner 14:06) | done 2026-10-31; see RESULTS.md (A+B PARTIAL in today's-price units; at the time's prices +75,598 THB at 0.1 lot over 3 years) |
| `swing-ml-wf/` | CatBoost walk-forward filter on rules A + B, 2010-2019, money at the time's prices | done 2026-10-31; see RESULTS.md (seed 7 passes, 1/5 other seeds; not robust; ML parked by owner) |
| `swing-c0-range/` | C0 range formula: leg stretch filter and range-based TP/SL, 2010-2019 | done 2026-10-31; see RESULTS.md (stretch no effect; no exit beats current) |
| `swing-bzone/` | Swing strategy with the peak at a Model B (E68 A2) zone rejection, 2011-2019 | done 2026-10-31; see RESULTS.md (156 trades only, not passed; scale mismatch with the owner's pattern) |
| `swing-bzone-oracle/` | SELL on the bounce after a zone-to-zone run down; ratios searched 2011-16, locked, 2017-19 blind | done 2026-10-31; see RESULTS.md (no edge at the drawn size; zones add nothing; run >= 4u cell positive 2017-19 but locked filter had 7 trades) |
| `swing-cost-ratio/` | Rules A + B: filter by swing size in $ vs the spread (theta$/0.168) and leg ratio; select 2010-16, check 2017-19 | done 2026-10-31; see RESULTS.md (A: theta >= $2.16 passes, max DD 126k -> 59k with similar money; B filter fails) |
| `swing-entry-timing/` | Rules A + B (locked filters): limit / limit+fallback / stall / session-skip entries vs the immediate entry, 2010-16 | done 2026-10-31; see RESULTS.md (0/42 cells improve; bounce extension has momentum, immediate entry is best; 2017-19 not opened) |
| `swing-ext-stop/` | Rules A + B (locked filters): stop at 1-2.5 theta from entry vs 3 theta, 2010-16 | done 2026-10-31; see RESULTS.md (every tighter stop loses, monotone; keep 3 theta; 2017-19 not opened) |
| `swing-v1/` | **Swing v1 (frozen 2026-10-31)**: rules A + B with the swing-cost-ratio filters; SPEC.md + self-contained code/swing_v1.py | frozen rules; OFFICIAL figures from the swing-causal-execution engine (owner 21:58): 2010-22 end 613,360 THB, max equity DD 68,463, 2020-22 +154,150 (t 1.84, PARTIAL). Original v1 simulator figures kept for history only |
| `swing-v2-ruleC/` | Search for a rule C to add to v1: slower-scale fade, leg ride, follow a failing fade, 240-min breakout (16 cells), 2010-16 | done 2026-10-31; see RESULTS.md (0/16 qualify; all follow/momentum rules lose gross; near miss fade at 2 x eff, flat 2014-16; 2017-19 not opened) |
| `swing-tf-tune/` | v1 swing setup re-tuned per timeframe (5m/15m/30m/1h; k, type, leg), select 2010-16, check 2017-19 | done 2026-10-31; see RESULTS.md (all 4 FAIL 2017-19: -7.6k to -31.8k THB vs v1 1m +64.3k; big-theta picks earn mostly 2010-12) |
| `swing-v1-audit-check/` | Fact-check of the swing-causal-execution audit: each correction alone on the frozen v1 code, 2010-19 | done 2026-10-31; see RESULTS.md (all audit points real but small; largest = volatility across missing minutes -18.9k; all together +352k vs audit +359k vs v1 +379k) |
| `swing-v1-flat-daily/` | v1 on the audit engine, always flat before the market closes (16:55 NY daily, DST-aware; holiday early closes) | done 2026-10-31; see RESULTS.md (0 trades across a day/gap; 2010-22 end 561,405 THB, max DD 60,899; vs holding through breaks 613,360 / 68,463, swap not modelled) |
| `swing-v1-stop-follow/` | After a v1 stop-out, follow the move (5 exit variants), Exness version, 2010-16 select | done 2026-10-31; see RESULTS.md (0/5 qualify; brackets hit at random-walk rates; best = hold to cutoff +39.8k over 13 yrs, t 0.4, DD up; not recommended) |
| `swing-v2-ruleC-r2/` | Rule C round 2: fade the extended leg (12 cells) and fade big moves into scheduled times (LBMA AM/PM, 08:30, 09:30, 13:30 NY), 2010-16 | done 2026-10-31; see RESULTS.md (0/14 qualify; best R1 A m5 t 1.0, 0.25/day; scheduled fades lose; 2017-19 not opened) |
| `swing-causal-execution/` | Engineering audit: causal fills, costs, liquidation equity; owner-authorized extension through2020-2022 | see RESULTS.md and RESULTS_2020_2022.md; corrected2020-22 +154,150THB, t1.84 (still PARTIAL by old bar); fixed-spread2010-22 end613,360; frozen v1 preserved; 2023+ closed |
