"""Swing strategy on E68 A2 B zones (see ../PLAN.md). 2011-2019 only; money at the time's price."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-adaptive-bounce" / "code"))
from adaptive import apply_stop, load_series, sigma60  # noqa: E402

_spec = importlib.util.spec_from_file_location("factors_build", ROOT.parent / "swing-factors-b1" / "code" / "build.py")
_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fb)
sigma_long, zigzag_x = _fb.sigma_long, _fb.zigzag_x
EDGE = ROOT.parent / "microstructure-edge-map" / "cache"
B68 = Path(r"C:\Users\ASUS\Documents\Codex\2026-10-30\task-6\deliverables\e68-a2-2011-2022")
YEARS = list(range(2011, 2020))
RULES = {"A": (1.0, "eff"), "B": (1.5, "s60")}
SPREAD, OZ, FX = 0.168, 10, 33.77

ev = pd.read_csv(B68 / "EVENTS.private.csv.gz")
ev = ev[(ev["status"] == "ISSUED") & (ev["year"] <= 2019)].copy()
zn = pd.read_csv(B68 / "SELECTED_ZONES.private.csv.gz")
zn = zn[zn["delivered"] & (zn["year"] <= 2019)]
zones = {k: g.sort_values("global_rank")[["lower", "upper", "side", "global_rank"]].to_numpy() for k, g in zn.groupby("event_key")}
ev = ev[ev["event_key"].isin(zones)].sort_values("lock_minute")
LOCK, END, KEYS = ev["lock_minute"].to_numpy().astype(np.int64), ev["end_minute"].to_numpy().astype(np.int64), ev["event_key"].to_numpy()
SESSION_DAYS = {yr: int(((ev["year"] == yr)).sum()) for yr in YEARS}


def year_rows(yr, rule):
    k, kind = RULES[rule]
    y, mins, blk = load_series(yr)
    n = len(y)
    zp = np.load(EDGE / f"M1_{yr}.private.npz")
    base = int(zp["base"])
    pos = (mins - base).astype(np.int64)
    mid = (zp["bid"][pos] + zp["ask"][pos]) / 2
    bz = np.load(ROOT / "cache" / f"BID_{yr}.private.npz")
    assert int(bz["base"]) == base
    bh, bl, bc = bz["high"][pos], bz["low"][pos], bz["close"][pos]
    s60 = sigma60(y, blk)
    sl_ = sigma_long(y, blk)
    seff = np.where(np.isfinite(sl_), np.fmax(s60, sl_), s60)
    T = k * (seff if kind == "eff" else s60)
    idx, d, ext, exi, th = zigzag_x(y, blk, T)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(len(idx), np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    peak = np.r_[0, exi[:-1]]
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (B / th >= 2.5)
    ex = np.minimum(exit_i + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    rows = []
    for j in np.flatnonzero(ok):
        tp, te = int(mins[peak[j]]), int(mins[ent[j]])
        s = int(np.searchsorted(LOCK, tp, side="right")) - 1
        if s < 0 or tp >= END[s] or te >= END[s]:
            continue
        p = peak[j]
        w = np.arange(max(p - 2, 0), min(p + 3, n))
        w = w[blk[w] == blk[p]]
        hmax, lmin, cpk = np.nanmax(bh[w]), np.nanmin(bl[w]), bc[p]
        zz = zones[KEYS[s]]
        sell = d[j] == 1
        hit = (zz[:, 0] <= hmax) & (zz[:, 1] >= cpk) if sell else (zz[:, 1] >= lmin) & (zz[:, 0] <= cpk)
        hz = np.flatnonzero(hit)
        level = np.nan
        if len(hz):
            z0 = zz[hz[0]]
            hs = mid[p] - bc[p]
            level = (max(hmax, z0[1]) if sell else min(lmin, z0[0])) + hs
        rows.append(dict(j=j, Z=bool(len(hz)), zside=zz[hz[0], 2] if len(hz) else "", zrank=int(zz[hz[0], 3]) if len(hz) else 0,
                         level=level, session=KEYS[s].split("|")[1]))
    if not rows:
        return pd.DataFrame()
    R = pd.DataFrame(rows)
    jj = R["j"].to_numpy()
    sg = -d[jj].astype(np.float64)
    e = ent[jj]
    o3, st3 = apply_stop(y, e, ex[jj], sg, 3.0 * th[jj])
    lvl = R["level"].to_numpy()
    dist = np.where(np.isfinite(lvl), sg * (y[e] - 1e4 * np.log(np.where(np.isfinite(lvl), lvl, 1.0))), np.nan)
    dist = np.where(np.isfinite(dist), np.maximum(dist, 0.1), -1.0)
    op, stp = apply_stop(y, e, ex[jj], sg, dist)
    R["net3"] = sg * (mid[o3] - mid[e]) - SPREAD
    R["stop3"] = st3 == 1
    R["netp"] = np.where(np.isfinite(lvl), sg * (mid[op] - mid[e]) - SPREAD, np.nan)
    R["stopp"] = stp == 1
    R["peak_dist_theta"] = dist / th[jj]
    R["t_ent"], R["t_exit3"], R["t_exitp"] = mins[e].astype(np.int64), mins[o3].astype(np.int64), mins[op].astype(np.int64)
    R["day"] = (R["t_ent"] * 60 + 3 * 3600) // 86400
    R["yr"], R["rule"], R["side"] = yr, rule, np.where(sg < 0, "sell", "buy")
    return R.drop(columns=["j"])


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(se)


D = pd.concat([year_rows(yr, r) for r in RULES for yr in YEARS], ignore_index=True)
D.to_pickle(ROOT / "cache" / "TRADES.private.pkl")
rep = {}
for per, (lo, hi) in {"2011-19": (2011, 2019), "2011-16": (2011, 2016), "2017-19": (2017, 2019)}.items():
    m = D["yr"].between(lo, hi)
    z, nz = D[m & D["Z"]], D[m & ~D["Z"]]
    mz, sz = ct(z["net3"], z["day"])
    mn, sn = ct(nz["net3"], nz["day"])
    mp, spp = ct(z["netp"], z["day"])
    rep[per] = dict(nZ=len(z), nN=len(nz), Z_net=mz, Z_t=mz / sz, N_net=mn, N_t=mn / sn, diff=mz - mn, diff_t=(mz - mn) / np.hypot(sz, sn),
                    Zpeak_net=mp, Zpeak_t=mp / spp, Z_win=float((z["net3"] > 0).mean()), Z_stop=float(z["stop3"].mean()),
                    Zpeak_stop=float(z["stopp"].mean()), N_win=float((nz["net3"] > 0).mean()))
p = rep
primary = bool(p["2011-19"]["diff_t"] >= 2 and np.sign(p["2011-16"]["diff"]) == np.sign(p["2017-19"]["diff"]) == np.sign(p["2011-19"]["diff"]))
by_rule = {r: {g: dict(n=int(len(x)), net=float(x["net3"].mean()), netp=float(x["netp"].mean()) if g == "Z" else None)
               for g, x in (("Z", D[(D.rule == r) & D.Z]), ("N", D[(D.rule == r) & ~D.Z]))} for r in RULES}
yearly = {}
for yr in YEARS:
    z = D[(D.yr == yr) & D.Z]
    row = {}
    for v, col, tcol in (("Z_3theta", "net3", "t_exit3"), ("Z_peak", "netp", "t_exitp"), ("N", "net3", "t_exit3")):
        x = z if v != "N" else D[(D.yr == yr) & ~D.Z]
        x = x.sort_values(tcol)
        thb = x[col].to_numpy() * OZ * FX
        eq = np.cumsum(thb)
        dd = float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max()) if len(eq) else 0.0
        row[v] = dict(n=int(len(x)), win=float((thb > 0).mean()) if len(x) else 0, thb=float(thb.sum()), dd=dd,
                      net_oz=float(x[col].mean()) if len(x) else 0)
    yearly[yr] = row
zz = D[D.Z]
brk = {"by_zone_side": zz.groupby("zside")["net3"].agg(["size", "mean"]).round(3).to_dict(),
       "by_zone_rank": zz.groupby("zrank")["net3"].agg(["size", "mean"]).round(3).to_dict(),
       "by_trade_side": zz.groupby("side")["net3"].agg(["size", "mean"]).round(3).to_dict(),
       "by_session": zz.groupby("session")["net3"].agg(["size", "mean"]).round(3).to_dict(),
       "peak_dist_theta_median": float(zz["peak_dist_theta"].median())}
json.dump(dict(periods=rep, primary_pass=primary, by_rule=by_rule, yearly=yearly, breakdown=brk), open(ROOT / "out" / "BZONE.json", "w"),
          indent=1, default=str)
print("population (peak and entry inside a B session window), rules A + B, 2011-2019:", len(D), "trades; Z", int(D.Z.sum()))
for per, r in rep.items():
    print(f"{per}: Z n {r['nZ']} net {r['Z_net']:+.3f} (t {r['Z_t']:+.1f}) win {100 * r['Z_win']:.0f}% stop {100 * r['Z_stop']:.1f}% | "
          f"Z-peak net {r['Zpeak_net']:+.3f} (t {r['Zpeak_t']:+.1f}) stop {100 * r['Zpeak_stop']:.1f}% | N n {r['nN']} net {r['N_net']:+.3f} "
          f"(t {r['N_t']:+.1f}) win {100 * r['N_win']:.0f}% | diff {r['diff']:+.3f} (t {r['diff_t']:+.1f})")
print("PRIMARY (Z better than N) pass:", primary)
print("by rule:", json.dumps(by_rule))
print("year | Z trades | Z win | Z THB (3theta) | Z DD | Z-peak THB | Z-peak DD | N trades | N THB")
for yr, r in yearly.items():
    a, b, c = r["Z_3theta"], r["Z_peak"], r["N"]
    print(f"{yr} | {a['n']} | {100 * a['win']:.0f}% | {a['thb']:+,.0f} | {a['dd']:,.0f} | {b['thb']:+,.0f} | {b['dd']:,.0f} | {c['n']} | {c['thb']:+,.0f}")
print("breakdown:", json.dumps(brk))
