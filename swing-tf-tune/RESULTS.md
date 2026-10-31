# Results: swing setup re-tuned per timeframe (31 Oct 2026)
Plan PLAN.md (before outcomes). Code: code/build.py, select_.py (2010-16, out/LOCK.json),
check.py (2017-19, once). Money: 0.1 lot per rule, at the time's price, $0.168, 33.77 THB/USD.
Consistency: 5m type A k 1 leg 2.5 equals the v1-on-5m run (+65,714 THB 2010-19).
2020-22 not used; 2023+ closed.

## Selection on 2010-16 (20 cells per TF; big theta wins everywhere)
| TF | Chosen cells (t, family p) | 2010-16 THB of the chosen set |
|---|---|---|
| 5m | A k 1.5 leg 3.5 (t 2.94, p 0.024); no B qualified | +139,545 |
| 15m | A k 1.5 leg 3.5 (t 2.77, p 0.034); no B qualified | +138,593 |
| 30m | A k 2 leg 2.5 (t 2.80, p 0.036) + B k 2 leg 3.5 (t 4.12, p 0.000) | +423,132 |
| 1h | A k 1.5 leg 2.5 (t 2.48, p 0.082) + B k 2 leg 3.5 (t 3.69, p 0.002) | +396,329 |
v1 on 1m over 2010-16: +315,156 THB. On paper the re-tuned 30m and 1h looked better.

## Check 2017-19 (once): every re-tuned TF FAILS; v1 on 1m makes money
| Set | Trades | Net $/oz (t) | 2017 | 2018 | 2019 | Total THB | DD |
|---|---|---|---|---|---|---|---|
| 1m v1 | 1,429 | +0.133 (1.92) | +41,937 | -8,048 | +30,404 | +64,294 | 31,291 |
| 5m | 233 | -0.097 (-0.39) | +13,864 | -2,328 | -19,169 | -7,633 | 28,343 |
| 15m | 188 | -0.242 (-0.72) | +3,862 | -1,241 | -17,956 | -15,334 | 24,882 |
| 30m | 264 | -0.357 (-0.95) | -14,158 | +522 | -18,200 | -31,835 | 39,229 |
| 1h | 293 | -0.300 (-0.90) | +2,478 | +1,243 | -33,395 | -29,675 | 43,162 |

Money 2010-19 from 100,000 THB:

| Set | End capital (THB) | Max DD (THB) | Notes |
|---|---|---|---|
| 1m v1 | 479,450 | 58,773 | |
| 5m | 231,912 | 42,155 | |
| 15m | 223,258 | 29,130 | |
| 30m | 491,297 | 56,863 | +264,668 of it in 2011 alone |
| 1h | 466,654 | 60,837 | +209,624 in 2011 |

## Reading
- Re-tuning picks a large theta (1.5-2x) on every higher timeframe. Those rules earn mostly in
  the high-volatility years 2010-12, with the same pattern as the 1m near miss in swing-v2-ruleC,
  and then lose in 2017-19.
- The 1m advantage is not just tuning. Higher timeframes see the bounce later and check the stop
  less often, and the blind years show that.
- v1 stays on 1m.
