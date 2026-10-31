"""v1-r4: lot sizing 0.1-0.5 on unchanged v1-r2 entries/exits, plus risk analysis (see PLAN.md).
Phases: check | design | evaluate | extend     (python -B v1-r4/v1_r4.py <phase>)
v1-r1 / v1-r2 / v1-r3 code and locks are imported read-only. No live orders. 2023+ is never read."""
import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "v1-r3"))
import v1_r3 as v3  # noqa: E402  (imports v1-r2 and v1-r1 read-only)

r2 = v3.r2
d = r2.d
OUT = ROOT / "out"
VERSION = "v1-r4"
START, FX, OZ_PER_LOT = 100_000.0, 33.77, 100.0
LOT_LO, LOT_HI = 0.1, 0.5
CANDS = ([("Z0", dict(lot=x)) for x in (0.1, 0.2, 0.3, 0.4, 0.5)]
         + [("Z1", dict(tiers=t)) for t in ((.1, .2, .3), (.1, .2, .5), (.1, .3, .5), (.2, .3, .5))]
         + [("Z2", dict(tiers=t)) for t in ((.1, .2, .3), (.1, .3, .5))]
         + [("Z3", dict(r=x)) for x in (.02, .03, .04, .05)]
         + [("Z4", dict(r=x)) for x in (.02, .03, .04)])
LIMITS = dict(dd_pct=20.0, boot95_pct=30.0, worst_trade_pct=6.0, lowest=80_000.0)
SEED = 20261101


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1, default=float))


def name_of(code, p):
    return f"{code}-" + ("/".join(f"{x:g}" for x in p["tiers"]) if "tiers" in p else f"{p.get('lot', p.get('r')):g}")


# ---------------------------------------------------------------- sized joint replay (mirrors v1-r1 execution._replay)
@nb.njit(cache=True)
def size_of(mode, eq, lot_fixed, tiers, r_base, mult, tl, tt, tusd, stop_theta, fx):
    if mode == 0:
        lot = lot_fixed
    elif mode == 1:
        lot = tiers[tl]
    elif mode == 2:
        lot = tiers[tt]
    else:
        loss_per_lot = stop_theta * tusd * 100. * fx
        rr = r_base * (mult[tl] if mode == 4 else 1.)
        lot = math.floor(rr * eq / loss_per_lot * 100. + 1e-9) / 100.
    return lot


@nb.njit(cache=True)
def replay2(mins, mid, half, ev0, ev1, blocked_a, deadlines, stop_theta, fx, commission, slip, start,
            mode, lot_fixed, tiers, r_base, mult, lot_lo, lot_hi, tl0, tl1, tt0, tt1, tu0, tu1):
    n = len(mins)
    out = np.empty((len(ev0) + len(ev1) + 2, 19))
    eqp = np.empty(n)
    cash = np.zeros(2)
    side = np.zeros(2)
    entry_i = np.full(2, -1)
    signal_i = np.full(2, -1)
    entry_fill = np.zeros(2)
    entry_half = np.zeros(2)
    theta = np.zeros(2)
    lot = np.zeros(2)
    eq_entry = np.zeros(2)
    pend = np.full(2, -1)
    pend_side = np.zeros(2)
    pend_theta = np.zeros(2)
    pend_lot = np.zeros(2)
    pend_ev = np.zeros(2, np.int64)
    pend_exit = np.zeros(2, np.int64)
    exit_req = np.full(2, -1)
    jj = np.zeros(2, np.int64)
    unreal = np.zeros(2)
    k = 0
    eq_prev = start
    for i in range(n):
        now = mins[i]
        gap = i > 0 and now - mins[i - 1] > 30
        blocked = blocked_a[i]
        newp = np.zeros(2, np.bool_)
        for rr in range(2):
            ev = ev0 if rr == 0 else ev1
            crossed = side[rr] != 0 and now >= deadlines[entry_i[rr]]
            scheduled = blocked or crossed
            force = 4 if scheduled else (3 if gap else 0)
            reason = force if (side[rr] != 0 and force != 0) else (pend_exit[rr] if side[rr] != 0 else 0)
            if reason != 0:
                factor = lot[rr] * 100. * fx
                fill = mid[i] - side[rr] * (half[i] + slip)
                net = (side[rr] * (fill - entry_fill[rr]) - 2 * commission) * factor
                cash[rr] += (side[rr] * (fill - entry_fill[rr]) - commission) * factor
                out[k, 0] = mins[signal_i[rr]]
                out[k, 1] = mins[entry_i[rr]]
                out[k, 2] = now
                out[k, 3] = side[rr]
                out[k, 4] = mid[entry_i[rr]]
                out[k, 5] = mid[i]
                out[k, 6] = entry_fill[rr]
                out[k, 7] = fill
                out[k, 8] = theta[rr]
                out[k, 9] = side[rr] * (mid[i] - mid[entry_i[rr]]) * factor
                out[k, 10] = (entry_half[rr] + half[i]) * factor
                out[k, 11] = 2 * slip * factor
                out[k, 12] = 2 * commission * factor
                out[k, 13] = net
                out[k, 14] = reason
                out[k, 15] = (now - exit_req[rr]) if force == 0 else 0
                out[k, 16] = rr
                out[k, 17] = lot[rr]
                out[k, 18] = eq_entry[rr]
                k += 1
                side[rr] = 0.
            pend_exit[rr] = 0
            if pend[rr] >= 0:
                if force == 0 and now == mins[pend[rr]] + 1 and side[rr] == 0:
                    side[rr] = pend_side[rr]
                    signal_i[rr] = pend[rr]
                    entry_i[rr] = i
                    theta[rr] = pend_theta[rr]
                    lot[rr] = pend_lot[rr]
                    eq_entry[rr] = eq_prev
                    entry_half[rr] = half[i]
                    entry_fill[rr] = mid[i] + side[rr] * (entry_half[rr] + slip)
                    cash[rr] -= commission * lot[rr] * 100. * fx
                pend[rr] = -1
            j = jj[rr]
            if j < len(ev) and int(ev[j, 0]) == i:
                if side[rr] != 0:
                    pend_exit[rr] = 1
                    exit_req[rr] = now
                if ev[j, 3] != 0 and not scheduled:
                    pend[rr] = i
                    pend_side[rr] = -ev[j, 1]
                    pend_theta[rr] = ev[j, 2]
                    pend_ev[rr] = j
                    newp[rr] = True
                jj[rr] = j + 1
            if side[rr] != 0 and i > entry_i[rr] and side[rr] * 1e4 * math.log(mid[i] / mid[entry_i[rr]]) <= -stop_theta * theta[rr]:
                pend_exit[rr] = 2
                exit_req[rr] = now
            if side[rr] != 0:
                liq = mid[i] - side[rr] * (half[i] + slip)
                unreal[rr] = (side[rr] * (liq - entry_fill[rr]) - commission) * lot[rr] * 100. * fx
            else:
                unreal[rr] = 0.
        eq = start + cash[0] + cash[1] + unreal[0] + unreal[1]
        eqp[i] = eq
        for rr in range(2):
            if newp[rr]:
                j = pend_ev[rr]
                if rr == 0:
                    x = size_of(mode, eq, lot_fixed, tiers, r_base, mult, tl0[j], tt0[j], tu0[j], stop_theta, fx)
                else:
                    x = size_of(mode, eq, lot_fixed, tiers, r_base, mult, tl1[j], tt1[j], tu1[j], stop_theta, fx)
                pend_lot[rr] = min(max(x, lot_lo), lot_hi)
        eq_prev = eq
    return out[:k], eqp


COLS = ["t_signal", "t_entry", "t_exit", "side", "entry_mid", "exit_mid", "entry_fill", "exit_fill", "theta_bps", "gross_mid_thb",
        "spread_cost_thb", "slippage_cost_thb", "commission_thb", "net_thb", "reason_code", "exit_delay_minutes", "rule_i", "lot", "eq_at_entry"]


# ---------------------------------------------------------------- inputs
def lock2_info():
    return v3.lock2_info()


def context(years, phase):
    if max(years) <= 2019:
        c = d.load(years, phase)
    else:
        c = d.context(*r2.r1ext.load_prices(years, allow_2020_2022=True))
    return r2.add_session(c)


def streams(c, l2, rules=None, ov=None):
    rules = rules or l2["base"]["rules"]
    ov = l2["ov"] if ov is None else ov
    out = {}
    for r in ("A", "B"):
        ev, aux = v3.build_rule3(c, rules[r], ov.get(r, {}))
        leg = aux["leg"]
        tl = np.where(np.isfinite(leg), np.where(leg < 3.5, 0, np.where(leg < 5, 1, 2)), 0).astype(np.int64)
        m = c["mins"][ev[:, 0].astype(np.int64)]
        el = ev[:, 3] > 0
        tu = aux["tusd"].astype(float)
        tt = np.zeros(len(ev), np.int64)
        em, eu = m[el], tu[el]
        a, b = np.searchsorted(em, m - 365 * 1440), np.searchsorted(em, m)
        for kk in np.flatnonzero(el & (b - a >= 60)):
            q1, q2 = np.quantile(eu[a[kk]:b[kk]], [1 / 3, 2 / 3])
            tt[kk] = 0 if tu[kk] < q1 else (1 if tu[kk] < q2 else 2)
        out[r] = dict(ev=ev, tl=tl, tt=tt, tu=tu)
    return out


def config_arrays(c, cost):
    mid = (c["bid"] + c["ask"]) / 2
    if cost == "historical":
        half, comm, slip = (c["ask"] - c["bid"]) / 2, 0., 0.
    else:
        half = np.full(len(mid), .168 / 2)
        comm, slip = (.01, .02) if cost == "cost_example" else (0., 0.)
    return mid, half, comm, slip


def run_sized(c, st, code, p, stop, cost="fixed"):
    mid, half, comm, slip = config_arrays(c, cost)
    mode = {"Z0": 0, "Z1": 1, "Z2": 2, "Z3": 3, "Z4": 4}[code]
    tiers = np.array(p.get("tiers", (0.1, 0.1, 0.1)), float)
    lo, hi = (p["lot"], p["lot"]) if code == "Z0" else (LOT_LO, LOT_HI)
    A, B = st["A"], st["B"]
    tr, eq = replay2(c["mins"], mid, half, A["ev"], B["ev"], c["calendar"].blocked, c["calendar"].deadline, stop, FX, comm, slip, START,
                     mode, float(p.get("lot", .1)), tiers, float(p.get("r", 0.)), np.array([1., 1.5, 2.]), lo, hi,
                     A["tl"], B["tl"], A["tt"], B["tt"], A["tu"], B["tu"])
    t = pd.DataFrame(tr, columns=COLS)
    t["rule"] = np.where(t.rule_i == 0, "A", "B")
    t = t.sort_values(["t_exit", "rule"], kind="stable").reset_index(drop=True)
    return t, eq


# ---------------------------------------------------------------- risk metrics
def drawdown(eq, start=START):
    peak = np.maximum.accumulate(np.r_[start, eq])[1:]
    dd = peak - eq
    return float(dd.max()), float((dd / peak).max() * 100)


@nb.njit(cache=True)
def boot_paths(rets, n_paths, block, seed):
    np.random.seed(seed)
    n = len(rets)
    dd = np.empty(n_paths)
    low = np.empty(n_paths)
    for p in range(n_paths):
        idx = np.random.randint(n)
        v, peak, mdd, mn = 1., 1., 0., 1.
        for t in range(n):
            if t > 0:
                if np.random.random() < 1. / block:
                    idx = np.random.randint(n)
                else:
                    idx = (idx + 1) % n
            v *= 1. + rets[idx]
            if v > peak:
                peak = v
            x = 1. - v / peak
            if x > mdd:
                mdd = x
            if v < mn:
                mn = v
        dd[p] = mdd
        low[p] = mn
    return dd, low


def daily_equity(c, eq):
    sd = c["calendar"].session_day
    last = np.r_[sd[1:] != sd[:-1], True]
    return np.r_[START, eq[last]]


def risk(c, t, eq, cut_recent=2014):
    dd, pct = drawdown(eq)
    e = daily_equity(c, eq)
    rets = e[1:] / e[:-1] - 1
    bdd, blow = boot_paths(rets, 2000, 5.0, SEED)
    peak = np.maximum.accumulate(e)
    under, longest = 0, 0
    for x, pk in zip(e, peak):
        under = under + 1 if x < pk else 0
        longest = max(longest, under)
    cutm = int(np.datetime64(f"{cut_recent}-01-01", "m").astype(np.int64))
    q = int(np.searchsorted(c["mins"], cutm))
    before = float(eq[q - 1]) if q else START
    tu = t.theta_bps / 1e4 * t.entry_mid
    risk_at_entry = 2.5 * tu * 100 * FX * t.lot / t.eq_at_entry * 100
    worst_pct = float((-t.net_thb / t.eq_at_entry).max() * 100) if len(t) else 0.
    m = dict(net=float(eq[-1] - START), dd=dd, dd_pct=pct, lowest=float(eq.min()), trades=int(len(t)),
             worst=float(t.net_thb.min()), worst_pct=worst_pct, recent=float(eq[-1] - before),
             boot50=float(np.percentile(bdd, 50) * 100), boot95=float(np.percentile(bdd, 95) * 100),
             boot99=float(np.percentile(bdd, 99) * 100), p_dd_gt_30=float((bdd > .30).mean()), p_low_lt_half=float((blow < .5).mean()),
             longest_underwater_days=int(longest), mean_lot=float(t.lot.mean()), share_lot_gt_01=float((t.lot > .1001).mean()),
             max_lot=float(t.lot.max()), risk_pct_mean=float(risk_at_entry.mean()), risk_pct_max=float(risk_at_entry.max()))
    m["acceptable"] = bool(m["dd_pct"] <= LIMITS["dd_pct"] and m["boot95"] <= LIMITS["boot95_pct"]
                           and m["worst_pct"] <= LIMITS["worst_trade_pct"] and m["lowest"] >= LIMITS["lowest"])
    return m


def yearly(c, t, eq, years):
    rows, prev = {}, START
    for y in years:
        lo = int(np.datetime64(f"{y}-01-01", "m").astype(np.int64))
        hi = int(np.datetime64(f"{y + 1}-01-01", "m").astype(np.int64))
        sel = (c["mins"] >= lo) & (c["mins"] < hi)
        e = eq[sel]
        tt = t[(t.t_exit >= lo) & (t.t_exit < hi)]
        end = float(e[-1]) if len(e) else prev
        pk = np.maximum.accumulate(np.r_[prev, e])[1:]
        rows[y] = dict(net=end - prev, end=end, dd=float((pk - e).max()) if len(e) else 0., trades=int(len(tt)),
                       wins=float(tt.net_thb[tt.net_thb > 0].sum()), losses=float(tt.net_thb[tt.net_thb <= 0].sum()),
                       mean_lot=float(tt.lot.mean()) if len(tt) else None)
        prev = end
    return rows


@nb.njit(cache=True)
def boot_capital(dp, n_paths, block, seed, x):
    np.random.seed(seed)
    n = len(dp)
    out = np.empty(n_paths)
    for q in range(n_paths):
        idx = np.random.randint(n)
        p, mx, need = 0., 0., 0.
        for t in range(n):
            if t > 0:
                if np.random.random() < 1. / block:
                    idx = np.random.randint(n)
                else:
                    idx = (idx + 1) % n
            p += dp[idx]
            if p > mx:
                mx = p
            v = (mx - p) / x - mx
            if v > need:
                need = v
        out[q] = need
    return out


def capital_needed(c, eq01, lot):
    """Smallest start capital (THB, rounded up to 1,000) for a FIXED lot (no compounding) with minute max DD <= 20%
    and bootstrap-95 daily max DD <= 30%. Exact: DD%(C) <= x  <=>  C >= max_t[(M_t - p_t)/x - M_t] (Amendment A)."""
    scale = lot / .1
    p = np.r_[0., eq01 - START] * scale
    mx = np.maximum.accumulate(p)
    need_hist = float(((mx - p) / .20 - mx).max())
    dp = np.diff(daily_equity(c, eq01)) * scale
    need_boot = float(np.percentile(boot_capital(dp, 2000, 5.0, SEED, .30), 95))
    up = lambda v: int(math.ceil(v / 1000.) * 1000)
    return dict(lot=lot, capital_hist_dd20=up(need_hist), capital_boot95_dd30=up(need_boot), capital_needed=up(max(need_hist, need_boot)))


# ---------------------------------------------------------------- phases
def check(c, l2):
    st = streams(c, l2)
    t, eq = run_sized(c, st, "Z0", dict(lot=.1), l2["base"]["stop_theta"])
    ref, _ = v3.run(c, {}, l2)
    rt = ref.trades.reset_index(drop=True)
    for col in ("t_signal", "t_entry", "t_exit", "side", "entry_fill", "exit_fill", "net_thb", "reason_code"):
        np.testing.assert_allclose(t[col].to_numpy(float), rt[col].to_numpy(float), rtol=0, atol=1e-6, err_msg=col)
    np.testing.assert_allclose(eq, ref.equity.equity.to_numpy(), rtol=0, atol=1e-6)
    m = risk(c, t, eq)
    assert abs(m["net"] - l2["training"]["net"]) < 1e-6 and abs(m["dd"] - l2["training"]["dd"]) < 1e-6
    print("CHECK PASS: sized replay at 0.1 lot == v1-r2 engine (trades and minute equity)", json.dumps({k: m[k] for k in ("net", "dd", "trades")}),
          flush=True)
    return st, t, eq, m


def sensitivity(c, l2):
    base = l2["base"]
    rows = {}

    def shifted(rule, key, delta):
        rules = {r: dict(v) for r, v in base["rules"].items()}
        ov = {r: {s: dict(o) for s, o in l2["ov"].get(r, {}).items()} for r in ("A", "B")}
        rules[rule][key] = rules[rule][key] + delta
        for s in ov[rule]:
            ov[rule][s][key] = ov[rule][s][key] + delta
        return rules, ov

    for label, rule, key, delta in (("A k -0.1", "A", "k", -.1), ("A k +0.1", "A", "k", .1), ("B k -0.25", "B", "k", -.25),
                                    ("B k +0.25", "B", "k", .25), ("A leg -0.5", "A", "leg", -.5), ("A leg +0.5", "A", "leg", .5),
                                    ("B leg -0.5", "B", "leg", -.5), ("B leg +0.5", "B", "leg", .5)):
        rules, ov = shifted(rule, key, delta)
        res = r2.run(c, rules, ov, base["stop_theta"])
        m = d.metrics(res)
        rows[label] = dict(net=m["net"], dd=m["dd"], trades=m["trades"])
    for stop in (2.25, 2.75):
        res = r2.run(c, base["rules"], l2["ov"], stop)
        m = d.metrics(res)
        rows[f"stop {stop}"] = dict(net=m["net"], dd=m["dd"], trades=m["trades"])
    return rows


def design():
    if (OUT / "LOCK.json").exists():
        raise FileExistsError("v1-r4 already locked")
    l2 = lock2_info()
    c = context(list(range(2010, 2017)), "design")
    st, t01, eq01, m01 = check(c, l2)
    table = []
    for code, p in CANDS:
        t, eq = run_sized(c, st, code, p, l2["base"]["stop_theta"])
        assert np.array_equal(t.t_entry.to_numpy(), t01.t_entry.to_numpy()), "sizing changed trade timing"
        m = risk(c, t, eq)
        table.append(dict(name=name_of(code, p), code=code, params=p, metrics=m))
        print("cand", name_of(code, p), "net", round(m["net"]), "dd", round(m["dd"]), f"({m['dd_pct']:.1f}%)", "boot95", round(m["boot95"], 1),
              "worst%", round(m["worst_pct"], 1), "low", round(m["lowest"]), "meanlot", round(m["mean_lot"], 3),
              "OK" if m["acceptable"] else "", flush=True)
    write_json(OUT / "CANDIDATES_2010_2016.json", table)
    order = {"Z0": 0, "Z1": 1, "Z2": 2, "Z3": 3, "Z4": 4}
    ok = [x for x in table if x["metrics"]["acceptable"]]
    pick = sorted(ok, key=lambda x: (-x["metrics"]["net"], order[x["code"]]))[0] if ok else None
    sens = sensitivity(c, l2)
    write_json(OUT / "SENSITIVITY_2010_2016.json", dict(base=dict(net=m01["net"], dd=m01["dd"], trades=m01["trades"]), shifted=sens))
    caps = [capital_needed(c, eq01, lot) for lot in (.1, .2, .3, .4, .5)]
    write_json(OUT / "CAPITAL_2010_2016.json", caps)
    out = dict(version=VERSION, locked_utc=datetime.now(timezone.utc).isoformat(), status="SELECTED" if pick else "NOT_CONFIRMED",
               pick=pick, base_v1r2_01=m01, limits=LIMITS, candidates=len(table), acceptable=[x["name"] for x in ok],
               base_lock_sha256=l2["sha"], code_sha256=sha(Path(__file__)), plan_sha256=sha(ROOT / "PLAN.md"), training_years=[2010, 2016],
               note="design 2010-2016 only; 2017+ not read before this lock")
    write_json(OUT / "LOCK.json", out)
    (OUT / "LOCK.sha256").write_text(sha(OUT / "LOCK.json"))
    print("LOCK", out["status"], pick["name"] if pick else "-", "acceptable:", out["acceptable"], flush=True)


def read_lock():
    lock = json.loads((OUT / "LOCK.json").read_text())
    if sha(OUT / "LOCK.json") != (OUT / "LOCK.sha256").read_text().strip():
        raise ValueError("v1-r4 LOCK changed")
    return lock


def evaluate():
    if (OUT / "EVALUATION.json").exists():
        raise FileExistsError("already evaluated")
    lock, l2 = read_lock(), lock2_info()
    if lock["status"] != "SELECTED":
        raise SystemExit("nothing selected")
    pk = lock["pick"]
    res = {}
    for period, years in (("validation", [2017, 2018, 2019]), ("full", list(range(2010, 2020)))):
        c = context(years, "evaluate")
        st = streams(c, l2)
        res[period] = {}
        for cost in ("fixed", "cost_example", "historical"):
            tb, eb = run_sized(c, st, "Z0", dict(lot=.1), l2["base"]["stop_theta"], cost)
            tp, ep = run_sized(c, st, pk["code"], pk["params"], l2["base"]["stop_theta"], cost)
            mb, mp = risk(c, tb, eb, 2018 if period == "validation" else 2014), risk(c, tp, ep, 2018 if period == "validation" else 2014)
            res[period][cost] = {"v1-r2@0.1": mb, "v1-r4": mp}
            if cost == "fixed":
                res[period]["yearly"] = {"v1-r2@0.1": yearly(c, tb, eb, years), "v1-r4": yearly(c, tp, ep, years)}
                tp.to_csv(OUT / f"TRADES_{period}_fixed.private.csv", index=False)
                if period == "full":
                    res["capital_2010_2019"] = [capital_needed(c, eb, lot) for lot in (.1, .2, .3, .4, .5)]
            print(period, cost, "v1-r2@0.1", round(mb["net"]), round(mb["dd"]), f"{mb['dd_pct']:.1f}%", "| v1-r4", round(mp["net"]),
                  round(mp["dd"]), f"{mp['dd_pct']:.1f}%", "boot95", round(mp["boot95"], 1), "OK" if mp["acceptable"] else "", flush=True)
    v = res["validation"]["fixed"]
    b, p = v["v1-r2@0.1"], v["v1-r4"]
    passed = bool(p["acceptable"] and p["net"] > b["net"] and p["net"] / max(p["dd"], 1) >= b["net"] / max(b["dd"], 1) * (1 - 1e-9))
    doc = dict(version=VERSION, lock_sha256=sha(OUT / "LOCK.json"), pick=pk["name"], results=res, passed=passed,
               status="PASS" if passed else "NOT_CONFIRMED", finished_utc=datetime.now(timezone.utc).isoformat())
    write_json(OUT / "EVALUATION.json", doc)
    print("VERDICT", doc["status"], flush=True)


def extend():
    lock, l2 = read_lock(), lock2_info()
    years = list(range(2010, 2023))
    c = context(years, "extend")
    st = streams(c, l2)
    out = {"candidates": {}}
    t01, eq01 = run_sized(c, st, "Z0", dict(lot=.1), l2["base"]["stop_theta"])
    for code, p in CANDS:
        t, eq = run_sized(c, st, code, p, l2["base"]["stop_theta"])
        m = risk(c, t, eq, 2020)
        out["candidates"][name_of(code, p)] = m
        if lock.get("pick") and name_of(code, p) == lock["pick"]["name"]:
            out["pick_yearly"] = yearly(c, t, eq, years)
            out["pick_by_rule"] = {k: dict(trades=int(len(g)), net=float(g.net_thb.sum()), mean_lot=float(g.lot.mean())) for k, g in t.groupby("rule")}
            t.to_csv(OUT / "TRADES_2010_2022_pick.private.csv", index=False)
        print("2010-22", name_of(code, p), round(m["net"]), round(m["dd"]), f"{m['dd_pct']:.1f}%", "boot95", round(m["boot95"], 1),
              "low", round(m["lowest"]), "OK" if m["acceptable"] else "", flush=True)
    out["v1r2_01_yearly"] = yearly(c, t01, eq01, years)
    out["capital_2010_2022"] = [capital_needed(c, eq01, lot) for lot in (.1, .2, .3, .4, .5)]
    write_json(OUT / "EXTEND_2010_2022.json", out)
    print("capital 2010-22:", json.dumps(out["capital_2010_2022"]), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=["check", "design", "evaluate", "extend"])
    a = ap.parse_args()
    if a.phase == "check":
        l2 = lock2_info()
        check(context(list(range(2010, 2017)), "design"), l2)
    else:
        {"design": design, "evaluate": evaluate, "extend": extend}[a.phase]()
