"""Swing v1 one-shot exam on 2020-2022 (see ../EXAM_PLAN.md). Uses swing_v1.py unchanged."""
import json

import numpy as np
import pandas as pd

import swing_v1 as v1

EX = pd.concat([v1.trades_year(yr, r) for r in v1.RULES for yr in (2020, 2021, 2022)], ignore_index=True)
EX.to_pickle(v1.OUT / "V1_TRADES_2020_2022.private.pkl")
DEV = pd.read_pickle(v1.OUT / "V1_TRADES_2010_2019.private.pkl")


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


day = (EX["t_entry"] * 60 + 3 * 3600) // 86400
ndays = int(day.nunique())
mu, t = ct(EX["net_usd_oz"], day)
ypos = int(sum(EX.loc[EX["yr"] == y, "net_thb"].sum() > 0 for y in (2020, 2021, 2022)))
verdict = "PASS" if (mu > 0 and t >= 2 and ypos >= 2) else ("PARTIAL" if mu > 0 else "FAIL")
alone = v1.money_table(EX)
cont = v1.money_table(pd.concat([DEV, EX], ignore_index=True))
rules = {}
for r, g in EX.groupby("rule"):
    m, tt = ct(g["net_usd_oz"], (g["t_entry"] * 60 + 3 * 3600) // 86400)
    w, lo = g.loc[g["net_thb"] > 0, "net_thb"], g.loc[g["net_thb"] <= 0, "net_thb"]
    rules[r] = dict(trades=len(g), per_day=len(g) / ndays, net_usd_oz=m, t=tt, win=float((g["net_thb"] > 0).mean()),
                    avg_win=float(w.mean()), avg_loss=float(lo.mean()), stop_rate=float(g["stopped"].mean()), worst=float(g["net_thb"].min()),
                    thb=float(g["net_thb"].sum()), years={int(y): float(g.loc[g["yr"] == y, "net_thb"].sum()) for y in (2020, 2021, 2022)})
rep = dict(verdict=verdict, net_usd_oz=mu, t=t, years_positive=ypos, trades=len(EX), per_day=len(EX) / ndays, rules=rules,
           alone_100k=alone, continued_2010_2022=dict(end=cont["end"], max_dd=cont["max_dd"], dd_from=cont["dd_from"], dd_to=cont["dd_to"],
                                                      years={y: cont["years"][y] for y in (2020, 2021, 2022)}),
           unfiltered_exam_reference_thb=75_598)
json.dump(rep, open(v1.OUT / "V1_EXAM_2020_2022.json", "w"), indent=1)
print(f"VERDICT {verdict}: {len(EX)} trades ({len(EX) / ndays:.2f}/day), net {mu:+.3f} $/oz (t {t:+.2f}), years positive {ypos}/3")
for r, s in rules.items():
    print(f"rule {r}: {s['trades']} trades ({s['per_day']:.2f}/day) net {s['net_usd_oz']:+.3f} (t {s['t']:+.2f}) win {100 * s['win']:.0f}% "
          f"avg win {s['avg_win']:+,.0f} loss {s['avg_loss']:+,.0f} stop {100 * s['stop_rate']:.1f}% worst {s['worst']:+,.0f} | "
          f"total {s['thb']:+,.0f} | years {', '.join(f'{y} {v:+,.0f}' for y, v in s['years'].items())}")
print("\n2020-22 alone, 100,000 THB start:")
for y, v in alone["years"].items():
    print(f"  {y}: trades {v['trades']} win {100 * v['win']:.0f}% A {v['thb_A']:+,.0f} B {v['thb_B']:+,.0f} net {v['net']:+,.0f} "
          f"{v['start']:,.0f} -> {v['end']:,.0f} DD {v['dd']:,.0f} worst {v['worst']:+,.0f}")
print(f"  end {alone['end']:,.0f}, max DD {alone['max_dd']:,.0f} ({alone['dd_from']} -> {alone['dd_to']}), lowest {alone['lowest']:,.0f}")
print("\ncontinued from 2010 (100,000 THB in 2010):")
for y in (2020, 2021, 2022):
    v = cont["years"][y]
    print(f"  {y}: net {v['net']:+,.0f} end {v['end']:,.0f} DD in year {v['dd']:,.0f}")
print(f"  2010-2022 end {cont['end']:,.0f}, max DD {cont['max_dd']:,.0f} ({cont['dd_from']} -> {cont['dd_to']})")
