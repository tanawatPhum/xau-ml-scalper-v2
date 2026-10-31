"""Part A (catalogue) and Part B (playability). Usage: analysis.py [synth]"""

import json
import sys

import numpy as np
import pandas as pd

from patterns import CACHE, FAM_OF_CODE, FAMILIES, NAMES, OUT, OWNER_BPS, PREFIXES, states

LS = (5, 10, 20)
rng = np.random.default_rng(20261031)


def load(name):
    z = np.load(CACHE / f"{name}.private.npz")
    return {k: z[k] for k in z.files}


def coded(d, theta):
    st = states(np.stack([d["m1"], d["m2"], d["m3"]], 1),
                np.stack([d["sig1"], d["sig2"], d["sig3"]], 1), theta)
    return st, (9 * st[:, 0] + 3 * st[:, 1] + st[:, 2]).astype(int)


def share(code, k):
    return np.bincount(code, minlength=k) / max(len(code), 1)


def boot_ci(code, day, k, nboot=300):
    days, inv = np.unique(day, return_inverse=True)
    cnt = np.zeros((len(days), k))
    np.add.at(cnt, (inv, code), 1)
    tot = cnt.sum(1)
    res = np.array([cnt[p].sum(0) / tot[p].sum()
                    for p in (rng.integers(0, len(days), len(days)) for _ in range(nboot))])
    return np.quantile(res, 0.025, 0), np.quantile(res, 0.975, 0)


def cluster_t(y, day):
    days, inv = np.unique(day, return_inverse=True)
    S, n = np.bincount(inv, y), np.bincount(inv)
    E = S.sum() / n.sum()
    D = len(S)
    se = np.sqrt(D / max(D - 1, 1) * np.sum((S - E * n) ** 2)) / n.sum()
    return float(E), float(E / se) if se > 0 else 0.0, int(n.sum())


def part_a(d, periods):
    st, code = coded(d, 0.5)
    fam = FAM_OF_CODE[code]
    nfam = FAM_OF_CODE[d["null"].astype(int)]
    out = {"patterns": {}, "families": {}, "transition": {}}
    for pname, m in periods.items():
        rs, ns = share(code[m], 27), share(d["null"][m].ravel().astype(int), 27)
        rf, nf = share(fam[m], 5), share(nfam[m].ravel(), 5)
        for i, nm in enumerate(NAMES):
            out["patterns"].setdefault(nm, {})[pname] = (float(rs[i]), float(ns[i]))
        for i, nm in enumerate(FAMILIES):
            out["families"].setdefault(nm, {})[pname] = (float(rf[i]), float(nf[i]))
    m = periods["all"]
    lo, hi = boot_ci(code[m], d["day"][m], 27)
    flo, fhi = boot_ci(fam[m], d["day"][m], 5)
    for i, nm in enumerate(NAMES):
        out["patterns"][nm]["ci"] = (float(lo[i]), float(hi[i]))
    for i, nm in enumerate(FAMILIES):
        out["families"][nm]["ci"] = (float(flo[i]), float(fhi[i]))

    def structured(entry):
        if "disc" not in entry:
            return None
        rd = entry["disc"][0] / entry["disc"][1]
        rc = entry["conf"][0] / entry["conf"][1]
        lo_, hi_ = entry["ci"]
        null_all = entry["all"][1]
        same = (rd > 1.05 and rc > 1.05) or (rd < 0.95 and rc < 0.95)
        return bool(same and not (lo_ <= null_all <= hi_))

    for grp in ("patterns", "families"):
        for nm, e in out[grp].items():
            e["structured"] = structured(e)
    pre = 3 * st[m, 0] + st[m, 1]
    base3 = share(st[m, 2].astype(int), 3)
    out["transition"]["base_next"] = base3.tolist()
    for p in range(9):
        out["transition"][PREFIXES[p]] = share(st[m, 2][pre == p].astype(int), 3).tolist()
    return out, st


def cell_table(key, day, yr, y, conf, flip_of_day=None):
    """Per (period, cell) clustered mean/t and per (cell, year) means of y (optionally flipped)."""
    f = np.ones(len(y)) if flip_of_day is None else flip_of_day[day - day.min()]
    df = pd.DataFrame({"per": conf.astype(int), "c": key, "d": day, "yr": yr, "v": y * f})
    g = df.groupby(["per", "c", "d"]).agg(S=("v", "sum"), n=("v", "size"), yr=("yr", "first"))
    g = g.reset_index()
    g["S2"], g["Sn"], g["n2"] = g.S ** 2, g.S * g.n, g.n ** 2
    a = g.groupby(["per", "c"]).agg(S=("S", "sum"), n=("n", "sum"), S2=("S2", "sum"),
                                    Sn=("Sn", "sum"), n2=("n2", "sum"), D=("S", "size"))
    a["E"] = a.S / a.n
    var = (a.S2 - 2 * a.E * a.Sn + a.E ** 2 * a.n2) * a.D / (a.D - 1).clip(lower=1)
    a["t"] = a.E / (np.sqrt(var.clip(lower=0)) / a.n)
    yy = g[g.per == 1].groupby(["c", "yr"]).agg(S=("S", "sum"), n=("n", "sum"))
    yy["E"] = yy.S / yy.n
    return a, yy


def part_b(d, st, cost_owner, cost_duka, nperm=20, key_kind="hour"):
    yr, day, m3 = d["yr"], d["day"], d["m3"]
    conf = yr >= 2017
    pre = (3 * st[:, 0] + st[:, 1]).astype(int)
    key = pre * 24 + d["nyh"] if key_kind == "hour" else pre
    ckeys = np.unique(key)
    oc = pd.Series(cost_owner[conf]).groupby(key[conf]).median()
    dc = pd.Series(cost_duka[conf]).groupby(key[conf]).median()

    def evaluate(flip):
        a, yy = cell_table(key, day, yr, m3, conf, flip)
        res = []
        for c in ckeys:
            if (0, c) not in a.index or (1, c) not in a.index:
                continue
            ad, ac = a.loc[(0, c)], a.loc[(1, c)]
            if ad.n < 50 or ac.n < 50:
                continue
            s = np.sign(ad.E)
            nonrand = abs(ad.t) >= 3 and s * ac.t >= 2
            gross = s * ac.E
            ye = yy.loc[c].E if c in yy.index.get_level_values(0) else pd.Series(dtype=float)
            ypos_o = int(((s * ye) - oc[c] > 0).sum())
            ypos_d = int(((s * ye) - dc[c] > 0).sum())
            res.append(dict(cell=int(c), E_disc=float(ad.E), t_disc=float(ad.t), n_disc=int(ad.n),
                            E_conf=float(ac.E), t_conf=float(ac.t), n_conf=int(ac.n),
                            gross=float(gross), owner_cost=float(oc[c]), duka_cost=float(dc[c]),
                            years_pos_owner=ypos_o, years_pos_duka=ypos_d, nonrandom=bool(nonrand),
                            play_owner=bool(nonrand and gross > oc[c] and ypos_o >= 4),
                            play_duka=bool(nonrand and gross > dc[c] and ypos_d >= 4)))
        return res

    real = evaluate(None)
    ndays = int(day.max() - day.min() + 1)
    nulls = []
    for _ in range(nperm):
        r = evaluate(rng.choice([-1.0, 1.0], ndays))
        nulls.append((sum(x["nonrandom"] for x in r), sum(x["play_owner"] for x in r),
                      sum(x["play_duka"] for x in r)))
    return real, nulls


def pooled_prefix(d, st, periods):
    pre = (3 * st[:, 0] + st[:, 1]).astype(int)
    out = {}
    for p in range(9):
        out[PREFIXES[p]] = {}
        for pname, m in periods.items():
            mm = m & (pre == p)
            E, t, n = cluster_t(d["m3"][mm], d["day"][mm])
            out[PREFIXES[p]][pname] = dict(E=E, t=t, n=n,
                                           E_sigma=float(np.mean(d["m3"][mm] / d["sig3"][mm])))
    return out


def main(synth):
    report = {}
    for L in LS:
        d = load(f"SYNTH_L{L}" if synth else f"TRIPLES_L{L}")
        yr = d["yr"]
        periods = {"all": np.ones(len(yr), bool)}
        if not synth:
            periods.update(disc=yr <= 2016, conf=yr >= 2017)
        A, st = part_a(d, periods)
        P = pooled_prefix(d, st, periods)
        rep = dict(n=int(len(yr)), A=A, pooled_prefix=P)
        if not synth:
            cost_o = OWNER_BPS * d["mid_t"] / 1e4
            cost_d = (d["sp_t"] + d["sp_tL"]) / 2
            real, nulls = part_b(d, st, cost_o, cost_d)
            rep["B_cells"] = [x for x in real if x["nonrandom"]]
            rep["B_summary"] = dict(
                cells=len(real), nonrandom=sum(x["nonrandom"] for x in real),
                play_owner=sum(x["play_owner"] for x in real),
                play_duka=sum(x["play_duka"] for x in real),
                null_mean=np.mean(nulls, 0).tolist(), null_max=np.max(nulls, 0).tolist())
            realp, nullp = part_b(d, st, cost_o, cost_d, key_kind="prefix")
            rep["B_pooled_cells"] = realp
            rep["B_pooled_null"] = dict(mean=np.mean(nullp, 0).tolist(),
                                        max=np.max(nullp, 0).tolist())
            # positive control: decision exactly at 16:00 NY
            pc = {}
            for lab, s2 in (("last_U", 2), ("last_D", 0)):
                for pname in ("disc", "conf"):
                    mm = periods[pname] & (d["nymin"] == 960) & (st[:, 1] == s2)
                    pc[f"{lab}_{pname}"] = cluster_t(d["m3"][mm], d["day"][mm])
            rep["positive_control_1600"] = pc
            st1, _ = coded(d, 1.0)
            rep["pooled_prefix_theta1"] = pooled_prefix(d, st1, periods)
            rep["costs"] = dict(owner_median=float(np.median(cost_o)),
                                duka_median=float(np.median(cost_d)),
                                abs_move_median=float(np.median(np.abs(d["m3"]))))
        report[L] = rep
        print(f"\n######## L = {L} min (window {3 * L} min), n = {len(yr)}"
              + (" [SYNTHETIC]" if synth else ""))
        print(" Families (all): real% / random-order% / ratio" +
              ("" if synth else " | disc ratio, conf ratio, structured"))
        for nm, e in A["families"].items():
            r, nl = e["all"]
            extra = "" if synth else (f" | {e['disc'][0] / e['disc'][1]:.3f}, "
                                      f"{e['conf'][0] / e['conf'][1]:.3f}, {e['structured']}")
            print(f"   {nm:9s} {r * 100:6.2f} / {nl * 100:6.2f} / {r / nl:.3f}{extra}")
        top = sorted(A["patterns"].items(), key=lambda kv: -kv[1]["all"][0])
        print(" Patterns (all) real% / null% / ratio, sorted by frequency:")
        print("   " + "  ".join(f"{nm} {e['all'][0] * 100:.1f}/{e['all'][1] * 100:.1f}"
                                f"({e['all'][0] / e['all'][1]:.2f})"
                                + ("*" if e.get("structured") else "") for nm, e in top))
        tb = A["transition"]
        print(" Next-state shares D/F/U: base " + "/".join(f"{x * 100:.1f}" for x in tb["base_next"]))
        print("   " + "  ".join(f"{p}->" + "/".join(f"{x * 100:.1f}" for x in tb[p])
                                for p in PREFIXES))
        print(" Pooled prefix -> next-segment mean move ($), t:")
        for p, e in P.items():
            s = "  ".join(f"{k} {v['E']:+.4f} (t {v['t']:+.1f})" for k, v in e.items())
            print(f"   {p}: {s}")
        if not synth:
            print(" Costs: owner median ${:.3f}, Dukascopy ${:.3f}, median |next move| ${:.3f}".format(
                rep["costs"]["owner_median"], rep["costs"]["duka_median"],
                rep["costs"]["abs_move_median"]))
            b = rep["B_summary"]
            print(f" Part B prefix x NY hour: cells {b['cells']}, non-random {b['nonrandom']}, "
                  f"playable owner {b['play_owner']}, playable Dukascopy {b['play_duka']} | "
                  f"null mean {np.round(b['null_mean'], 2).tolist()} max {b['null_max']}")
            for x in sorted(rep["B_cells"], key=lambda z: -z["gross"]):
                p, h = PREFIXES[x["cell"] // 24], x["cell"] % 24
                print(f"   {p} NY{h:02d}: E disc {x['E_disc']:+.4f} (t {x['t_disc']:+.1f}) conf "
                      f"{x['E_conf']:+.4f} (t {x['t_conf']:+.1f}, n {x['n_conf']}) gross "
                      f"{x['gross']:.4f} | owner {x['owner_cost']:.3f} yrs+ {x['years_pos_owner']}"
                      f" | duka {x['duka_cost']:.3f} | play_owner {x['play_owner']}")
            print(" Pooled prefixes passing:",
                  [(PREFIXES[x["cell"]], round(x["gross"], 4), x["play_owner"])
                   for x in rep["B_pooled_cells"] if x["nonrandom"]],
                  "null", rep["B_pooled_null"])
            print(" Positive control at 16:00 NY (E, t, n):",
                  {k: (round(v[0], 3), round(v[1], 1), v[2])
                   for k, v in rep["positive_control_1600"].items()})
    name = "SYNTH_REPORT.json" if synth else "REPORT.json"
    with open(OUT / name, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, default=float)


if __name__ == "__main__":
    main("synth" in sys.argv)
