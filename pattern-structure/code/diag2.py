"""Post-hoc follow-up: does the prefix edge clear the owner's fixed cost in high volatility?
Cells = prefix (9) x S60 tercile at decision time (cuts from 2010-2016), NY hour 16 excluded.
Same rules as Part B (discovery 2010-16 |t|>=3, confirmation same sign t>=2, playable if
confirmation gross > owner cost and net > 0 in >= 4/6 years) and 20 day-level sign-flip nulls."""

import json

import numpy as np
import pandas as pd

from analysis import cell_table
from patterns import CACHE, OUT, OWNER_BPS, PREFIXES, states

rng = np.random.default_rng(5)
rep = {}
for L in (5, 10, 20):
    z = np.load(CACHE / f"TRIPLES_L{L}.private.npz")
    keep = z["nyh"] != 16
    d = {k: z[k][keep] for k in z.files}
    st = states(np.stack([d["m1"], d["m2"], d["m3"]], 1),
                np.stack([d["sig1"], d["sig2"], d["sig3"]], 1), 0.5)
    pre = (3 * st[:, 0] + st[:, 1]).astype(int)
    yr, day, m3 = d["yr"], d["day"], d["m3"]
    S = d["sig3"] / np.sqrt(L / 60)
    cuts = np.quantile(S[yr <= 2016], [1 / 3, 2 / 3])
    terc = np.searchsorted(cuts, S)
    key = pre * 3 + terc
    conf = yr >= 2017
    oc = pd.Series((OWNER_BPS * d["mid_t"] / 1e4)[conf]).groupby(key[conf]).median()

    def evaluate(flip):
        a, yy = cell_table(key, day, yr, m3, conf, flip)
        out = []
        for c in np.unique(key):
            ad, ac = a.loc[(0, c)], a.loc[(1, c)]
            s = np.sign(ad.E)
            nonrand = abs(ad.t) >= 3 and s * ac.t >= 2
            ye = yy.loc[c].E
            ypos = int(((s * ye) - oc[c] > 0).sum())
            out.append(dict(cell=int(c), prefix=PREFIXES[c // 3], tercile=int(c % 3),
                            E_disc=float(ad.E), t_disc=float(ad.t), E_conf=float(ac.E),
                            t_conf=float(ac.t), n_conf=int(ac.n), gross=float(s * ac.E),
                            owner=float(oc[c]), years_pos=ypos, nonrandom=bool(nonrand),
                            playable=bool(nonrand and s * ac.E > oc[c] and ypos >= 4)))
        return out

    real = evaluate(None)
    ndays = int(day.max() - day.min() + 1)
    nulls = [(sum(x["nonrandom"] for x in r), sum(x["playable"] for x in r))
             for r in (evaluate(rng.choice([-1.0, 1.0], ndays)) for _ in range(20))]
    rep[L] = dict(cells=real, null_mean=np.mean(nulls, 0).tolist(),
                  null_max=np.max(nulls, 0).tolist(), cuts=cuts.tolist())
    print(f"\nL {L} (NY16 excluded): S60 tercile cuts {np.round(cuts, 2)}; non-random "
          f"{sum(x['nonrandom'] for x in real)}, playable {sum(x['playable'] for x in real)} "
          f"| null mean {np.round(np.mean(nulls, 0), 2).tolist()} max {np.max(nulls, 0).tolist()}")
    for x in real:
        if x["nonrandom"] or x["prefix"] in ("UU", "DD"):
            print(f"  {x['prefix']} vol{x['tercile']}: E disc {x['E_disc']:+.4f} (t {x['t_disc']:+.1f})"
                  f" conf {x['E_conf']:+.4f} (t {x['t_conf']:+.1f}, n {x['n_conf']}) gross "
                  f"{x['gross']:.4f} vs owner {x['owner']:.3f} yrs+ {x['years_pos']} "
                  f"{'NONRANDOM' if x['nonrandom'] else ''} {'PLAYABLE' if x['playable'] else ''}")
with open(OUT / "DIAG2.json", "w", encoding="utf-8") as f:
    json.dump(rep, f, indent=1)
