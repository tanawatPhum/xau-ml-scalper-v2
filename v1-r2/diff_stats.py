"""v1-r2 vs v1-r1: day-clustered t of the daily net difference, and where the difference comes from.

Reads only out/TRADES_2010_2022_v1-r{1,2}.private.csv (fixed spread, continuous 2010-2022 run).
Trading day = NY time + 6 h (18:00 NY starts the next day; positions are flat daily).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "out"
SES = {0: "Asia", 1: "London", 2: "NY morning", 3: "NY afternoon"}
PERIODS = {"2010-2016": (2010, 2016), "2017-2019": (2017, 2019), "2020-2022": (2020, 2022)}


def load(v):
    t = pd.read_csv(OUT / f"TRADES_2010_2022_{v}.private.csv")
    sig = pd.to_datetime(t.t_signal * 60, unit="s", utc=True).dt.tz_convert("America/New_York")
    mod = sig.dt.hour * 60 + sig.dt.minute
    t["session"] = np.where((mod >= 18 * 60) | (mod < 3 * 60), 0, np.where(mod < 8 * 60, 1, np.where(mod < 12 * 60, 2, 3)))
    ex = pd.to_datetime(t.t_exit * 60, unit="s", utc=True).dt.tz_convert("America/New_York")
    t["day"] = (ex + pd.Timedelta(hours=6)).dt.date
    t["year"] = pd.to_datetime(t.t_exit * 60, unit="s", utc=True).dt.year
    return t


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 1 and x.std(ddof=1) > 0 else 0.0


def main():
    r1, r2 = load("v1-r1"), load("v1-r2")
    res = {}
    for name, (a, b) in PERIODS.items():
        p1, p2 = r1[r1.year.between(a, b)], r2[r2.year.between(a, b)]
        d1, d2 = p1.groupby("day").net_thb.sum(), p2.groupby("day").net_thb.sum()
        days = d1.index.union(d2.index)
        d1, d2 = d1.reindex(days, fill_value=0.0), d2.reindex(days, fill_value=0.0)
        diff = d2 - d1
        cells = {}
        for rule in ("A", "B"):
            for s, sn in SES.items():
                n1 = p1[(p1.rule == rule) & (p1.session == s)]
                n2 = p2[(p2.rule == rule) & (p2.session == s)]
                cells[f"{rule} {sn}"] = dict(r1_trades=int(len(n1)), r1_net=round(float(n1.net_thb.sum())),
                                             r2_trades=int(len(n2)), r2_net=round(float(n2.net_thb.sum())),
                                             diff=round(float(n2.net_thb.sum() - n1.net_thb.sum())))
        res[name] = dict(days=int(len(days)), r1_net=round(float(d1.sum())), r2_net=round(float(d2.sum())),
                         diff_net=round(float(diff.sum())), t_r1=round(tstat(d1), 2), t_r2=round(tstat(d2), 2),
                         t_diff=round(tstat(diff), 2), days_changed=int((diff.abs() > 1e-6).sum()), cells=cells)
    (OUT / "DIFF_STATS.json").write_text(json.dumps(res, indent=1))
    for name, r in res.items():
        print(f"{name}: r1 {r['r1_net']:+,} (t {r['t_r1']}) | r2 {r['r2_net']:+,} (t {r['t_r2']}) | "
              f"diff {r['diff_net']:+,} t_diff {r['t_diff']} | days {r['days']} changed {r['days_changed']}")
        for k, c in r["cells"].items():
            print(f"   {k:16s} r1 {c['r1_trades']:4d} {c['r1_net']:+9,} | r2 {c['r2_trades']:4d} {c['r2_net']:+9,} | diff {c['diff']:+9,}")


if __name__ == "__main__":
    main()
