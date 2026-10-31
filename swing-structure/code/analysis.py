"""Swing pattern structure (Part A) and playability after the owner's cost (Part B)."""

import json

import numpy as np
import pandas as pd

from swing import (CACHE, COST_BPS, FAMILY, FAMILY_NAMES, NAMES, OUT, RW_FAMILY, THETA_USD,
                   USD_PER_BPS)

rng = np.random.default_rng(20261031)
U = USD_PER_BPS  # bps -> today's dollars


def tstat(x):
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 1 else 0.0


def cell_stats(y, day, conf, yr, flip=None):
    """Clustered (by UTC day) mean and t for discovery (conf False) and confirmation."""
    f = np.ones(len(y)) if flip is None else flip[day - day.min()]
    df = pd.DataFrame({"p": conf.astype(int), "d": day, "v": y * f, "yr": yr})
    g = df.groupby(["p", "d"]).agg(S=("v", "sum"), n=("v", "size"), yr=("yr", "first"))
    g = g.reset_index()
    res = {}
    for p in (0, 1):
        gg = g[g.p == p]
        S, n = gg.S.to_numpy(), gg.n.to_numpy()
        if n.sum() < 30:
            res[p] = (np.nan, 0.0, int(n.sum()))
            continue
        E = S.sum() / n.sum()
        D = len(S)
        se = np.sqrt(D / max(D - 1, 1) * np.sum((S - E * n) ** 2)) / n.sum()
        res[p] = (float(E), float(E / se) if se > 0 else 0.0, int(n.sum()))
    gy = g[g.p == 1].groupby("yr").agg(S=("S", "sum"), n=("n", "sum"))
    res["years"] = (gy.S / gy.n).to_dict()
    return res


def judge(st):
    Ed, td, nd = st[0]
    Ec, tc, nc = st[1]
    if not np.isfinite(Ed) or not np.isfinite(Ec):
        return None
    s = 1.0 if Ed > 0 else -1.0
    nonrand = abs(td) >= 3 and s * tc >= 2
    net = s * Ec - COST_BPS
    ypos = sum(1 for v in st["years"].values() if s * v - COST_BPS > 0)
    return dict(side="follow" if s > 0 else "fade", E_disc=Ed * U, t_disc=td, n_disc=nd,
                E_conf=Ec * U, t_conf=tc, n_conf=nc, gross_conf=s * Ec * U, net_conf=net * U,
                years_pos=ypos, nonrandom=bool(nonrand),
                playable=bool(nonrand and net > 0 and ypos >= 4),
                years_net={int(k): round((s * v - COST_BPS) * U, 3)
                           for k, v in st["years"].items()})


def main():
    synth = json.load(open(OUT / "SYNTH.json", encoding="utf-8"))
    nullj = json.load(open(OUT / "NULL_SIGNFLIP.json", encoding="utf-8"))
    report = {}
    for tu in THETA_USD:
        z = np.load(CACHE / f"EVENTS_theta{tu}.private.npz")
        ev = {k: z[k] for k in z.files}
        v = ev["code"] >= 0
        ev = {k: x[v] for k, x in ev.items()}
        code, yr, day = ev["code"], ev["yr"], ev["day"]
        conf = yr >= 2017
        nyears_days = len(np.unique(day))
        rep = dict(events_per_day=float(len(code) / nyears_days),
                   median_leg_usd=float(np.median(ev["A"]) * U),
                   median_r1_minutes=float(np.median(ev["r1dur"])))
        # ---- Part A: shares real vs null vs theory
        share = np.bincount(code, minlength=8) / len(code)
        nl = nullj[str(tu)]
        ncount = np.array([sum(x[str(c)]["n"] for x in nl) for c in range(8)], float)
        nshare = ncount / ncount.sum()
        fam_real = np.bincount(FAMILY[code], minlength=4) / len(code)
        fam_null = np.array([nshare[FAMILY == f].sum() for f in range(4)])
        sy = synth[str(tu)]
        scount = np.array([sy[str(c)]["n"] for c in range(8)], float)
        fam_syn = np.array([scount[FAMILY == f].sum() for f in range(4)]) / scount.sum()
        rep["patterns"] = {NAMES[c]: dict(share=float(share[c]), null_share=float(nshare[c]))
                           for c in range(8)}
        rep["families"] = {FAMILY_NAMES[f]: dict(real=float(fam_real[f]), null=float(fam_null[f]),
                                                 synth=float(fam_syn[f]), rw_theory=float(RW_FAMILY[f]))
                           for f in range(4)}
        # self-test and null P&L (should be ~0)
        for nm, src in (("synth", [sy]), ("null", nl)):
            for rule in ("r1", "r3"):
                n = sum(x[str(c)]["n"] for x in src for c in range(8))
                s = sum(x[str(c)][rule] for x in src for c in range(8))
                sq = sum(x[str(c)][rule + "sq"] for x in src for c in range(8))
                mean = s / n
                sd = np.sqrt(max(sq / n - mean ** 2, 0))
                rep[f"{nm}_{rule}_mean_usd"] = float(mean * U)
                rep[f"{nm}_{rule}_t"] = float(mean / (sd / np.sqrt(n)))
        # ---- Part B: playability per pattern x rule (+ pooled)
        excl = (ev["nymin"] >= 945) & (ev["nymin"] <= 990)
        cells = []
        for rule in ("r1", "r3"):
            for c in list(range(8)) + [-1]:
                m = np.ones(len(code), bool) if c < 0 else code == c
                st = cell_stats(ev[rule][m], day[m], conf[m], yr[m])
                j = judge(st)
                if j is None:
                    continue
                m2 = m & ~excl
                j2 = judge(cell_stats(ev[rule][m2], day[m2], conf[m2], yr[m2]))
                mm = m & conf
                g = (1 if j["side"] == "follow" else -1) * ev[rule][mm]
                j.update(rule=rule, pattern="ALL" if c < 0 else NAMES[c],
                         share=float(m.mean()), trades_per_year=float(mm.sum() / 6),
                         win_net=float(((g - COST_BPS) > 0).mean()),
                         robust_ex1600=bool(j2 and j2["playable"]),
                         net_conf_ex1600=float(j2["net_conf"]) if j2 else None)
                cells.append(j)
        # day-level sign-flip nulls on trade P&L
        ndays = int(day.max() - day.min() + 1)
        null_pass = []
        for _ in range(20):
            fl = rng.choice([-1.0, 1.0], ndays)
            cnt_nr, cnt_pl = 0, 0
            for rule in ("r1", "r3"):
                for c in list(range(8)) + [-1]:
                    m = np.ones(len(code), bool) if c < 0 else code == c
                    j = judge(cell_stats(ev[rule][m], day[m], conf[m], yr[m], fl))
                    if j:
                        cnt_nr += j["nonrandom"]
                        cnt_pl += j["playable"]
            null_pass.append((cnt_nr, cnt_pl))
        rep["cells"] = cells
        rep["null_pass_mean"] = np.mean(null_pass, 0).tolist()
        rep["null_pass_max"] = np.max(null_pass, 0).tolist()
        # extra descriptive: R1 mean gross by pattern, all years, real vs null
        rep["r1_by_pattern"] = {}
        for c in range(8):
            m = code == c
            nn = sum(x[str(c)]["n"] for x in nl)
            rep["r1_by_pattern"][NAMES[c]] = dict(
                real=float(ev["r1"][m].mean() * U), real_t=tstat(ev["r1"][m]),
                null=float(sum(x[str(c)]["r1"] for x in nl) / nn * U))
        report[tu] = rep

        print(f"\n######## theta ${tu} today: {rep['events_per_day']:.0f} swings/day, median leg "
              f"${rep['median_leg_usd']:.2f}, median swing time {rep['median_r1_minutes']:.0f} min")
        print("  family  real% | sign-flip null% | synthetic RW% | RW theory%")
        for f, e in rep["families"].items():
            print(f"   {f:9s} {e['real'] * 100:5.1f} | {e['null'] * 100:5.1f} | {e['synth'] * 100:5.1f}"
                  f" | {e['rw_theory'] * 100:5.1f}")
        print("  patterns real% (null%):", "  ".join(
            f"{k} {e['share'] * 100:.1f} ({e['null_share'] * 100:.1f})"
            for k, e in rep["patterns"].items()))
        print(f"  checks: synth R1 mean ${rep['synth_r1_mean_usd']:+.4f} (t {rep['synth_r1_t']:+.1f}), "
              f"R3 ${rep['synth_r3_mean_usd']:+.4f} (t {rep['synth_r3_t']:+.1f}); null R1 "
              f"${rep['null_r1_mean_usd']:+.4f} (t {rep['null_r1_t']:+.1f}), R3 "
              f"${rep['null_r3_mean_usd']:+.4f} (t {rep['null_r3_t']:+.1f})")
        print("  R1 follow gross by pattern, all years, $ (t) [null $]:", "  ".join(
            f"{k} {e['real']:+.3f} ({e['real_t']:+.1f}) [{e['null']:+.3f}]"
            for k, e in rep["r1_by_pattern"].items()))
        print(f"  Part B: null passes mean {rep['null_pass_mean']} max {rep['null_pass_max']}")
        for j in cells:
            if j["nonrandom"] or j["pattern"] == "ALL":
                print(f"   {j['rule']} {j['pattern']:16s} {j['side']:6s} share {j['share'] * 100:4.1f}% "
                      f"| disc ${j['E_disc']:+.3f} (t {j['t_disc']:+.1f}) conf ${j['E_conf']:+.3f} "
                      f"(t {j['t_conf']:+.1f}) | net ${j['net_conf']:+.3f} win {j['win_net'] * 100:.0f}% "
                      f"{j['trades_per_year']:.0f}/yr yrs+ {j['years_pos']} | "
                      f"{'NONRANDOM ' if j['nonrandom'] else ''}{'PLAYABLE ' if j['playable'] else ''}"
                      f"{'ROBUST' if j['robust_ex1600'] else ''}")
    with open(OUT / "REPORT.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, default=float)


if __name__ == "__main__":
    main()
