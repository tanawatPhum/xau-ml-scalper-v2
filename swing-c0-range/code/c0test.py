"""C0 range formula test (see ../PLAN.md). 2010-2019 only; money at the time's price."""
import importlib.util
import json
import sys
from pathlib import Path

import numba as nb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "swing-adaptive-bounce" / "code"))
from adaptive import apply_stop, load_series, sigma60  # noqa: E402

_spec = importlib.util.spec_from_file_location("factors_build", ROOT.parent / "swing-factors-b1" / "code" / "build.py")
_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fb)
sigma_long, zigzag_x = _fb.sigma_long, _fb.zigzag_x
EDGE = ROOT.parent / "microstructure-edge-map" / "cache"
DAYS = {int(k): v for k, v in json.load(open(ROOT.parent / "swing-adaptive-bounce" / "out" / "TRADING_DAYS.json")).items()}
YEARS = list(range(2010, 2020))
RULES = {"A": (1.0, "eff"), "B": (1.5, "s60")}
SPREAD, OZ, FX, H = 0.168, 10, 33.77, 80
PERIODS = {"2010-16": list(range(2010, 2017)), "2017-19": [2017, 2018, 2019]}


@nb.njit(cache=True)
def bracket(y, mins, blk, ent, sgn, tp, sl, hmin, lastb):
    m = len(ent)
    out = np.empty(m, np.int64)
    why = np.zeros(m, np.int64)  # 1 tp, 2 stop, 3 time, 4 block end
    for k in range(m):
        e = ent[k]
        j = e
        while True:
            j += 1
            if j > lastb[k]:
                j = lastb[k]
                why[k] = 4
                break
            mv = sgn[k] * (y[j] - y[e])
            if mv >= tp[k]:
                why[k] = 1
                break
            if mv <= -sl[k]:
                why[k] = 2
                break
            if mins[j] - mins[e] >= hmin:
                why[k] = 3
                break
        out[k] = j
    return out, why


def one_position(ent_t, exit_t):
    keep = np.zeros(len(ent_t), bool)
    busy = -1
    for i in np.argsort(ent_t, kind="stable"):
        if ent_t[i] >= busy:
            keep[i] = True
            busy = exit_t[i]
    return keep


def year_rows(yr, k, kind):
    y, mins, blk = load_series(yr)
    n = len(y)
    zp = np.load(EDGE / f"M1_{yr}.private.npz")
    pos = (mins - int(zp["base"])).astype(np.int64)
    mid = (zp["bid"][pos] + zp["ask"][pos]) / 2
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
    tleg = (mins[exi] - mins[peak]).astype(float)
    z = B / (s60[peak] * np.sqrt(np.maximum(tleg, 1) / 60))
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (B / th >= 2.5)
    ex = np.minimum(exit_i + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    e, sg, sH = ent[ok], -d[ok].astype(np.float64), seff[idx[ok]] * np.sqrt(H / 60)
    lastb = last_of_blk[eb[ok]]
    res = {}
    o0, st0 = apply_stop(y, e, ex[ok], sg, 3.0 * th[ok])
    res["E0"] = (o0, np.where(st0 == 1, 2, 0))
    o1, st1 = apply_stop(y, e, ex[ok], sg, 1.645 * sH)
    res["E1"] = (o1, np.where(st1 == 1, 2, 0))
    res["E2"] = bracket(y, mins, blk, e, sg, 0.674 * sH, 1.645 * sH, H, lastb)
    res["E3"] = bracket(y, mins, blk, e, sg, 1.645 * sH, 1.645 * sH, H, lastb)
    out = {}
    for v, (o, why) in res.items():
        keep = one_position(mins[e], mins[o])
        net = (sg * (mid[o] - mid[e]) - SPREAD)
        out[v] = dict(net=net[keep], stop=(why[keep] == 2), t_exit=mins[o][keep].astype(np.int64),
                      day=((mins[e][keep].astype(np.int64) * 60 + 3 * 3600) // 86400), z=z[ok][keep],
                      yr=np.full(int(keep.sum()), yr))
    return out


def cat(parts):
    return {f: np.concatenate([p[f] for p in parts]) for f in parts[0]}


def ct(x, day):
    u, inv = np.unique(day, return_inverse=True)
    S, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = S.sum() / N.sum()
    se = np.sqrt(((S - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(mu / se)


def pstats(z, yrs):
    m = np.isin(z["yr"], yrs)
    x, te = z["net"][m], z["t_exit"][m]
    thb = x * OZ * FX
    o = np.argsort(te, kind="stable")
    eq = np.cumsum(thb[o])
    dd = float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max())
    loss = thb < 0
    st = z["stop"][m]
    return dict(trades=int(m.sum()), per_day=float(m.sum() / sum(DAYS[y] for y in yrs)), net_oz=float(x.mean()),
                total=float(thb.sum()), max_dd=dd, win=float((x > 0).mean()), stop_rate=float(st.mean()),
                stop_loss_share=float(-thb[loss & st].sum() / -thb[loss].sum()) if loss.any() else 0.0,
                worst=float(thb.min()))


rep = {}
for r, (k, kind) in RULES.items():
    parts = [year_rows(yr, k, kind) for yr in YEARS]
    Z = {v: cat([p[v] for p in parts]) for v in ("E0", "E1", "E2", "E3")}
    rr = {v: {p: pstats(Z[v], yrs) for p, yrs in PERIODS.items()} for v in Z}
    # Part 1: stretch terciles on E0
    z0 = Z["E0"]
    disc = z0["yr"] <= 2016
    val = (z0["yr"] >= 2017) & (z0["yr"] <= 2019)
    cuts = np.nanquantile(z0["z"][disc], [1 / 3, 2 / 3])
    g = np.where(np.isfinite(z0["z"]), np.digitize(z0["z"], cuts), -1)
    tab = {}
    for i, nm in enumerate(("low", "mid", "high")):
        row = {}
        for p, m in (("2010-16", disc), ("2017-19", val)):
            mm = m & (g == i)
            mu, t = ct(z0["net"][mm], z0["day"][mm])
            se = mu / t if t else np.nan
            row[p] = dict(n=int(mm.sum()), net=mu, se=se, stop=float(z0["stop"][mm].mean()))
        tab[nm] = row
    md = np.array([tab[nm]["2010-16"]["net"] for nm in ("low", "mid", "high")])
    b, w = int(np.argmax(md)), int(np.argmin(md))
    names = ("low", "mid", "high")

    def tdiff(p):
        a, c = tab[names[b]][p], tab[names[w]][p]
        return (a["net"] - c["net"]) / np.hypot(a["se"], c["se"])

    part1 = dict(cuts=[float(c) for c in cuts], table=tab, best=names[b], worst=names[w], t_disc=float(tdiff("2010-16")),
                 t_val=float(tdiff("2017-19")))
    part1["matters"] = bool(abs(part1["t_disc"]) >= 3 and part1["t_val"] >= 2)
    acc = [v for v in ("E1", "E2", "E3") if all(rr[v][p]["total"] > rr["E0"][p]["total"] and rr[v][p]["max_dd"] < rr["E0"][p]["max_dd"]
                                                for p in PERIODS)]
    if len(acc) > 1:
        acc = [max(acc, key=lambda v: sum(rr[v][p]["total"] for p in PERIODS))]
    rep[r] = dict(exits=rr, stretch=part1, accepted_exit=acc[0] if acc else "E0 (none accepted)")
json.dump(rep, open(ROOT / "out" / "C0TEST.json", "w"), indent=1, default=float)
for r, x in rep.items():
    print(f"\n######## rule {r}")
    s = x["stretch"]
    print(f"  Part 1 stretch z cuts {np.round(s['cuts'], 2).tolist()}: best {s['best']} vs worst {s['worst']} t {s['t_disc']:+.1f} / "
          f"{s['t_val']:+.1f} -> {'MATTERS' if s['matters'] else 'no'}")
    for nm, row in s["table"].items():
        print("     " + nm + " | " + " | ".join(f"{p}: n {v['n']} net {v['net']:+.3f} $/oz stop {100 * v['stop']:.1f}%" for p, v in row.items()))
    print("  Part 2 exits (trades/day | net $/oz | total THB | max DD THB | win | stop rate | stop share of losses | worst THB)")
    for v, pp in x["exits"].items():
        for p, q in pp.items():
            print(f"     {v} {p}: {q['per_day']:.2f} | {q['net_oz']:+.3f} | {q['total']:+,.0f} | {q['max_dd']:,.0f} | {100 * q['win']:.0f}% | "
                  f"{100 * q['stop_rate']:.1f}% | {100 * q['stop_loss_share']:.0f}% | {q['worst']:,.0f}")
    print("  accepted exit:", x["accepted_exit"])
