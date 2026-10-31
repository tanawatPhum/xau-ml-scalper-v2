"""v1-r2: per-session formulas for rules A and B on top of v1-r1 (D058). See PLAN.md.
Phases:  check | design | evaluate | extend      (python -B v1-r2/v1_r2.py <phase>)
v1-r1 code, calendar and lock are imported read-only. No live orders."""
import argparse
import hashlib
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
R1 = ROOT.parent / "v1-r1"
sys.path.insert(0, str(R1 / "daily"))
sys.path.insert(0, str(R1))
import run_study as d  # noqa: E402  (v1-r1 daily study: context, metrics, engine, calendar)
import strategy as r1strategy  # noqa: E402
import extend_2022 as r1ext  # noqa: E402

OUT = ROOT / "out"
VERSION = "v1-r2"
SESSIONS = {0: "Asia 18-03 NY", 1: "London 03-08 NY", 2: "NY morning 08-12", 3: "NY afternoon 12-18"}
GRID = {"A": dict(k=(0.75, 1.0, 1.25, 1.5), min_usd=(2.1626934441569983, 3.0, 4.0), leg=(2.5, 3.5)),
        "B": dict(k=(1.5, 2.0, 2.5), min_usd=(2.1626934441569983, 3.0, 4.0), leg=(2.5, 3.5))}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r1_lock():
    lock = d.study.read_lock(d.OUT / "LOCK.json")
    d.study.verify_hashes(lock["source_hashes"])
    if d.study.sha(d.OUT / "CALENDAR.json") != lock["calendar_hash"]:
        raise ValueError("v1-r1 calendar changed")
    return lock


def add_session(c):
    ny = pd.to_datetime(c["mins"] * 60, unit="s", utc=True).tz_convert("America/New_York")
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    c["session"] = np.where((mod >= 18 * 60) | (mod < 3 * 60), 0, np.where(mod < 8 * 60, 1, np.where(mod < 12 * 60, 2, 3))).astype(np.int64)
    return c


@nb.njit(cache=True)
def swings_x(mins, y, threshold):
    """Exact copy of the engine's _swings state machine; returns events [i, dir, theta, prev_ok], leg/theta, theta$."""
    n = len(y)
    events = np.empty((n, 4))
    legs = np.empty(n)
    tusd = np.empty(n)
    count = 0
    mode = 0
    hi = lo = 0.
    hi_i = lo_i = 0
    previous = np.nan
    for i in range(n):
        if i == 0 or mins[i] - mins[i - 1] > 30:
            hi = lo = y[i]
            hi_i = lo_i = i
            mode = 0
            previous = np.nan
            continue
        v, t = y[i], threshold[i]
        live = np.isfinite(t) and t > 0
        direction = 0
        extreme = 0.
        if mode == 0:
            if v > hi:
                hi, hi_i = v, i
            if v < lo:
                lo, lo_i = v, i
            if live and v - lo >= t and lo_i < i:
                direction, extreme = 1, lo
            elif live and hi - v >= t and hi_i < i:
                direction, extreme = -1, hi
        elif mode == 1:
            if v > hi:
                hi, hi_i = v, i
            elif live and hi - v >= t:
                direction, extreme = -1, hi
        else:
            if v < lo:
                lo, lo_i = v, i
            elif live and v - lo >= t:
                direction, extreme = 1, lo
        if direction:
            legs[count] = direction * (previous - extreme) / t
            tusd[count] = t * math.exp(v / 1e4) / 1e4
            events[count, 0] = i
            events[count, 1] = direction
            events[count, 2] = t
            events[count, 3] = np.isfinite(previous)
            count += 1
            previous = extreme
            mode = direction
            if direction == 1:
                hi, hi_i = v, i
            else:
                lo, lo_i = v, i
    return events[:count], legs[:count], tusd[:count]


def policy_mask(c, idx, policy):
    if policy == "all":
        return np.ones(len(idx), bool)
    if policy == "skip_late":
        return ((c["mins"][idx] % 1440) // 60) < 21
    if policy == "vol_le15":
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = c["s60"][idx] / c["sl"][idx]
        return np.isfinite(ratio) & (ratio <= 1.5)
    raise ValueError(f"policy {policy} not supported in v1-r2")


def build_rule(c, p, ov):
    """p = v1-r1 rule params; ov = {session: dict(k, min_usd, leg, on)} overrides."""
    vol = c["eff"] if p["long_vol"] else c["s60"]
    kvec = np.full(len(vol), float(p["k"]))
    for s, o in ov.items():
        kvec[c["session"] == int(s)] = o["k"]
    ev, leg, tusd = swings_x(c["mins"], c["y"], kvec * vol)
    ev = ev.copy()
    idx = ev[:, 0].astype(np.int64)
    ss = c["session"][idx]
    mu = np.full(len(idx), float(p["min_usd"]))
    lg = np.full(len(idx), float(p["leg"]))
    on = np.ones(len(idx), bool)
    for s, o in ov.items():
        m = ss == int(s)
        mu[m], lg[m], on[m] = o["min_usd"], o["leg"], o["on"]
    elig = (ev[:, 3] > 0) & (leg >= lg) & (tusd >= mu) & on & policy_mask(c, idx, p["policy"])
    ev[:, 3] = elig.astype(float)
    return ev


def run(c, base_rules, overrides, stop, config=None):
    sig = {r: build_rule(c, base_rules[r], overrides.get(r, {})) for r in ("A", "B")}
    return d.engine.simulate(c["mins"], c["bid"], c["ask"], sig, config or d.engine.Config(), stop_theta=stop, calendar=c["calendar"])


def good(m):
    return m["market_close_crossings"] == 0 and m["session_crossings"] == 0


def ratio(m):
    return m["net"] / max(m["dd"], 1.0)


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1, default=float))


def check(c, lock):
    base = lock["selected"]
    for r in ("A", "B"):
        mine = build_rule(c, base["rules"][r], {})
        ref = r1strategy.signals_for(c, base["rules"][r])
        np.testing.assert_array_equal(mine, ref)
    m = d.metrics(run(c, base["rules"], {}, base["stop_theta"]))
    for k in ("net", "dd", "trades", "loss"):
        assert abs(m[k] - base["metrics"][k]) < 1e-6, (k, m[k], base["metrics"][k])
    print("CHECK PASS: signals identical to v1-r1 and 2010-16 metrics reproduced", json.dumps({k: m[k] for k in ("net", "dd", "trades")}), flush=True)
    return m


def design():
    if (OUT / "LOCK.json").exists():
        raise FileExistsError("v1-r2 already locked; no retuning")
    lock = r1_lock()
    base = lock["selected"]
    c = add_session(d.load(list(range(2010, 2017)), "design"))
    bm = check(c, lock)
    stage1, picks = [], {}
    for r in ("A", "B"):
        g = GRID[r]
        cells = [dict(k=k, min_usd=u, leg=lg, on=True) for k, u, lg in itertools.product(g["k"], g["min_usd"], g["leg"])]
        cells.append(dict(k=float(base["rules"][r]["k"]), min_usd=float(base["rules"][r]["min_usd"]), leg=float(base["rules"][r]["leg"]), on=False))
        for s in SESSIONS:
            best = None
            for cell in cells:
                m = d.metrics(run(c, base["rules"], {r: {s: cell}}, base["stop_theta"]))
                row = dict(rule=r, session=s, cell=cell, metrics=m)
                stage1.append(row)
                if good(m) and m["net"] >= bm["net"] and m["dd"] <= bm["dd"] and ratio(m) > ratio(bm):
                    if best is None or ratio(m) > ratio(best["metrics"]):
                        best = row
            if best is not None:
                picks[(r, s)] = best
            print("stage1", r, SESSIONS[s], "pick" if best else "keep base",
                  json.dumps(best["cell"]) if best else "", round(ratio(best["metrics"]), 3) if best else "", flush=True)
        write_json(OUT / "STAGE1_2010_2016.json", stage1)

    def accept(m):
        return (m["net"] > bm["net"] and m["dd"] < bm["dd"] and m["recent"] >= bm["recent"] and m["lowest"] > 0
                and m["trades"] >= 500 and good(m))

    def ov_of(keys):
        ov = {"A": {}, "B": {}}
        for (r, s) in keys:
            ov[r][s] = picks[(r, s)]["cell"]
        return ov

    combo = list(picks)
    mc = d.metrics(run(c, base["rules"], ov_of(combo), base["stop_theta"])) if combo else bm
    path = [dict(step="all picks", keys=[f"{r}{s}" for r, s in combo], metrics=mc)]
    chosen = combo if (combo and accept(mc)) else None
    if chosen is None and combo:
        order = sorted(combo, key=lambda k: -ratio(picks[k]["metrics"]))
        cur, cm = [], bm
        for k in order:
            m = d.metrics(run(c, base["rules"], ov_of(cur + [k]), base["stop_theta"]))
            keep = good(m) and m["net"] >= bm["net"] and m["dd"] <= bm["dd"] and ratio(m) > ratio(cm)
            path.append(dict(step=f"greedy add {k[0]}{k[1]}", kept=keep, metrics=m))
            if keep:
                cur, cm = cur + [k], m
        if cur and accept(cm):
            chosen, mc = cur, cm
    status = "SELECTED" if chosen else "NOT_CONFIRMED"
    sel = ov_of(chosen) if chosen else {"A": {}, "B": {}}
    final = mc if chosen else bm
    out = dict(version=VERSION, locked_utc=datetime.now(timezone.utc).isoformat(), status=status, base_version="v1-r1", base_id=base["id"],
               base_rules=base["rules"], stop_theta=base["stop_theta"], overrides={r: {str(s): v for s, v in sel[r].items()} for r in sel},
               sessions=SESSIONS, training_metrics=final, base_training_metrics=bm, stage2_path=path,
               r1_lock_sha256=d.study.sha(d.OUT / "LOCK.json"), code_sha256=sha(Path(__file__)), plan_sha256=sha(ROOT / "PLAN.md"),
               training_years=[2010, 2016], note="design 2010-2016 only; 2017-2019 not read before this lock")
    write_json(OUT / "LOCK.json", out)
    (OUT / "LOCK.sha256").write_text(sha(OUT / "LOCK.json"))
    print("LOCK", status, json.dumps(out["overrides"]), json.dumps({k: final[k] for k in ("net", "dd", "trades", "recent", "loss")}), flush=True)


def read_lock():
    lock = json.loads((OUT / "LOCK.json").read_text())
    if sha(OUT / "LOCK.json") != (OUT / "LOCK.sha256").read_text().strip():
        raise ValueError("v1-r2 LOCK changed")
    ov = {r: {int(s): v for s, v in lock["overrides"][r].items()} for r in lock["overrides"]}
    return lock, ov


def by_session(trades, c):
    ny = pd.to_datetime(trades.t_signal * 60, unit="s", utc=True).dt.tz_convert("America/New_York")
    mod = ny.dt.hour * 60 + ny.dt.minute
    s = np.where((mod >= 18 * 60) | (mod < 3 * 60), 0, np.where(mod < 8 * 60, 1, np.where(mod < 12 * 60, 2, 3)))
    t = trades.assign(session=[SESSIONS[i] for i in s])
    return {k: dict(trades=int(len(g)), win=float((g.net_thb > 0).mean()), net=float(g.net_thb.sum())) for k, g in t.groupby("session")}


def yearly(result, years, start=100_000.0):
    rows, prev = {}, start
    eq = result.equity
    for y in years:
        lo = int(np.datetime64(f"{y}-01-01", "m").astype(np.int64))
        hi = int(np.datetime64(f"{y + 1}-01-01", "m").astype(np.int64))
        e = eq.equity.to_numpy()[(eq.t_minute.to_numpy() >= lo) & (eq.t_minute.to_numpy() < hi)]
        t = result.trades[(result.trades.t_exit >= lo) & (result.trades.t_exit < hi)]
        end = float(e[-1]) if len(e) else prev
        pk = np.maximum.accumulate(np.r_[prev, e])[1:]
        rows[y] = dict(net=end - prev, end=end, dd=float((pk - e).max()) if len(e) else 0.0, trades=int(len(t)),
                       wins=float(t.net_thb[t.net_thb > 0].sum()), losses=float(t.net_thb[t.net_thb <= 0].sum()))
        prev = end
    return rows


def evaluate():
    if (OUT / "EVALUATION.json").exists():
        raise FileExistsError("already evaluated")
    lock, ov = read_lock()
    r1 = r1_lock()
    base = r1["selected"]
    r1eval = json.loads((d.OUT / "EVALUATION.json").read_text())["results"]
    scen = {"fixed": d.engine.Config(), "cost_example": d.engine.Config(commission=.01, slippage=.02),
            "historical": d.engine.Config(cost_mode="historical")}
    res = {}
    for period, years in (("full", list(range(2010, 2020))), ("validation", [2017, 2018, 2019])):
        c = add_session(d.load(years, "evaluate"))
        res[period] = {}
        for sc, cfg in scen.items():
            a = run(c, base["rules"], {}, base["stop_theta"], cfg)
            b = run(c, base["rules"], ov, base["stop_theta"], cfg)
            ma, mb = d.metrics(a), d.metrics(b)
            ref = r1eval[period][sc]["rx"]
            assert abs(ma["net"] - ref["net"]) < 1e-6 and abs(ma["dd"] - ref["dd"]) < 1e-6, ("v1-r1 reproduction", period, sc)
            res[period][sc] = {"v1-r1": ma, "v1-r2": mb}
            if sc == "fixed":
                res[period]["sessions"] = {"v1-r1": by_session(a.trades, c), "v1-r2": by_session(b.trades, c)}
                res[period]["yearly"] = {"v1-r1": yearly(a, years), "v1-r2": yearly(b, years)}
                b.trades.to_csv(OUT / f"TRADES_{period}_fixed.private.csv", index=False)
            print(period, sc, "v1-r1", json.dumps({k: round(ma[k]) for k in ("net", "dd", "trades")}),
                  "| v1-r2", json.dumps({k: round(mb[k]) for k in ("net", "dd", "trades")}), flush=True)
    v = res["validation"]["fixed"]
    passed = bool(lock["status"] == "SELECTED" and v["v1-r2"]["net"] > v["v1-r1"]["net"] and v["v1-r2"]["dd"] <= v["v1-r1"]["dd"] and good(v["v1-r2"]))
    doc = dict(version=VERSION, lock_sha256=sha(OUT / "LOCK.json"), results=res, passed=passed,
               status=("PASS" if passed else "NOT_CONFIRMED"), finished_utc=datetime.now(timezone.utc).isoformat())
    write_json(OUT / "EVALUATION.json", doc)
    print("VERDICT", doc["status"], flush=True)


def extend():
    lock, ov = read_lock()
    base = r1_lock()["selected"]
    years = list(range(2010, 2023))
    c = add_session(d.context(*r1ext.load_prices(years, allow_2020_2022=True)))
    out = {}
    for name, o in (("v1-r1", {}), ("v1-r2", ov)):
        r = run(c, base["rules"], o, base["stop_theta"])
        m = d.metrics(r)
        out[name] = dict(metrics=m, yearly=yearly(r, years), sessions=by_session(r.trades, c),
                         by_rule={k: dict(trades=int(len(g)), net=float(g.net_thb.sum())) for k, g in r.trades.groupby("rule")})
        r.trades.to_csv(OUT / f"TRADES_2010_2022_{name}.private.csv", index=False)
        print(name, json.dumps({k: round(m[k]) for k in ("net", "dd", "trades", "lowest")}), flush=True)
    write_json(OUT / "EXTEND_2010_2022.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=["check", "design", "evaluate", "extend"])
    a = ap.parse_args()
    if a.phase == "check":
        check(add_session(d.load(list(range(2010, 2017)), "design")), r1_lock())
    else:
        {"design": design, "evaluate": evaluate, "extend": extend}[a.phase]()
