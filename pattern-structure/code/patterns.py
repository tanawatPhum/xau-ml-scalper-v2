"""Pattern-structure library (see PLAN.md)."""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EDGE_CACHE = ROOT.parent / "microstructure-edge-map" / "cache"  # read-only reuse
CACHE = ROOT / "cache"
OUT = ROOT / "out"
YEARS = list(range(2010, 2023))
OWNER_BPS = 0.168 / 4083.276 * 1e4
LETTERS = "DFU"  # state codes 0, 1, 2
NAMES = [a + b + c for a in LETTERS for b in LETTERS for c in LETTERS]
PREFIXES = [a + b for a in LETTERS for b in LETTERS]


def family(name):
    moves = [c for c in name if c != "F"]
    if not moves:
        return "QUIET"
    if len(moves) == 1:
        return "IMPULSE"
    changes = sum(1 for a, b in zip(moves, moves[1:], strict=False) if a != b)
    if changes == 0:
        return "TREND"
    return "REVERSAL" if changes == 1 else "WHIPSAW"


FAMILIES = ["QUIET", "IMPULSE", "TREND", "REVERSAL", "WHIPSAW"]
FAM_OF_CODE = np.array([FAMILIES.index(family(n)) for n in NAMES])


def load_year(yr):
    z = np.load(EDGE_CACHE / f"M1_{yr}.private.npz")
    bid, ask = z["bid"], z["ask"]
    return int(z["base"]), bid, ask, (bid + ask) / 2


def s60(bid):
    d = np.diff(bid)
    ok = np.isfinite(d)
    d2 = np.r_[0.0, np.where(ok, d * d, 0.0)]
    pc = np.r_[0, ok.astype(np.int64)]
    c2, cp = np.cumsum(d2), np.cumsum(pc)
    n = len(bid)
    out = np.full(n, np.nan)
    i = np.arange(61, n)
    ssum = c2[i - 1] - c2[i - 60]
    psum = cp[i - 1] - cp[i - 60]
    out[i] = np.where(psum >= 50, np.sqrt(ssum), np.nan)
    return out


def ny_clock(base, n):
    t = pd.to_datetime((base + np.arange(n)) * 60, unit="s", utc=True).tz_convert(
        "America/New_York")
    return t.hour.to_numpy(), t.minute.to_numpy()


def states(moves, sig, theta):
    return np.where(moves >= theta * sig, 2, np.where(moves <= -theta * sig, 0, 1)).astype(np.int8)


def build_triples(base, bid, ask, mid, L, nshuf, rng, theta=0.5, null_kind="perm"):
    """All valid consecutive 3-segment windows of a year (dense minute arrays).
    null_kind 'perm': minute returns permuted within the window (pre-registered null).
    null_kind 'sign': minute returns keep their order and size, signs flipped at random
    (post-hoc diagnostic: keeps volatility timing, removes direction dependence)."""
    n = len(mid)
    valid = np.isfinite(mid)
    idx = np.maximum.accumulate(np.where(valid, np.arange(n), -1))
    mf = np.where(idx >= 0, mid[np.maximum(idx, 0)], np.nan)
    r = np.zeros(n)
    r[1:] = np.diff(mf)
    r[~np.isfinite(r)] = 0.0
    ctr = np.r_[0, np.cumsum(valid)]
    s = s60(bid)
    hr, mn = ny_clock(base, n)
    start = (-base) % L
    B = np.arange(start, n - 3 * L - 1, L)
    B = B[B >= 61]

    def price_ok(b):
        j = idx[b - 1]
        return (j >= 0) & ((b - 1 - j) <= 2)

    seg_ok = price_ok(B) & price_ok(B + L) & ((ctr[B + L] - ctr[B]) >= 0.9 * L) & \
        np.isfinite(s[B])
    move = mf[B + L - 1] - mf[B - 1]
    sig = s[B] * np.sqrt(L / 60)
    tri = seg_ok[:-2] & seg_ok[1:-1] & seg_ok[2:]
    j = np.flatnonzero(tri)
    t = B[j + 2]
    M = np.stack([move[j], move[j + 1], move[j + 2]], 1)
    SG = np.stack([sig[j], sig[j + 1], sig[j + 2]], 1)
    R = r[B[j][:, None] + np.arange(3 * L)]
    assert np.allclose(R.reshape(-1, 3, L).sum(2), M, atol=1e-6)
    null = np.empty((len(j), nshuf), np.int8)
    for k in range(nshuf):
        if null_kind == "sign":
            Rs = (R * rng.choice([-1.0, 1.0], R.shape)).reshape(-1, 3, L).sum(2)
        else:
            perm = np.argsort(rng.random(R.shape), axis=1)
            Rs = np.take_along_axis(R, perm, 1).reshape(-1, 3, L).sum(2)
        st = states(Rs, SG, theta)
        null[:, k] = 9 * st[:, 0] + 3 * st[:, 1] + st[:, 2]
    sp = ask - bid
    return dict(
        day=(base + t) // 1440, nyh=hr[t], nymin=hr[t] * 60 + mn[t],
        m1=M[:, 0], m2=M[:, 1], m3=M[:, 2], sig1=SG[:, 0], sig2=SG[:, 1], sig3=SG[:, 2],
        mid_t=mf[t - 1], sp_t=sp[idx[t - 1]], sp_tL=sp[idx[t + L - 1]], null=null)
