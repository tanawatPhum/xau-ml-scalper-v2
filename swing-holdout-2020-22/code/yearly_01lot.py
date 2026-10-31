"""Owner view 14:20: 2010-2022 per year, 100,000 THB start, rules A and B at 0.1 lot each (10 oz),
USD/THB 33.77, after spread. 2010-2019 = design years (in-sample), 2020-2022 = one-shot exam."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("exam", HERE / "exam.py")
ex = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(ex)  # same frozen rules and the same code as the exam
H, _ = ex.collect(list(range(2010, 2023)))
OZ, FX, START = 10, 33.77, 100_000.0
net = np.concatenate([H["A"]["net"], H["B"]["net"]]) * OZ * FX
te = np.concatenate([H["A"]["t_exit"], H["B"]["t_exit"]])
yr = np.concatenate([H["A"]["yr"], H["B"]["yr"]])
rule = np.r_[np.zeros(len(H["A"]["net"]), int), np.ones(len(H["B"]["net"]), int)]
o = np.argsort(te, kind="stable")
net, te, yr, rule = net[o], te[o], yr[o], rule[o]
eq = START + np.cumsum(net)
rows, e0 = {}, START
for y in range(2010, 2023):
    m = yr == y
    p = net[m]
    e = e0 + np.cumsum(p)
    pk = np.maximum.accumulate(np.r_[e0, e])[1:]
    rows[y] = dict(start=e0, wins=float(p[p > 0].sum()), losses=float(p[p <= 0].sum()), net=float(p.sum()),
                   end=float(e[-1]), best=float(p.max()), worst=float(p.min()), dd=float((pk - e).max()),
                   trades=int(m.sum()), win=float((p > 0).mean()), net_A=float(p[rule[m] == 0].sum()),
                   net_B=float(p[rule[m] == 1].sum()))
    e0 = float(e[-1])
peak = np.maximum.accumulate(np.r_[START, eq])[1:]
i = int(np.argmax(peak - eq))
whole = dict(end=float(eq[-1]), max_dd=float((peak - eq).max()), dd_date=str((te[i] * 60).astype("datetime64[s]").astype("datetime64[D]")),
             lowest=float(eq.min()), best=float(net.max()), worst=float(net.min()))
json.dump(dict(rows=rows, whole=whole), open(HERE.parent / "out" / "YEARLY_01LOT_2010_2022.json", "w"), indent=1)
print("year | start | sum of wins | sum of losses | net | end | best trade | worst trade | max DD in year | trades | win | net A | net B")
for y, r in rows.items():
    print(f"{y} | {r['start']:,.0f} | {r['wins']:+,.0f} | {r['losses']:+,.0f} | {r['net']:+,.0f} | {r['end']:,.0f} | "
          f"{r['best']:+,.0f} | {r['worst']:+,.0f} | {r['dd']:,.0f} | {r['trades']} | {100 * r['win']:.0f}% | {r['net_A']:+,.0f} | {r['net_B']:+,.0f}")
print("whole:", whole)
