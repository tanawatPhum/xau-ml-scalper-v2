"""Rule variants v1 (see ../PLAN.md). 2010-2019 only."""

import json
import sys
from pathlib import Path

import numpy as np

import importlib.util

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-adaptive-bounce" / "code"))
from adaptive import COST_BPS, U, YEARS, apply_stop, load_series, sigma60  # noqa: E402

_spec = importlib.util.spec_from_file_location("factors_build", ROOT.parent / "swing-factors-b1" / "code" / "build.py")
_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fb)
sigma_long, zigzag_x = _fb.sigma_long, _fb.zigzag_x

OUT = ROOT / "out"
RUN_YEARS = [y for y in YEARS if y <= 2019]
DAYS = {int(k): v for k, v in json.load(open(ROOT.parent / "swing-adaptive-bounce" / "out" / "TRADING_DAYS.json")).items()}
DISC, VAL = list(range(2010, 2017)), list(range(2017, 2020))


def run(y, mins, blk, T, S):
    """T: zigzag threshold per minute; S: stop scale per minute (stop = 3 x S at the event)."""
    n = len(y)
    idx, d, ext, exi, th = zigzag_x(y, blk, T)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(len(idx), np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    brel = B / th
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    nxt = np.r_[idx[1:], -1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, nxt, last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (brel >= 2.5)
    ex = np.minimum(exit_i + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    sgn = -d.astype(np.float64)
    stop = 3.0 * S[idx]
    stop = np.where(np.isfinite(stop), stop, 3.0 * th)
    ent, ex, sgn, stop = ent[ok], ex[ok], sgn[ok], stop[ok]
    out_i, stopped = apply_stop(y, ent, ex, sgn, stop)
    gross = sgn * (y[out_i] - y[ent])
    tm = mins[ent].astype(np.int64)
    return dict(net=(gross - COST_BPS) * U, stopped=stopped, hour=(tm % 1440) // 60,
                day=(tm * 60 + 3 * 3600) // 86400, t=tm)


def stats(z, yrs):
    m = np.isin(z["yr"], yrs)
    x, day, t = z["net"][m], z["day"][m], z["t"][m]
    ndays = sum(DAYS[y] for y in yrs)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    o = np.argsort(t, kind="stable")
    eq = np.cumsum(x[o])
    dd = float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max())
    w = x > 0
    yp = sum(1 for y in yrs if (z["yr"][m] == y).any() and x[z["yr"][m] == y].mean() > 0)
    return dict(n=int(m.sum()), per_day=float(m.sum() / ndays), net=float(mu), t=float(mu / se),
                net_per_day=float(x.sum() / ndays), years_pos=f"{yp}/{len(yrs)}",
                stop=float(z["stopped"][m].mean()), win=float(w.mean()), avg_win=float(x[w].mean()),
                avg_loss=float(x[~w].mean()), p1=float(np.quantile(x, 0.01)), worst=float(x.min()), max_dd=dd)


data = {yr: load_series(yr) for yr in RUN_YEARS}
rows = {}
for k in (1.0, 1.5):
    for v in ("V0", "V1", "V2"):
        parts = []
        for yr in RUN_YEARS:
            y, mins, blk = data[yr]
            s60 = sigma60(y, blk)
            sl = sigma_long(y, blk)
            seff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
            T = k * (seff if v == "V2" else s60)
            S = k * (seff if v in ("V1", "V2") else s60)
            r = run(y, mins, blk, T, S)
            r["yr"] = np.full(len(r["net"]), yr)
            parts.append(r)
        z = {f: np.concatenate([p[f] for p in parts]) for f in parts[0]}
        rows[(k, v)] = z
        if k == 1.0:
            keep = z["hour"] >= 7
            rows[(k, v + "S")] = {f: a[keep] for f, a in z.items()}

rep = {}
for (k, v), z in rows.items():
    rep[f"k{k:g} {v}"] = {"2010-16": stats(z, DISC), "2017-19": stats(z, VAL)}


def better(a, b):  # a improves on b in both periods, per trade and per day
    return all(rep[a][p]["net"] > rep[b][p]["net"] and rep[a][p]["net_per_day"] > rep[b][p]["net_per_day"]
               for p in ("2010-16", "2017-19"))


accept = {}
for k in ("k1", "k1.5"):
    cands = [v for v in ("V1", "V2") if better(f"{k} {v}", f"{k} V0")]
    if len(cands) == 2:
        tot = {v: sum(rep[f"{k} {v}"][p]["net_per_day"] * (7 if p == "2010-16" else 3) for p in ("2010-16", "2017-19"))
               for v in cands}
        cands = [max(tot, key=tot.get)]
    base = cands[0] if cands else "V0"
    rule = base
    if k == "k1" and better(f"{k} {base}S", f"{k} {base}"):
        rule = base + "S"
    accept[k] = dict(stop_component=cands[0] if cands else "none", session_filter=rule.endswith("S"), rule=rule)
rep["acceptance"] = accept
json.dump(rep, open(OUT / "REPORT.json", "w"), indent=1)

for name, r in rep.items():
    if name == "acceptance":
        continue
    print(name)
    for p, s in r.items():
        print(f"   {p}: n {s['n']:5d} ({s['per_day']:.2f}/day) net {s['net']:+.3f} (t {s['t']:+.1f}) "
              f"per day {s['net_per_day']:+.3f} | years>0 {s['years_pos']} | stop {100 * s['stop']:.1f}% win "
              f"{100 * s['win']:.1f}% avg +{s['avg_win']:.2f}/{s['avg_loss']:.2f} p1 {s['p1']:.1f} worst {s['worst']:.1f} "
              f"maxDD {s['max_dd']:.0f}")
print("acceptance:", accept)
