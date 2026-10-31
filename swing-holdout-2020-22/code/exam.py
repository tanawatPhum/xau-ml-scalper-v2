"""One-shot holdout exam (see ../PLAN.md). Step 1 reproduces 2017-2019; step 2 runs 2020-2022."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
sys.path.insert(0, str(ROOT.parent / "swing-adaptive-bounce" / "code"))
from adaptive import COST_BPS, U, apply_stop, load_series, sigma60  # noqa: E402

_spec = importlib.util.spec_from_file_location("factors_build", ROOT.parent / "swing-factors-b1" / "code" / "build.py")
_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fb)
sigma_long, zigzag_x = _fb.sigma_long, _fb.zigzag_x
FX = 33.77
RULES = {"A": (1.0, "eff"), "B": (1.5, "s60")}


def run_year(yr, k, kind):
    y, mins, blk = load_series(yr)
    n = len(y)
    s60 = sigma60(y, blk)
    sl = sigma_long(y, blk)
    seff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    T = k * (seff if kind == "eff" else s60)
    idx, d, ext, exi, th = zigzag_x(y, blk, T)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(len(idx), np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (B / th >= 2.5)
    ex = np.minimum(exit_i + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    sgn = -d.astype(np.float64)
    out_i, stopped = apply_stop(y, ent[ok], ex[ok], sgn[ok], 3.0 * th[ok])
    gross = sgn[ok] * (y[out_i] - y[ent[ok]])
    te = mins[ent[ok]].astype(np.int64)
    t = (mins.astype(np.int64) * 60 + 3 * 3600) // 86400
    ud = np.unique(t)
    days = int(np.sum(((ud + 3) % 7) < 5))
    return dict(net=(gross - COST_BPS) * U, stop=stopped, t_ent=te, t_exit=mins[out_i].astype(np.int64),
                day=(te * 60 + 3 * 3600) // 86400, yr=np.full(len(te), yr)), days


def collect(years):
    res, days = {}, {}
    for r, (k, kind) in RULES.items():
        parts = []
        for yr in years:
            p, dd = run_year(yr, k, kind)
            parts.append(p)
            days[yr] = dd
        res[r] = {f: np.concatenate([p[f] for p in parts]) for f in parts[0]}
    return res, days


def ct(x, day):
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


def maxdd(p, te):
    o = np.argsort(te, kind="stable")
    eq = np.cumsum(p[o])
    return float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max())


# ---- step 1: reproduce 2017-2019
chk, _ = collect([2017, 2018, 2019])
na, ma = len(chk["A"]["net"]), chk["A"]["net"].mean()
nb, mb = len(chk["B"]["net"]), chk["B"]["net"].mean()
print(f"CHECK 2017-19: A {na} trades net {ma:+.3f} (expect 2034 / +0.504); B {nb} trades net {mb:+.3f} (expect 1791 / +0.583)")
assert na == 2034 and abs(ma - 0.504) < 0.0015 and nb == 1791 and abs(mb - 0.583) < 0.0015, "reproduction failed"

# ---- step 2: the exam
H, DAYS = collect([2020, 2021, 2022])
rep = {"days": DAYS}
for r in ("A", "B"):
    z = H[r]
    mu, t = ct(z["net"], z["day"])
    rep[r] = dict(trades=len(z["net"]), per_day=len(z["net"]) / sum(DAYS.values()), net=mu, t=t,
                  win=float((z["net"] > 0).mean()), stop=float(z["stop"].mean()), worst=float(z["net"].min()),
                  max_dd=maxdd(z["net"], z["t_exit"]),
                  years={int(y): dict(n=int((z["yr"] == y).sum()), net=float(z["net"][z["yr"] == y].mean()),
                                      total=float(z["net"][z["yr"] == y].sum())) for y in (2020, 2021, 2022)})
AB = {f: np.concatenate([H["A"][f], H["B"][f]]) for f in H["A"]}
half = 0.5 * AB["net"]
mu, t = ct(AB["net"], AB["day"])
ypos = sum(1 for y in (2020, 2021, 2022) if AB["net"][AB["yr"] == y].mean() > 0)
verdict = "PASS" if (mu > 0 and t >= 2 and ypos >= 2) else ("PARTIAL" if mu > 0 else "FAIL")
rep["A+B"] = dict(trades=len(AB["net"]), net=mu, t=t, years_pos=ypos, verdict=verdict,
                  max_dd_per_oz_eq=maxdd(half, AB["t_exit"]), hist_max_dd_per_oz_eq=262.6,
                  years={int(y): float(AB["net"][AB["yr"] == y].mean()) for y in (2020, 2021, 2022)})
# 100,000 THB, 0.01 lot each (1 oz each)
p_thb, te = AB["net"] * FX, AB["t_exit"]
o = np.argsort(te, kind="stable")
p_thb, te_s, yr_s = p_thb[o], te[o], AB["yr"][o]
eq = 100_000 + np.cumsum(p_thb)
thb, e0 = {}, 100_000.0
for y in (2020, 2021, 2022):
    m = yr_s == y
    e = e0 + np.cumsum(p_thb[m])
    pk = np.maximum.accumulate(np.r_[e0, e])[1:]
    a_m = m & (np.r_[np.zeros(len(H["A"]["net"]), int), np.ones(len(H["B"]["net"]), int)][o] == 0)
    thb[y] = dict(start=e0, pnl=float(p_thb[m].sum()), pnl_A=float(p_thb[a_m].sum()), pnl_B=float(p_thb[m & ~a_m].sum()),
                  end=float(e[-1]), dd=float((pk - e).max()), trades=int(m.sum()), win=float((p_thb[m] > 0).mean()))
    e0 = float(e[-1])
rep["thb_100k_001_each"] = dict(years=thb, max_dd=float((np.maximum.accumulate(np.r_[100_000, eq])[1:] - eq).max()),
                                lowest=float(eq.min()), end=float(eq[-1]))
json.dump(rep, open(OUT / "EXAM.json", "w"), indent=1)
for r in ("A", "B"):
    s = rep[r]
    print(f"\nRULE {r} 2020-22: {s['trades']} trades ({s['per_day']:.2f}/day), net {s['net']:+.3f} (t {s['t']:+.1f}), win "
          f"{100 * s['win']:.1f}%, stop {100 * s['stop']:.1f}%, worst {s['worst']:+.1f}, max DD/oz {s['max_dd']:.1f}")
    for y, v in s["years"].items():
        print(f"   {y}: n {v['n']} net/trade {v['net']:+.3f} total/oz {v['total']:+.1f}")
s = rep["A+B"]
print(f"\nA+B 2020-22: {s['trades']} trades, net {s['net']:+.3f} (t {s['t']:+.1f}), years>0 {s['years_pos']}/3, "
      f"max DD per oz-eq {s['max_dd_per_oz_eq']:.1f} (2010-19: 262.6) -> VERDICT {s['verdict']}")
print("   per year net/trade:", {y: round(v, 3) for y, v in s["years"].items()})
print("\n100,000 THB, 0.01 lot each:")
for y, v in thb.items():
    print(f"   {y}: trades {v['trades']} win {100 * v['win']:.0f}% A {v['pnl_A']:+,.0f} B {v['pnl_B']:+,.0f} total "
          f"{v['pnl']:+,.0f} | {v['start']:,.0f} -> {v['end']:,.0f} | max DD in year {v['dd']:,.0f}")
x = rep["thb_100k_001_each"]
print(f"   whole: end {x['end']:,.0f}, lowest {x['lowest']:,.0f}, max DD {x['max_dd']:,.0f}")
