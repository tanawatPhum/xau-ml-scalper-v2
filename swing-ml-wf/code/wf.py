"""Expanding-window walk-forward CatBoost filter (pre-registered in ../PLAN.md). 2010-2019 only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_pickle(ROOT / "cache" / "DATASET.private.pkl")
assert df["yr"].max() <= 2019
df["session"] = pd.cut(df["hour"], [-1, 6, 12, 20, 23], labels=["asia", "london", "ny", "late"]).astype(str)
for c in ("dow", "htf", "structure"):
    df[c] = df[c].astype(int).astype(str)
CAT = ["rule", "session", "dow", "htf", "structure"]
NUM = ["theta_bps", "cost_bps", "theta_over_cost", "legsize", "legtime", "bouncetime", "volratio", "rangepos",
       "vol_bounce_leg", "vol_bounce_day", "vol_climax", "spread_rel"]
FEAT = CAT + NUM
PARAMS = dict(depth=4, learning_rate=0.03, iterations=400, l2_leaf_reg=10, loss_function="RMSE", random_seed=7,
              verbose=False, allow_writing_files=False)
THB = 10 * 33.77  # 0.1 lot = 10 oz, USD/THB 33.77


def fit(train):
    m = CatBoostRegressor(**PARAMS)
    m.fit(train[FEAT], train["net_bps"], cat_features=CAT)
    return m


preds = []
for Y in range(2012, 2020):
    tr, te = df[df["yr"] < Y], df[df["yr"] == Y].copy()
    te["pred"] = fit(tr).predict(te[FEAT])
    preds.append(te)
    print("trained through", Y - 1, "-> predicted", Y, flush=True)
T = pd.concat(preds).sort_values("t_exit", kind="stable")
T["take"] = T["pred"] > 0
T["thb"] = T["net_usd"] * THB


def path_stats(x):
    eq = np.cumsum(x)
    dd = float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max()) if len(x) else 0.0
    return float(x.sum()), dd


rows = {}
for Y in range(2012, 2020):
    s = T[T["yr"] == Y]
    bt, bdd = path_stats(s["thb"].to_numpy())
    mt, mdd = path_stats(s.loc[s["take"], "thb"].to_numpy())
    rows[Y] = dict(trades=len(s), kept=int(s["take"].sum()), base_net=bt, base_dd=bdd, ml_net=mt, ml_dd=mdd,
                   base_per_trade=float(s["net_usd"].mean()), ml_per_trade=float(s.loc[s["take"], "net_usd"].mean()))
bt, bdd = path_stats(T["thb"].to_numpy())
mt, mdd = path_stats(T.loc[T["take"], "thb"].to_numpy())
wins = sum(1 for r in rows.values() if r["ml_net"] >= r["base_net"])
accept = bool(mt > bt and mdd < bdd and wins >= 5)
# ranking diagnostic: test outcome by prediction decile (pooled)
T["dec"] = pd.qcut(T["pred"], 10, labels=False, duplicates="drop")
dec = T.groupby("dec").agg(n=("net_usd", "size"), pred_bps=("pred", "mean"), net_usd=("net_usd", "mean")).round(3)
spear = float(T[["pred", "net_bps"]].corr(method="spearman").iloc[0, 1])
final = fit(df)
imp = dict(sorted(zip(FEAT, final.get_feature_importance(), strict=True), key=lambda kv: -kv[1]))
rep = dict(years=rows, pooled=dict(base_net=bt, base_dd=bdd, ml_net=mt, ml_dd=mdd, base_trades=len(T),
                                   ml_trades=int(T["take"].sum()), years_ml_ge_base=wins, ACCEPT=accept,
                                   spearman=spear), deciles=dec.reset_index().to_dict(orient="records"),
           importance={k: float(v) for k, v in imp.items()})
json.dump(rep, open(ROOT / "out" / "WF.json", "w"), indent=1)
print("\nyear | trades | kept | base net/trade $/oz | ML net/trade | base THB | ML THB | base DD | ML DD")
for Y, r in rows.items():
    print(f"{Y} | {r['trades']} | {r['kept']} | {r['base_per_trade']:+.3f} | {r['ml_per_trade']:+.3f} | {r['base_net']:+,.0f} | "
          f"{r['ml_net']:+,.0f} | {r['base_dd']:,.0f} | {r['ml_dd']:,.0f}")
print(f"\npooled 2012-19: base {len(T)} trades net {bt:+,.0f} THB maxDD {bdd:,.0f} | ML {int(T['take'].sum())} trades net {mt:+,.0f} "
      f"maxDD {mdd:,.0f} | ML >= base in {wins}/8 years | spearman(pred, outcome) {spear:+.3f} | ACCEPT {accept}")
print("\ndeciles of prediction (test years pooled):\n", dec.to_string())
print("\nimportance (model on 2010-2019):", {k: round(v, 1) for k, v in imp.items()})
