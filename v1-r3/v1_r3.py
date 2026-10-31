"""v1-r3: literature-driven filters on top of v1-r2 (see PLAN.md).
Phases:  check | design | evaluate | extend      (python -B v1-r3/v1_r3.py <phase>)
v1-r1 / v1-r2 code, calendar and locks are imported read-only. No live orders. 2023+ is never read."""
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
sys.path.insert(0, str(ROOT.parent / "v1-r2"))
import v1_r2 as r2  # noqa: E402  (also puts v1-r1 modules on sys.path)

d = r2.d
EXT = ROOT.parent / "data-ext"
OUT = ROOT / "out"
VERSION = "v1-r3"
NY = "America/New_York"
FAMILIES = {"F1": [15, 30, 60], "F2": ["settle", "glds"], "F3": ["leg_high", "leg_low", "pb_high", "pb_low"],
            "F3n": ["jump_norel", "jump_rel"], "F4": ["seas", "seas_bp"], "F5": [2.0, 3.0],
            "F6": ["leg_release", "pb_release", "window"], "F7": ["low", "high"], "F8": [15, 60], "F9": ["reject"]}  # PLAN amendment A
NULL_DRAWS, NULL_SEED = 20, 20261101


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1, default=float))


# ---------------------------------------------------------------- zigzag with pivots
@nb.njit(cache=True)
def swings_p(mins, y, threshold):
    """Same state machine as v1-r2 swings_x (= engine _swings) plus pivot indices of each leg."""
    n = len(y)
    events = np.empty((n, 4))
    legs = np.empty(n)
    tusd = np.empty(n)
    piv = np.empty(n, np.int64)
    ppiv = np.empty(n, np.int64)
    count = 0
    mode = 0
    hi = lo = 0.
    hi_i = lo_i = 0
    previous = np.nan
    prev_i = -1
    for i in range(n):
        if i == 0 or mins[i] - mins[i - 1] > 30:
            hi = lo = y[i]
            hi_i = lo_i = i
            mode = 0
            previous = np.nan
            prev_i = -1
            continue
        v, t = y[i], threshold[i]
        live = np.isfinite(t) and t > 0
        direction = 0
        extreme = 0.
        ext_i = -1
        if mode == 0:
            if v > hi:
                hi, hi_i = v, i
            if v < lo:
                lo, lo_i = v, i
            if live and v - lo >= t and lo_i < i:
                direction, extreme, ext_i = 1, lo, lo_i
            elif live and hi - v >= t and hi_i < i:
                direction, extreme, ext_i = -1, hi, hi_i
        elif mode == 1:
            if v > hi:
                hi, hi_i = v, i
            elif live and hi - v >= t:
                direction, extreme, ext_i = -1, hi, hi_i
        else:
            if v < lo:
                lo, lo_i = v, i
            elif live and v - lo >= t:
                direction, extreme, ext_i = 1, lo, lo_i
        if direction:
            legs[count] = direction * (previous - extreme) / t
            tusd[count] = t * math.exp(v / 1e4) / 1e4
            events[count, 0] = i
            events[count, 1] = direction
            events[count, 2] = t
            events[count, 3] = np.isfinite(previous)
            piv[count] = ext_i
            ppiv[count] = prev_i
            count += 1
            previous = extreme
            prev_i = ext_i
            mode = direction
            if direction == 1:
                hi, hi_i = v, i
            else:
                lo, lo_i = v, i
    return events[:count], legs[:count], tusd[:count], piv[:count], ppiv[:count]


@nb.njit(cache=True)
def seg_j(mins, y, a_idx, b_idx):
    """J = max r^2 / sum r^2 and n (adjacent returns) over index ranges (a, b]."""
    n = len(a_idx)
    out = np.full(n, np.nan)
    cnt = np.zeros(n, np.int64)
    for k in range(n):
        a, b = a_idx[k], b_idx[k]
        if a < 0 or b <= a:
            continue
        mx = 0.
        sm = 0.
        m = 0
        for j in range(a + 1, b + 1):
            if mins[j] - mins[j - 1] == 1:
                q = (y[j] - y[j - 1]) ** 2
                sm += q
                m += 1
                if q > mx:
                    mx = q
        cnt[k] = m
        if sm > 0:
            out[k] = mx / sm
    return out, cnt


def matched_cuts(m, J, n, el):
    """Duration-matched trailing-180-day 0.8 / 0.2 quantiles over eligible events (PLAN amendment A)."""
    hi, lo = np.full(len(J), np.nan), np.full(len(J), np.nan)
    em, ej, en = m[el], J[el], n[el]
    a = np.searchsorted(em, m - 180 * 1440)
    b = np.searchsorted(em, m)
    for k in np.flatnonzero(el & np.isfinite(J)):
        wj, wn = ej[a[k]:b[k]], en[a[k]:b[k]]
        sel = np.isfinite(wj) & (wn >= n[k] / 1.5) & (wn <= n[k] * 1.5)
        if sel.sum() >= 30:
            hi[k], lo[k] = np.quantile(wj[sel], .8), np.quantile(wj[sel], .2)
    return hi, lo


# ---------------------------------------------------------------- features
def window_stats(mins, x, adj):
    """v1-r1 60-minute window (returns lo..i-1, restart after >30-min gaps): sum of x over adjacent pairs and count."""
    n = len(x)
    cs = np.r_[0., np.cumsum(np.where(adj, x, 0.))]
    cc = np.r_[0, np.cumsum(adj)]
    first = np.maximum.accumulate(np.where(np.r_[True, np.diff(mins) > 30], np.arange(n), 0))
    i = np.arange(n)
    lo = np.minimum(np.maximum(i - 60, first + 1), i)
    return cs[i] - cs[lo], cc[i] - cc[lo]


def seasonal(c, days=60):
    mins, y = c["mins"], c["y"]
    r = np.r_[0., np.diff(y)]
    adj = np.r_[False, np.diff(mins) == 1]
    b = c["nymod"] // 15
    uday, didx = np.unique(c["calendar"].session_day, return_inverse=True)
    nd = len(uday)
    S, N = np.zeros((nd, 96)), np.zeros((nd, 96))
    np.add.at(S, (didx, b), np.where(adj, r * r, 0.))
    np.add.at(N, (didx, b), adj.astype(float))
    cS, cN = np.vstack([np.zeros((1, 96)), np.cumsum(S, 0)]), np.vstack([np.zeros((1, 96)), np.cumsum(N, 0)])
    k = np.arange(nd)
    lo = np.maximum(k - days, 0)
    sS, sN = cS[k] - cS[lo], cN[k] - cN[lo]
    with np.errstate(invalid="ignore", divide="ignore"):
        tot = sS.sum(1) / sN.sum(1)
        s2 = (sS / sN) / tot[:, None]
    full = (k - lo) >= days
    s2 = np.where(full[:, None] & np.isfinite(s2) & (sN >= 30), np.clip(s2, .05, 20.), 1.)
    s_min = np.sqrt(s2[didx, b])
    rt = r / s_min
    # check the estimator against v1-r1's s60 on raw returns
    ss, cnt = window_stats(mins, r * r, adj)
    raw = np.where((cnt >= 30) & (ss > 1e-12), np.sqrt(ss / np.maximum(cnt, 1) * 60), np.nan)
    ok = np.isfinite(raw) | np.isfinite(c["s60"])
    assert np.allclose(raw[ok], c["s60"][ok], rtol=1e-9, atol=1e-9, equal_nan=True), "s60 re-implementation mismatch"
    ss, cnt = window_stats(mins, rt * rt, adj)
    good = (cnt >= 30) & (ss > 1e-12)
    c["s60_seas"] = np.where(good, np.sqrt(ss / np.maximum(cnt, 1) * 60), np.nan) * s_min
    adj2 = adj & np.r_[False, adj[:-1]]
    bp = np.abs(rt) * np.abs(np.r_[0., rt[:-1]])
    sb, cb = window_stats(mins, bp, adj2)
    c["s60_seas_bp"] = np.where((cb >= 30) & (sb > 1e-12), np.sqrt(math.pi / 2 * sb / np.maximum(cb, 1) * 60), np.nan) * s_min
    s2m, cnt2 = window_stats(mins, s_min ** 2, adj)
    e60 = np.sqrt(tot[didx] * (s2m / np.maximum(cnt2, 1)) * 60)
    with np.errstate(invalid="ignore", divide="ignore"):
        c["u"] = np.where(full[didx] & (cnt2 >= 30), c["s60"] / e60, np.nan)
    return c


def load_events(last):
    ev = pd.read_csv(OUT / "EVENTS_2010_2022.csv")
    return np.sort(ev[ev.date <= last].utc_minute.to_numpy(np.int64))


def load_gvz(last):
    g = pd.read_csv(EXT / "macro" / "GVZ_daily_2009_2022.csv", parse_dates=["date"])
    g = g[g.date <= last].reset_index(drop=True)
    v = g.GVZ.to_numpy(float)
    pct = np.full(len(v), np.nan)
    for i in range(len(v)):
        w = v[max(0, i - 251): i + 1]
        if len(w) >= 126:
            pct[i] = (w < v[i]).mean() + .5 * (w == v[i]).mean()
    return g.date.to_numpy("datetime64[D]").astype(np.int64), pct


def load_flight(last_year):
    ms, cs = [], []
    for y in range(2012, last_year + 1):
        p = EXT / "us500" / f"US500_M1_BID_{y}.private.npz"
        if not p.exists():
            raise FileNotFoundError(p)
        z = np.load(p)
        ms.append(z["mins"])
        cs.append(z["close"])
    m, cl = np.concatenate(ms), np.concatenate(cs)
    o = np.argsort(m, kind="stable")
    m, cl = m[o], cl[o]
    j = np.minimum(np.searchsorted(m, m - 5), len(m) - 1)
    ok = m[j] == m - 5
    r5 = np.where(ok, 1e4 * np.log(cl / cl[j]), np.nan)
    tm, rv = m[np.isfinite(r5)], r5[np.isfinite(r5)]
    ny = pd.to_datetime(tm * 60, unit="s", utc=True).tz_convert(NY)
    nbin = ((ny.hour * 60 + ny.minute) // 30).to_numpy()
    day = tm // 1440
    cut = np.full(len(tm), np.nan)
    for bb in np.unique(nbin):  # clock-matched: same 30-min NY bin, prior 60 days (PLAN amendment A)
        sel = np.flatnonzero(nbin == bb)
        t_b, r_b, d_b = tm[sel], rv[sel], day[sel]
        for dd in np.unique(d_b):
            a, b = np.searchsorted(t_b, (dd - 60) * 1440), np.searchsorted(t_b, dd * 1440)
            if b - a >= 300:
                cut[sel[d_b == dd]] = np.quantile(r_b[a:b], .01)
    return np.sort(tm[rv <= cut])


def ny_half_hours(c):
    """For each minute: index of the 11:30 and 12:00 NY minutes of the same NY calendar date (-1 if absent)."""
    ny = pd.to_datetime(c["mins"] * 60, unit="s", utc=True).tz_convert(NY)
    dates = ny.normalize()
    i1130, i1200 = np.full(len(ny), -1), np.full(len(ny), -1)
    for dt in pd.unique(dates[(c["nymod"] >= 930) & (c["nymod"] < 960)]):
        m1 = int(((dt + pd.Timedelta(minutes=690)).tz_convert("UTC")).value // 60_000_000_000)
        m2 = int(((dt + pd.Timedelta(minutes=720)).tz_convert("UTC")).value // 60_000_000_000)
        j1, j2 = np.searchsorted(c["mins"], m1), np.searchsorted(c["mins"], m2)
        if j1 < len(c["mins"]) and j2 < len(c["mins"]) and c["mins"][j1] == m1 and c["mins"][j2] == m2:
            sel = np.asarray(dates == dt)
            i1130[sel], i1200[sel] = j1, j2
    return i1130, i1200


def add_features(c, last):
    c = r2.add_session(c)
    ny = pd.to_datetime(c["mins"] * 60, unit="s", utc=True).tz_convert(NY)
    c["nymod"] = (ny.hour * 60 + ny.minute).to_numpy().astype(np.int64)
    sd = c["calendar"].session_day
    start = np.r_[True, sd[1:] != sd[:-1]]
    c["open_idx"] = np.maximum.accumulate(np.where(start, np.arange(len(sd)), 0))
    c = seasonal(c)
    c["i1130"], c["i1200"] = ny_half_hours(c)
    c["events"] = load_events(last)
    c["gvz_days"], c["gvz_pct"] = load_gvz(last)
    c["flight"] = load_flight(int(last[:4])) if int(last[:4]) >= 2012 else np.empty(0, np.int64)
    c["last"] = last
    return c


# ---------------------------------------------------------------- signals
def build_rule3(c, p, ov, vol_kind="raw"):
    if vol_kind == "raw":
        vol = c["eff"] if p["long_vol"] else c["s60"]
    else:
        sx = c[f"s60_{vol_kind}"]
        vol = np.where(np.isfinite(c["sl"]), np.fmax(sx, c["sl"]), sx) if p["long_vol"] else sx
    kvec = np.full(len(vol), float(p["k"]))
    for s, o in ov.items():
        kvec[c["session"] == int(s)] = o["k"]
    ev, leg, tusd, piv, ppiv = swings_p(c["mins"], c["y"], kvec * vol)
    ev = ev.copy()
    idx = ev[:, 0].astype(np.int64)
    ss = c["session"][idx]
    mu = np.full(len(idx), float(p["min_usd"]))
    lg = np.full(len(idx), float(p["leg"]))
    on = np.ones(len(idx), bool)
    for s, o in ov.items():
        m = ss == int(s)
        mu[m], lg[m], on[m] = o["min_usd"], o["leg"], o["on"]
    elig = (ev[:, 3] > 0) & (leg >= lg) & (tusd >= mu) & on & r2.policy_mask(c, idx, p["policy"])
    ev[:, 3] = elig.astype(float)
    return ev, dict(piv=piv, ppiv=ppiv, thr=kvec * vol, leg=leg, tusd=tusd)


def any_event(E, lo, hi):
    return (np.searchsorted(E, hi, "right") - np.searchsorted(E, lo, "left")) > 0


def enrich(c, ev, aux):
    idx = ev[:, 0].astype(np.int64)
    m = c["mins"][idx]
    el = ev[:, 3] > 0
    piv, ppiv = aux["piv"], aux["ppiv"]
    Jl, nl = seg_j(c["mins"], c["y"], ppiv, piv)
    Jp, npb = seg_j(c["mins"], c["y"], piv, idx)
    lhi, llo = matched_cuts(m, Jl, nl, el)
    phi, plo = matched_cuts(m, Jp, npb, el)
    start = np.where(ppiv >= 0, c["mins"][np.maximum(ppiv, 0)], m)
    ext = c["mins"][piv]
    E = c["events"]
    aux.update(Jl=Jl, lhi=lhi, llo=llo, Jp=Jp, phi=phi, plo=plo,
               rel_leg=any_event(E, start - 5, ext), rel_pb=any_event(E, ext - 5, m), rel_win=any_event(E, m - 15, m + 5))
    return aux


def keep_mask(c, ev, aux, fam, var):
    idx = ev[:, 0].astype(np.int64)
    side = -ev[:, 1]
    m = c["mins"][idx]
    if fam == "F1":
        return (c["calendar"].deadline[idx] - m) >= var
    if fam == "F2":
        if var == "settle":
            dm = c["y"][idx] - c["y"][c["open_idx"][idx]]
            w = (c["nymod"][idx] >= 13 * 60) & (c["nymod"][idx] < 13 * 60 + 30)
            return ~(w & (side * dm < 0))
        i1, i2 = c["i1130"][idx], c["i1200"][idx]
        have = (i1 >= 0) & (i2 >= 0)
        ret = np.where(have, c["y"][np.maximum(i2, 0)] - c["y"][np.maximum(i1, 0)], np.nan)
        w = (c["nymod"][idx] >= 930) & (c["nymod"][idx] < 960) & have
        return ~(w & (side * ret <= 0))
    if fam == "F3":
        if var == "leg_high":
            return ~(aux["Jl"] > aux["lhi"])
        if var == "leg_low":
            return ~(aux["Jl"] < aux["llo"])
        if var == "pb_high":
            return ~(aux["Jp"] > aux["phi"])
        return ~(aux["Jp"] < aux["plo"])
    if fam == "F3n":
        hj = aux["Jl"] > aux["lhi"]
        return ~(hj & ~aux["rel_leg"]) if var == "jump_norel" else ~(hj & aux["rel_leg"])
    if fam == "F5":
        return ~(c["u"][idx] > var)
    if fam == "F6":
        return ~{"leg_release": aux["rel_leg"], "pb_release": aux["rel_pb"], "window": aux["rel_win"]}[var]
    if fam == "F9":
        px_ext = np.exp(c["y"][aux["piv"]] / 1e4)
        px_sig = np.exp(c["y"][idx] / 1e4)
        th = aux["tusd"]
        up = side == 1  # prior leg up: extreme is a high
        k_up = np.ceil((px_ext - .5 * th) / 10.) * 10.   # smallest $10 level >= high - 0.5 theta$
        rej_up = up & (px_ext >= k_up - .1 * th) & (px_ext <= k_up + .5 * th) & (px_sig < k_up)
        k_dn = np.floor((px_ext + .5 * th) / 10.) * 10.  # largest $10 level <= low + 0.5 theta$
        rej_dn = ~up & (px_ext <= k_dn + .1 * th) & (px_ext >= k_dn - .5 * th) & (px_sig > k_dn)
        return ~(rej_up | rej_dn)
    if fam == "F7":
        sd = c["calendar"].session_day[idx]
        k = np.searchsorted(c["gvz_days"], sd, "left") - 1
        okk = (k >= 0) & (sd - c["gvz_days"][np.maximum(k, 0)] <= 5)
        pct = np.where(okk, c["gvz_pct"][np.maximum(k, 0)], np.nan)
        return ~(pct < 1 / 3) if var == "low" else ~(pct > 2 / 3)
    if fam == "F8":
        F = c["flight"]
        fl = (np.searchsorted(F, m, "right") - np.searchsorted(F, m - var, "right")) > 0
        return ~((side == -1) & fl)
    raise ValueError(fam)


def signals(c, base_rules, ov, filt, extra_block=None):
    sig, info = {}, {}
    for r in ("A", "B"):
        fr = filt.get(r, {})
        ev, aux = build_rule3(c, base_rules[r], ov.get(r, {}), fr.get("F4", "raw"))
        el0 = ev[:, 3] > 0
        keep = np.ones(len(ev), bool)
        if any(f != "F4" for f in fr):
            aux = enrich(c, ev, aux)
            for fam, var in fr.items():
                if fam != "F4":
                    keep &= keep_mask(c, ev, aux, fam, var)
        if extra_block is not None and r in extra_block:
            keep &= ~extra_block[r]
        ev[:, 3] = (el0 & keep).astype(float)
        sig[r] = ev
        info[r] = dict(eligible=int(el0.sum()), blocked=int((el0 & ~keep).sum()), thr=aux["thr"])
    return sig, info


def run(c, filt, lock2, config=None, extra_block=None):
    base = lock2["base"]
    sig, info = signals(c, base["rules"], lock2["ov"], filt, extra_block)
    res = d.engine.simulate(c["mins"], c["bid"], c["ask"], sig, config or d.engine.Config(), stop_theta=base["stop_theta"],
                            calendar=c["calendar"])
    return res, info


# ---------------------------------------------------------------- statistics
def daily(tr):
    ex = pd.to_datetime(tr.t_exit * 60, unit="s", utc=True).dt.tz_convert(NY) + pd.Timedelta(hours=6)
    return tr.net_thb.groupby(ex.dt.date).sum()


def t_diff(base_tr, new_tr):
    a, b = daily(base_tr), daily(new_tr)
    ix = a.index.union(b.index)
    x = b.reindex(ix, fill_value=0.) - a.reindex(ix, fill_value=0.)
    sd = x.std(ddof=1)
    return float(x.mean() / (sd / np.sqrt(len(x)))) if len(x) > 1 and sd > 0 else 0.0


def ratio(m):
    return m["net"] / max(m["dd"], 1.0)


def good(m):
    return m["market_close_crossings"] == 0 and m["session_crossings"] == 0


def lock2_info():
    lock, ov = r2.read_lock()
    base = r2.r1_lock()["selected"]
    return dict(base=base, ov=ov, sha=r2.sha(r2.OUT / "LOCK.json"), training=lock["training_metrics"])


def context(years, phase, last):
    if max(years) <= 2019:
        c = d.load(years, phase)
    else:
        c = d.context(*r2.r1ext.load_prices(years, allow_2020_2022=True))
    return add_features(c, last)


# ---------------------------------------------------------------- phases
def check(c, l2):
    for r in ("A", "B"):
        mine, _ = build_rule3(c, l2["base"]["rules"][r], l2["ov"].get(r, {}))
        ref = r2.build_rule(c, l2["base"]["rules"][r], l2["ov"].get(r, {}))
        np.testing.assert_array_equal(mine, ref)
    res, _ = run(c, {}, l2)
    m = d.metrics(res)
    for k in ("net", "dd", "trades"):
        assert abs(m[k] - l2["training"][k]) < 1e-6, (k, m[k], l2["training"][k])
    print("CHECK PASS: v1-r2 signals and 2010-16 metrics reproduced", json.dumps({k: m[k] for k in ("net", "dd", "trades")}), flush=True)
    return res, m


def diagnostics(c, l2, bres):
    """Descriptive only (PLAN amendment A): overshoot audit by prior-leg bin, and GVZ x surprise cells."""
    out = {"overshoot": {}, "gvz_surprise": {}}
    bins = [0, 1.5, 2.5, 3.5, 5, np.inf]
    for r in ("A", "B"):
        ev, aux = build_rule3(c, l2["base"]["rules"][r], l2["ov"].get(r, {}))
        idx = ev[:, 0].astype(np.int64)
        ok = np.r_[np.isfinite(aux["leg"][:-1]) & (aux["ppiv"][:-1] >= 0), False]
        nxt = np.r_[aux["piv"][1:], 0]
        O = np.where(ok, ev[:, 1] * (c["y"][nxt] - c["y"][idx]) / ev[:, 2], np.nan)
        rows = {}
        for lo, hi in zip(bins[:-1], bins[1:]):
            sel = ok & (aux["leg"] >= lo) & (aux["leg"] < hi) & np.isfinite(O)
            rows[f"leg {lo}-{hi}"] = dict(n=int(sel.sum()), mean_O=float(np.nanmean(O[sel])) if sel.any() else None,
                                          p_O_lt_1=float(np.mean(O[sel] < 1)) if sel.any() else None,
                                          eligible=int((sel & (ev[:, 3] > 0)).sum()))
        out["overshoot"][r] = rows
    tr = bres.trades
    ix = np.searchsorted(c["mins"], tr.t_signal.to_numpy())
    sd = c["calendar"].session_day[ix]
    k = np.searchsorted(c["gvz_days"], sd, "left") - 1
    pct = np.where(k >= 0, c["gvz_pct"][np.maximum(k, 0)], np.nan)
    u = c["u"][ix]
    for gname, g in (("gvz_ge_median", pct >= .5), ("gvz_lt_median", pct < .5)):
        for uname, uu in (("u_ge_2", u >= 2), ("u_lt_2", u < 2)):
            t = tr[g & uu]
            out["gvz_surprise"][f"{gname}|{uname}"] = dict(trades=int(len(t)), win=float((t.net_thb > 0).mean()) if len(t) else None,
                                                          avg_net=float(t.net_thb.mean()) if len(t) else None)
    return out


def design():
    if (OUT / "LOCK.json").exists():
        raise FileExistsError("v1-r3 already locked; no retuning")
    l2 = lock2_info()
    c = context(list(range(2010, 2017)), "design", "2016-12-31")
    bres, bm = check(c, l2)
    btr = bres.trades
    write_json(OUT / "DIAGNOSTICS_2010_2016.json", diagnostics(c, l2, bres))
    stage1, picks = [], {}
    for r in ("A", "B"):
        for fam, variants in FAMILIES.items():
            best = None
            for var in variants:
                res, info = run(c, {r: {fam: var}}, l2)
                m = d.metrics(res)
                t = t_diff(btr, res.trades)
                ok = (good(m) and m["net"] >= bm["net"] and m["dd"] <= bm["dd"] and ratio(m) > ratio(bm) and t >= 1.0
                      and (fam != "F4" or t >= 1.5))
                row = dict(rule=r, family=fam, variant=var, metrics=m, t_diff=t, blocked=info[r]["blocked"],
                           eligible=info[r]["eligible"], eligible_pick=ok)
                stage1.append(row)
                print("stage1", r, fam, var, "net", round(m["net"]), "dd", round(m["dd"]), "t", round(t, 2),
                      "blocked", info[r]["blocked"], "OK" if ok else "", flush=True)
                if ok and (best is None or ratio(m) > ratio(best["metrics"])):
                    best = row
            if best is not None:
                picks[(r, fam)] = best
    write_json(OUT / "STAGE1_2010_2016.json", stage1)
    # random-block null for blocking picks
    rng = np.random.default_rng(NULL_SEED)
    sig0, _ = signals(c, l2["base"]["rules"], l2["ov"], {})
    nulls, kept = {}, {}
    for (r, fam), row in picks.items():
        if fam == "F4":
            kept[(r, fam)] = row
            nulls[f"{r}-{fam}"] = dict(note="F4 exempt (theta change); passed stage 1 with t>=1.5")
            continue
        el = np.flatnonzero(sig0[r][:, 3] > 0)
        ratios = []
        for _ in range(NULL_DRAWS):
            blk = np.zeros(len(sig0[r]), bool)
            blk[rng.choice(el, size=row["blocked"], replace=False)] = True
            res, _ = run(c, {}, l2, extra_block={r: blk})
            ratios.append(ratio(d.metrics(res)))
        beat = int(sum(ratio(row["metrics"]) > x for x in ratios))
        nulls[f"{r}-{fam}"] = dict(variant=row["variant"], pick_ratio=ratio(row["metrics"]), null_ratios=ratios, beaten=beat)
        print("null", r, fam, row["variant"], "beats", beat, "of", NULL_DRAWS, flush=True)
        if beat >= 19:
            kept[(r, fam)] = row
    write_json(OUT / "NULL_2010_2016.json", nulls)

    def filt_of(keys):
        f = {"A": {}, "B": {}}
        for (r, fam) in keys:
            f[r][fam] = kept[(r, fam)]["variant"]
        return f

    def accept(m):
        return (m["net"] > bm["net"] and m["dd"] < bm["dd"] and m["recent"] >= bm["recent"] and m["lowest"] > 0
                and m["trades"] >= 500 and good(m))

    combo = list(kept)
    path, chosen, mc = [], None, bm
    if combo:
        res, _ = run(c, filt_of(combo), l2)
        mc = d.metrics(res)
        path.append(dict(step="all kept picks", keys=[f"{r}-{f}" for r, f in combo], metrics=mc, t_diff=t_diff(btr, res.trades)))
        if accept(mc):
            chosen = combo
        else:
            cur, cm = [], bm
            for k in sorted(combo, key=lambda k: -ratio(kept[k]["metrics"])):
                res, _ = run(c, filt_of(cur + [k]), l2)
                m = d.metrics(res)
                keep = good(m) and m["net"] >= bm["net"] and m["dd"] <= bm["dd"] and ratio(m) > ratio(cm)
                path.append(dict(step=f"greedy add {k[0]}-{k[1]}", kept=keep, metrics=m))
                if keep:
                    cur, cm = cur + [k], m
            if cur and accept(cm):
                chosen, mc = cur, cm
    status = "SELECTED" if chosen else "NOT_CONFIRMED"
    filt = filt_of(chosen) if chosen else {"A": {}, "B": {}}
    final = mc if chosen else bm
    out = dict(version=VERSION, locked_utc=datetime.now(timezone.utc).isoformat(), status=status, base_version="v1-r2",
               base_lock_sha256=l2["sha"], filters=filt, training_metrics=final, base_training_metrics=bm,
               stage1_picks=[f"{r}-{f}:{v['variant']}" for (r, f), v in picks.items()],
               kept_after_null=[f"{r}-{f}:{v['variant']}" for (r, f), v in kept.items()], stage2_path=path,
               ledger_cells=sum(len(v) for v in FAMILIES.values()) * 2, code_sha256=sha(Path(__file__)),
               plan_sha256=sha(ROOT / "PLAN.md"), events_sha256=sha(OUT / "EVENTS_2010_2022.csv"), training_years=[2010, 2016],
               note="design 2010-2016 only; 2017+ gold and external data not read before this lock")
    write_json(OUT / "LOCK.json", out)
    (OUT / "LOCK.sha256").write_text(sha(OUT / "LOCK.json"))
    print("LOCK", status, json.dumps(filt), json.dumps({k: final[k] for k in ("net", "dd", "trades", "recent")}), flush=True)


def read_lock():
    lock = json.loads((OUT / "LOCK.json").read_text())
    if sha(OUT / "LOCK.json") != (OUT / "LOCK.sha256").read_text().strip():
        raise ValueError("v1-r3 LOCK changed")
    return lock


def stop_theta_ratio(c, res, info):
    tr = res.trades
    out = {}
    for r in ("A", "B"):
        t = tr[(tr.rule == r) & (tr.exit_reason == "stop")]
        if not len(t):
            continue
        ix = np.searchsorted(c["mins"], t.t_exit.to_numpy())
        ix = np.minimum(ix, len(c["mins"]) - 1)
        q = info[r]["thr"][ix] / t.theta_bps.to_numpy()
        out[r] = dict(stops=int(len(t)), median=float(np.nanmedian(q)), share_gt_1_5=float(np.nanmean(q > 1.5)))
    return out


def evaluate():
    if (OUT / "EVALUATION.json").exists():
        raise FileExistsError("already evaluated")
    lock, l2 = read_lock(), lock2_info()
    filt = lock["filters"]
    scen = {"fixed": d.engine.Config(), "cost_example": d.engine.Config(commission=.01, slippage=.02),
            "historical": d.engine.Config(cost_mode="historical")}
    res_all = {}
    for period, years in (("full", list(range(2010, 2020))), ("validation", [2017, 2018, 2019])):
        c = context(years, "evaluate", "2019-12-31")
        res_all[period] = {}
        for sc, cfg in scen.items():
            a, ia = run(c, {}, l2, cfg)
            b, ib = run(c, filt, l2, cfg)
            ma, mb = d.metrics(a), d.metrics(b)
            row = {"v1-r2": ma, "v1-r3": mb, "t_diff": t_diff(a.trades, b.trades)}
            if sc == "fixed":
                row["sessions"] = {"v1-r2": r2.by_session(a.trades, c), "v1-r3": r2.by_session(b.trades, c)}
                row["yearly"] = {"v1-r2": r2.yearly(a, years), "v1-r3": r2.yearly(b, years)}
                row["stop_theta_ratio"] = {"v1-r2": stop_theta_ratio(c, a, ia), "v1-r3": stop_theta_ratio(c, b, ib)}
                loo = {}
                for r in ("A", "B"):
                    for fam in filt[r]:
                        f2 = {k: dict(v) for k, v in filt.items()}
                        del f2[r][fam]
                        x, _ = run(c, f2, l2, cfg)
                        loo[f"{r}-{fam}"] = mb["net"] - d.metrics(x)["net"]
                row["leave_one_out_net_contribution"] = loo
                b.trades.to_csv(OUT / f"TRADES_{period}_fixed.private.csv", index=False)
            res_all[period][sc] = row
            print(period, sc, "v1-r2", json.dumps({k: round(ma[k]) for k in ("net", "dd", "trades")}),
                  "| v1-r3", json.dumps({k: round(mb[k]) for k in ("net", "dd", "trades")}), "t", round(row["t_diff"], 2), flush=True)
    v = res_all["validation"]["fixed"]
    passed = bool(lock["status"] == "SELECTED" and v["v1-r3"]["net"] > v["v1-r2"]["net"] and v["v1-r3"]["dd"] <= v["v1-r2"]["dd"]
                  and good(v["v1-r3"]))
    doc = dict(version=VERSION, lock_sha256=sha(OUT / "LOCK.json"), results=res_all, passed=passed,
               status=("PASS" if passed else "NOT_CONFIRMED"), finished_utc=datetime.now(timezone.utc).isoformat())
    write_json(OUT / "EVALUATION.json", doc)
    print("VERDICT", doc["status"], flush=True)


def extend():
    lock, l2 = read_lock(), lock2_info()
    years = list(range(2010, 2023))
    c = context(years, "extend", "2022-12-31")
    out = {}
    base_tr = None
    for name, f in (("v1-r2", {}), ("v1-r3", lock["filters"])):
        res, info = run(c, f, l2)
        m = d.metrics(res)
        out[name] = dict(metrics=m, yearly=r2.yearly(res, years), sessions=r2.by_session(res.trades, c),
                         by_rule={k: dict(trades=int(len(g)), net=float(g.net_thb.sum())) for k, g in res.trades.groupby("rule")})
        if base_tr is None:
            base_tr = res.trades
        else:
            out["t_diff_2010_2022"] = t_diff(base_tr, res.trades)
        res.trades.to_csv(OUT / f"TRADES_2010_2022_{name}.private.csv", index=False)
        print(name, json.dumps({k: round(m[k]) for k in ("net", "dd", "trades", "lowest")}), flush=True)
    write_json(OUT / "EXTEND_2010_2022.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=["check", "design", "evaluate", "extend"])
    a = ap.parse_args()
    if a.phase == "check":
        check(context(list(range(2010, 2017)), "design", "2016-12-31"), lock2_info())
    else:
        {"design": design, "evaluate": evaluate, "extend": extend}[a.phase]()
