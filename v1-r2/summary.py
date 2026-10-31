"""Print the v1-r2 vs v1-r1 tables from out/EVALUATION.json and out/EXTEND_2010_2022.json."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent / "out"
X = json.loads((OUT / "EXTEND_2010_2022.json").read_text())
E = json.loads((OUT / "EVALUATION.json").read_text())
rows = []
for y in map(str, range(2010, 2023)):
    a, b = X["v1-r1"]["yearly"][y], X["v1-r2"]["yearly"][y]
    rows.append(dict(year=y, r1_net=a["net"], r2_net=b["net"], r2_wins=b["wins"], r2_losses=b["losses"], r2_end=b["end"], r1_dd=a["dd"], r2_dd=b["dd"],
                     r1_trades=a["trades"], r2_trades=b["trades"]))
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).round(0).to_string(index=False))
for v in ("v1-r1", "v1-r2"):
    m = X[v]["metrics"]
    print(v, {k: round(m[k]) for k in ("net", "dd", "trades", "lowest", "worst", "loss")}, "dd%", round(m["dd_pct"], 2), "by rule", X[v]["by_rule"])
print("\nsessions 2010-2022:")
print(pd.DataFrame({v: {s: f"{d['trades']} tr, win {d['win']:.0%}, {d['net']:+,.0f}" for s, d in X[v]["sessions"].items()} for v in X}).to_string())
print("\n2017-19 standalone:", {k: {v: {m: round(E['results']['validation'][k][v][m]) for m in ('net', 'dd', 'trades')} for v in ('v1-r1', 'v1-r2')}
                                for k in ('fixed', 'cost_example', 'historical')})
print("2010-19 continuous:", {k: {v: {m: round(E['results']['full'][k][v][m]) for m in ('net', 'dd', 'trades')} for v in ('v1-r1', 'v1-r2')}
                              for k in ('fixed', 'cost_example', 'historical')})
