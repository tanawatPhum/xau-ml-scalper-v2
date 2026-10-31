"""Owner 14:40: re-check the money report using the gold price AT THE TIME, not today's price.
Same frozen rules A and B and the same trades as exam.py. P&L per oz:
- today_usd  : old report method (bps move x 4083.276 - 0.168), for reference only;
- hist_usd   : real price difference at the time (mid), minus a fixed $0.168 spread per round trip;
- hist_duka  : real price difference, minus Dukascopy's own spread at that minute (half at entry,
               half at exit), as a stress reference.
Money: 0.1 lot each rule (10 oz), 100,000 THB start, USD/THB held at 33.77 (historical FX not
available offline). 2010-2019 design years, 2020-2022 exam years."""
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
    spec.loader.exec_module(ex)
EDGE = HERE.parents[1] / "microstructure-edge-map" / "cache"
OZ, FX, START, SPREAD = 10, 33.77, 100_000.0, 0.168


def run_year(yr, k, kind):
    y, mins, blk = ex.load_series(yr)
    n = len(y)
    s60 = ex.sigma60(y, blk)
    sl = ex.sigma_long(y, blk)
    seff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    T = k * (seff if kind == "eff" else s60)
    idx, d, ext, exi, th = ex.zigzag_x(y, blk, T)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(len(idx), np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (B / th >= 2.5)
    ex_ = np.minimum(exit_i + 1, n - 1)
    ex_ = np.where(blk[ex_] == eb, ex_, exit_i)
    ok &= ex_ > ent
    sgn = -d[ok].astype(np.float64)
    e = ent[ok]
    out_i, _ = ex.apply_stop(y, e, ex_[ok], sgn, 3.0 * th[ok])
    zp = np.load(EDGE / f"M1_{yr}.private.npz")
    pos = (mins - int(zp["base"])).astype(np.int64)
    bid, ask = zp["bid"][pos], zp["ask"][pos]
    mid = (bid + ask) / 2
    today = (sgn * (y[out_i] - y[e]) - ex.COST_BPS) * ex.U
    hist = sgn * (mid[out_i] - mid[e]) - SPREAD
    duka = sgn * (mid[out_i] - mid[e]) - ((ask - bid)[e] + (ask - bid)[out_i]) / 2
    return dict(today=today, hist=hist, duka=duka, price=mid[e], t_exit=mins[out_i].astype(np.int64),
                yr=np.full(len(e), yr))


parts = {r: [run_year(yr, *ex.RULES[r]) for yr in range(2010, 2023)] for r in ("A", "B")}
Z = {r: {f: np.concatenate([p[f] for p in v]) for f in v[0]} for r, v in parts.items()}
# sanity: identical trades to the exam code
for r in ("A", "B"):
    m = (Z[r]["yr"] >= 2020)
    print(f"check rule {r} 2020-22: n {m.sum()} today-$ net {Z[r]['today'][m].mean():+.3f}")
AB = {f: np.concatenate([Z["A"][f], Z["B"][f]]) for f in Z["A"]}
rule = np.r_[np.zeros(len(Z["A"]["today"]), int), np.ones(len(Z["B"]["today"]), int)]
o = np.argsort(AB["t_exit"], kind="stable")
AB = {f: a[o] for f, a in AB.items()}
rule = rule[o]
out = {}
for key in ("hist", "duka", "today"):
    pnl = AB[key] * OZ * FX
    eq = START + np.cumsum(pnl)
    peak = np.maximum.accumulate(np.r_[START, eq])[1:]
    rows, e0 = {}, START
    for y in range(2010, 2023):
        m = AB["yr"] == y
        p = pnl[m]
        e = e0 + np.cumsum(p)
        pk = np.maximum.accumulate(np.r_[e0, e])[1:]
        rows[y] = dict(start=e0, wins=float(p[p > 0].sum()), losses=float(p[p <= 0].sum()), net=float(p.sum()),
                       end=float(e[-1]), best=float(p.max()), worst=float(p.min()), dd=float((pk - e).max()),
                       win=float((p > 0).mean()), net_A=float(p[rule[m] == 0].sum()), net_B=float(p[rule[m] == 1].sum()),
                       per_trade_usd_oz=float(AB[key][m].mean()), avg_price=float(AB["price"][m].mean()),
                       spread_bps=float(SPREAD / AB["price"][m].mean() * 1e4))
        e0 = float(e[-1])
    out[key] = dict(rows=rows, end=float(eq[-1]), max_dd=float((peak - eq).max()), lowest=float(eq.min()))
json.dump(out, open(HERE.parent / "out" / "HISTORICAL_PRICE_01LOT.json", "w"), indent=1)
for key, title in (("hist", "REAL PRICE AT THE TIME, spread $0.168 fixed"), ("duka", "REAL PRICE, Dukascopy spread"),
                   ("today", "OLD METHOD (today's price)")):
    r = out[key]
    print(f"\n=== {title}: end {r['end']:,.0f} THB | max DD {r['max_dd']:,.0f} | lowest {r['lowest']:,.0f}")
    print("year | avg price | spread bps | net/trade $/oz | win | start | wins | losses | net | end | best | worst | DD in year | A | B")
    for y, s in r["rows"].items():
        print(f"{y} | {s['avg_price']:,.0f} | {s['spread_bps']:.2f} | {s['per_trade_usd_oz']:+.3f} | {100 * s['win']:.0f}% | "
              f"{s['start']:,.0f} | {s['wins']:+,.0f} | {s['losses']:+,.0f} | {s['net']:+,.0f} | {s['end']:,.0f} | "
              f"{s['best']:+,.0f} | {s['worst']:+,.0f} | {s['dd']:,.0f} | {s['net_A']:+,.0f} | {s['net_B']:+,.0f}")
