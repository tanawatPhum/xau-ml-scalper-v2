"""Descriptive: the owner-scale cells (run >= 1.5u, re-test of the trough) on 2011-16, zone vs not."""
import numpy as np
import pandas as pd

from common import FX, OZ, ROOT, ct, load_sessions, trades, zone_flag

G = pd.read_csv(ROOT / "out" / "GRID_2011_16.csv")
print(G[(G["rho"] == 0.5) & (G["m"] == 1.5) & (G["q"] == 0.0)][["r", "s", "n", "per_day", "net", "t", "gross", "win", "loss", "none"]].round(3).to_string(index=False))
S = load_sessions(list(range(2011, 2017)))
sel = np.ones(len(S["meta"]), bool)
for cell in ((0.5, 1.5, 0.382, 0.0, 0.25), (0.5, 1.5, 0.5, 0.0, 0.25)):
    D = trades(S, sel, *cell)
    for tol in (0.5, 0.0):
        z = zone_flag(D, S, tol)
        for name, x in (("zone", D[z]), ("not zone", D[~z])):
            mu, se = ct(x["net"], x["day"])
            print(cell, f"tol {tol} {name}: n {len(x)} net {mu:+.3f} (t {mu / se:+.2f}) TP {100 * (x['oc'] == 1).mean():.0f}% "
                  f"SL {100 * (x['oc'] == -1).mean():.0f}% THB/yr {x['net'].sum() * OZ * FX / 6:+,.0f}")
