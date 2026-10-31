"""Build triples per segment length L for 2010-2022 (and a synthetic random-walk self-test)."""

import sys

import numpy as np

from patterns import CACHE, YEARS, build_triples, load_year

LS = (5, 10, 20)
NSHUF = 10


def run_real():
    rng = np.random.default_rng(20261031)
    for L in LS:
        parts = []
        for yr in YEARS:
            base, bid, ask, mid = load_year(yr)
            d = build_triples(base, bid, ask, mid, L, NSHUF, rng)
            d["yr"] = np.full(len(d["m1"]), yr)
            parts.append(d)
        out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
        np.savez_compressed(CACHE / f"TRIPLES_L{L}.private.npz", **out)
        print("L", L, "triples", len(out["m1"]), flush=True)


def run_synthetic():
    """Gaussian random walk on the real 2017 trading calendar, constant per-minute sigma."""
    rng = np.random.default_rng(7)
    base, bid, ask, mid = load_year(2017)
    valid = np.isfinite(mid)
    sd = float(np.nanstd(np.diff(mid)))
    walk = 1250 + np.cumsum(rng.normal(0, sd, len(mid)))
    m = np.where(valid, walk, np.nan)
    for L in LS:
        d = build_triples(base, m - 0.15, m + 0.15, m, L, NSHUF, rng)
        d["yr"] = np.full(len(d["m1"]), 2017)
        np.savez_compressed(CACHE / f"SYNTH_L{L}.private.npz", **d)
        print("synthetic L", L, "triples", len(d["m1"]), flush=True)


if __name__ == "__main__":
    if "synth" in sys.argv:
        run_synthetic()
    else:
        run_real()
