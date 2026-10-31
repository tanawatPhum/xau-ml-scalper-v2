"""Post-hoc robustness: the same walk-forward with 5 other random seeds (acceptance was borderline)."""
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

import wf as W  # noqa: F401  (re-runs the seed-7 study first; reuse its data and helpers)

out = []
for seed in (1, 2, 3, 4, 5):
    preds = []
    for Y in range(2012, 2020):
        tr, te = W.df[W.df["yr"] < Y], W.df[W.df["yr"] == Y].copy()
        m = CatBoostRegressor(**(W.PARAMS | {"random_seed": seed}))
        m.fit(tr[W.FEAT], tr["net_bps"], cat_features=W.CAT)
        te["pred"] = m.predict(te[W.FEAT])
        preds.append(te)
    T = pd.concat(preds).sort_values("t_exit", kind="stable")
    T["thb"] = T["net_usd"] * W.THB
    take = T["pred"] > 0
    bt, bdd = W.path_stats(T["thb"].to_numpy())
    mt, mdd = W.path_stats(T.loc[take, "thb"].to_numpy())
    wins = 0
    for Y in range(2012, 2020):
        s = T["yr"] == Y
        wins += T.loc[s & take, "thb"].sum() >= T.loc[s, "thb"].sum()
    acc = mt > bt and mdd < bdd and wins >= 5
    out.append((seed, mt, mdd, wins, acc, int(take.sum())))
    print(f"seed {seed}: ML net {mt:+,.0f} THB (base {bt:+,.0f}), maxDD {mdd:,.0f} (base {bdd:,.0f}), years {wins}/8, "
          f"trades {int(take.sum())}, ACCEPT {acc}", flush=True)
print("accepted in", sum(o[4] for o in out), "of 5 extra seeds")
