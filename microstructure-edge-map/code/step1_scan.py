"""Step 1 scan (see PLAN.md). Discovery 2010-2016, confirmation 2017-2022, 20 sign-flip nulls."""

import json

import numpy as np
import pandas as pd

from common import CACHE, OUT, OWNER_BPS

H = (1, 5, 15, 30, 60)
NPERM = 20
rng = np.random.default_rng(20261031)


def cell_stats(cell, day, prev, nxt, thr, flip):
    """E (strong moves), clustered t, n, rho per cell."""
    sp = np.sign(prev) * flip
    strong = np.abs(prev) >= thr[cell]
    df = pd.DataFrame({"c": cell[strong], "d": day[strong], "o": (sp * nxt)[strong]})
    g = df.groupby(["c", "d"])["o"].agg(["sum", "count"]).reset_index()
    out = {}
    for c, gg in g.groupby("c"):
        S, n = gg["sum"].to_numpy(), gg["count"].to_numpy()
        E = S.sum() / n.sum()
        D = len(S)
        se = np.sqrt(D / max(D - 1, 1) * np.sum((S - E * n) ** 2)) / n.sum()
        out[int(c)] = (E, E / se if se > 0 else 0.0, int(n.sum()))
    rho = pd.DataFrame({"c": cell, "a": prev * flip, "b": nxt}).groupby("c")[["a", "b"]].corr()
    rr = {int(c): float(rho.loc[(c, "a"), "b"]) for c in np.unique(cell)}
    return out, rr


def evaluate(A, key, thr_cells, flip_day):
    yr, day = A[:, 0].astype(int), A[:, 1].astype(np.int64)
    prev, nxt, spread, mid = A[:, 4], A[:, 5], A[:, 6], A[:, 7]
    flip = flip_day[day - day.min()] if flip_day is not None else np.ones(len(A))
    res = {}
    for name, m in (("disc", yr <= 2016), ("conf", yr >= 2017)):
        st, rr = cell_stats(key[m], day[m], prev[m], nxt[m], thr_cells, flip[m])
        res[name] = (st, rr)
    cost = {}
    m = yr >= 2017
    for c in np.unique(key[m]):
        mm = m & (key == c)
        cost[int(c)] = (float(np.median(spread[mm])), float(OWNER_BPS * np.median(mid[mm]) / 1e4))
    return res, cost


def passes(res, cost):
    out = []
    d, c = res["disc"][0], res["conf"][0]
    for k in d:
        if k not in c:
            continue
        Ed, td, _ = d[k]
        Ec, tc, nc = c[k]
        s = np.sign(Ed)
        nonrand = abs(td) >= 3 and s * tc >= 2
        if nonrand:
            out.append(dict(cell=k, E_disc=Ed, t_disc=td, E_conf=Ec, t_conf=tc, n_conf=nc,
                            edge_conf=s * Ec, duka_spread=cost[k][0], owner_cost=cost[k][1],
                            trad_duka=bool(s * Ec > cost[k][0]),
                            trad_owner=bool(s * Ec > cost[k][1])))
    return out


report = {}
for h in H:
    A = np.load(CACHE / f"BLOCKS_h{h}.private.npy")
    yr, hr, S, prev = A[:, 0].astype(int), A[:, 2].astype(int), A[:, 3], A[:, 4]
    disc = yr <= 2016
    cuts = np.quantile(S[disc], [1 / 3, 2 / 3])
    terc = np.searchsorted(cuts, S)
    day = A[:, 1].astype(np.int64)
    ndays = int(day.max() - day.min() + 1)
    z = prev / (S * np.sqrt(h / 60))
    keys = {
        "pooled": np.zeros(len(A), int),
        "hour": hr,
        "hour_x_vol": hr * 3 + terc,
    }
    rep_h = {}
    for kname, key in keys.items():
        thr = np.full(key.max() + 1, np.inf)
        for c in np.unique(key[disc]):
            thr[c] = np.quantile(np.abs(prev[disc & (key == c)]), 0.8)
        res, cost = evaluate(A, key, thr, None)
        real = passes(res, cost)
        null_counts = []
        if kname == "hour_x_vol":
            for _ in range(NPERM):
                fl = rng.choice([-1.0, 1.0], ndays)
                r2, c2 = evaluate(A, key, thr, fl)
                p2 = passes(r2, c2)
                null_counts.append((len(p2), sum(x["trad_owner"] for x in p2),
                                    sum(x["trad_duka"] for x in p2)))
        rep_h[kname] = dict(
            cells=len(res["disc"][0]),
            nonrandom=len(real),
            trad_owner=sum(x["trad_owner"] for x in real),
            trad_duka=sum(x["trad_duka"] for x in real),
            null_mean=[float(np.mean([n[i] for n in null_counts])) for i in range(3)]
            if null_counts else None,
            null_max=[int(np.max([n[i] for n in null_counts])) for i in range(3)]
            if null_counts else None,
            passing=real,
            disc={k: list(v) for k, v in res["disc"][0].items()},
            conf={k: list(v) for k, v in res["conf"][0].items()},
            rho_disc=res["disc"][1], rho_conf=res["conf"][1], cost=cost)
    # jump bucket per hour (secondary)
    jm = np.abs(z) >= 2.5
    jk = np.where(jm, hr, -1)
    A2 = A[jm]
    thr = np.zeros(24)
    resj, costj = evaluate(A2, hr[jm], thr, None)
    rep_h["jump_hour"] = dict(nonrandom=passes(resj, costj),
                              disc={k: list(v) for k, v in resj["disc"][0].items()},
                              conf={k: list(v) for k, v in resj["conf"][0].items()})
    resp, costp = evaluate(A2, np.zeros(len(A2), int), np.zeros(1), None)
    rep_h["jump_pooled"] = dict(disc=resp["disc"][0], conf=resp["conf"][0])
    report[h] = rep_h
    p = rep_h["pooled"]
    print(f"\n===== h = {h} min, n = {len(A)}")
    print(f" pooled strong-move E disc {p['disc'][0][0]:+.4f} (t {p['disc'][0][1]:+.1f}) "
          f"conf {p['conf'][0][0]:+.4f} (t {p['conf'][0][1]:+.1f}) | rho disc "
          f"{p['rho_disc'][0]:+.4f} conf {p['rho_conf'][0]:+.4f} | owner cost "
          f"{p['cost'][0][1]:.3f}, duka {p['cost'][0][0]:.3f}")
    jp = rep_h["jump_pooled"]
    print(f" jumps |z|>=2.5: E disc {jp['disc'][0][0]:+.4f} (t {jp['disc'][0][1]:+.1f}, "
          f"n {jp['disc'][0][2]}) conf {jp['conf'][0][0]:+.4f} (t {jp['conf'][0][1]:+.1f}, "
          f"n {jp['conf'][0][2]})")
    for kname in ("hour", "hour_x_vol"):
        r = rep_h[kname]
        print(f" {kname:10s}: cells {r['cells']}, non-random {r['nonrandom']}, tradable owner "
              f"{r['trad_owner']}, tradable duka {r['trad_duka']}"
              + (f" | null mean {r['null_mean']} max {r['null_max']}" if r["null_mean"] else ""))
        for x in r["passing"]:
            hh = x["cell"] if kname == "hour" else x["cell"] // 3
            tt = "" if kname == "hour" else f" vol{x['cell'] % 3}"
            print(f"    NY {hh:02d}h{tt}: E disc {x['E_disc']:+.4f} (t {x['t_disc']:+.1f}) conf "
                  f"{x['E_conf']:+.4f} (t {x['t_conf']:+.1f}, n {x['n_conf']}) | edge "
                  f"{x['edge_conf']:.4f} vs owner {x['owner_cost']:.3f} / duka "
                  f"{x['duka_spread']:.3f}")
    jn = rep_h["jump_hour"]["nonrandom"]
    print(f" jump x hour non-random: {len(jn)}",
          [(x["cell"], round(x["E_conf"], 3), round(x["t_conf"], 1), x["trad_owner"])
           for x in jn])
with open(OUT / "STEP1_SCAN.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1, default=float)
