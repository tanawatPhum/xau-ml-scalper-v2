# ML walk-forward filter for swing rules A and B (written before any outcome)

Owner 14:48 ICT, 31 Oct: try ML with walk-forward on 2010-2019; 2020-2022 stays the occasional
exam (not used here); 2023-2026 locked until the owner unlocks it.
Owner reporting rules: money at 0.1 lot per trade (each rule), at the gold price of the time.

## Trades (unchanged frozen rules A and B)
- Rule A: theta = 1 x max(sigma60, sigma1440); rule B: theta = 1.5 x sigma60. Fade a confirmed
  bounce after a leg >= 2.5 theta; entry/exit 1 minute late; exit next swing; stop 3 theta; flat
  before the daily break. Both rules' trades form one pool (feature "rule").
- Outcome at the time: net_bps = gross move in bps - cost_bps, cost_bps = $0.168 / entry price x 1e4
  (fixed-dollar spread at that time's price). Money: net_usd = real price difference - $0.168.

## Features (known at the entry decision; nothing from the future)
rule; theta_bps; cost_bps; theta_over_cost; legsize (B / theta); legtime; bouncetime; volratio
(sigma60 / sigma1440); session hour; day of week; htf (k = 3 swing with / against / none);
rangepos (24 h range position); structure family; vol_bounce_leg; vol_bounce_day; vol_climax;
spread_rel (Dukascopy spread / its 24 h median).

## Model and walk-forward (fixed now, no tuning)
- CatBoostRegressor on net_bps: depth 4, learning_rate 0.03, 400 iterations, l2_leaf_reg 10,
  RMSE loss, random_seed 7, categorical: rule, session, dow, htf, structure. No early stopping.
- Expanding window: for each test year Y = 2012..2019, train on all trades of 2010..Y-1, predict Y.
- Decision: take a trade only if the predicted net_bps > 0.

## Acceptance (all required, test years 2012-2019 together, money at the time, 0.1 lot each rule)
1. Total net THB higher than the take-all baseline on the same years.
2. Max drawdown (THB, closed trades) lower than the baseline.
3. ML net >= baseline net in at least 5 of the 8 test years.
If accepted, the next step is a frozen model (trained on 2010-2019) for one 2020-2022 exam, run
only when the owner says so.

## Reported
Per test year: trades kept, net per trade, net THB, max drawdown, vs baseline; pooled totals;
feature importance of the model trained on 2010-2019 (descriptive).
