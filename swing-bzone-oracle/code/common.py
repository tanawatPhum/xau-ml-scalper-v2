"""Shared loaders, sigma unit and the tradable SELL state machine (see ../PLAN.md, v2)."""
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ROOT = Path(__file__).resolve().parents[1]
BIDC = ROOT.parent / "swing-bzone" / "cache"
B68 = Path(r"C:\Users\ASUS\Documents\Codex\2026-10-30\task-6\deliverables\e68-a2-2011-2022")
SPREAD, OZ, FX = 0.168, 10, 33.77
PRE = 120
COLS = ["k", "ipk", "itr", "ifill", "iexit", "P", "T", "X", "TP", "SL", "exitp", "oc", "u"]


def load_sessions(years):
    ev = pd.read_csv(B68 / "EVENTS.private.csv.gz")
    ev = ev[(ev["status"] == "ISSUED") & ev["year"].isin(years)]
    zn = pd.read_csv(B68 / "SELECTED_ZONES.private.csv.gz")
    zn = zn[zn["delivered"] & zn["year"].isin(years)]
    zones = {k: g[["lower", "upper"]].to_numpy(float) for k, g in zn.groupby("event_key")}
    ev = ev[ev["event_key"].isin(zones)].sort_values("lock_minute").reset_index(drop=True)
    H, L, C, so, sw, se, meta = [], [], [], [], [], [], []
    off = 0
    for yr, g in ev.groupby("year"):
        b = np.load(BIDC / f"BID_{yr}.private.npz")
        base = int(b["base"])
        h, l, c = b["high"], b["low"], b["close"]
        for row in g.itertuples():
            a0, a1 = int(row.lock_minute) - base, min(int(row.end_minute) - base, len(c))
            p0 = max(a0 - PRE, 0)
            H.append(h[p0:a1]); L.append(l[p0:a1]); C.append(c[p0:a1])
            so.append(off); sw.append(off + a0 - p0); se.append(off + a1 - p0)
            off += a1 - p0
            meta.append(dict(key=row.event_key, yr=int(yr), lock=int(row.lock_minute), session=row.event_key.split("|")[1],
                             span=int(row.end_minute - row.lock_minute)))
    S = dict(H=np.concatenate(H), L=np.concatenate(L), C=np.concatenate(C), so=np.array(so, np.int64), sw=np.array(sw, np.int64),
             se=np.array(se, np.int64), meta=pd.DataFrame(meta), zones=zones)
    S["U"] = sig_all(S["C"], S["so"], S["se"])
    return S


@njit(cache=True)
def sig_all(C, so, se):
    """u[t] = last close before t x sqrt(60 x mean r^2 of the last 60 returns before t) (>= 30), per segment."""
    U = np.full(len(C), np.nan)
    buf = np.zeros(60)
    for k in range(len(so)):
        cnt = 0
        kk = 0
        s = 0.0
        last = np.nan
        for t in range(so[k], se[k]):
            if cnt >= 30 and s > 0:
                U[t] = last * np.sqrt(60.0 * s / cnt)
            c = C[t]
            if c == c:
                if last == last:
                    r = np.log(c / last)
                    r2 = r * r
                    if cnt < 60:
                        buf[cnt] = r2
                        s += r2
                        cnt += 1
                    else:
                        s += r2 - buf[kk]
                        buf[kk] = r2
                        kk = (kk + 1) % 60
                last = c
    return U


@njit(cache=True)
def run_cell(H, L, C, U, so, sw, se, sel, rho, m, r, q, s, out):
    nt = 0
    for k in range(len(sw)):
        if not sel[k]:
            continue
        a, b = sw[k], se[k]
        cprev = np.nan
        for j in range(a - 1, so[k] - 1, -1):
            if C[j] == C[j]:
                cprev = C[j]
                break
        mode = 0
        Hs = -1e18
        ih = -1
        P = 0.0
        T = 0.0
        itr = -1
        up = 0.0
        ipk = -1
        t = a
        while t < b:
            h = H[t]
            l = L[t]
            if not (h == h):
                t += 1
                continue
            if mode == 0:
                uu = U[t]
                if ih >= 0 and h <= Hs and uu == uu and uu > 0 and l <= Hs - rho * uu:
                    mode = 1
                    P = Hs
                    ipk = ih
                    T = l
                    itr = t
                    up = uu
                elif h > Hs:
                    Hs = h
                    ih = t
            else:
                if h > P:
                    mode = 0
                    Hs = h
                    ih = t
                else:
                    run = P - T
                    lvl = T + r * run
                    if run >= m * up and h >= lvl and l >= T:
                        X = lvl
                        if cprev == cprev and cprev > X:
                            X = cprev
                        TPp = T + q * run
                        SLp = P + s * run
                        ex = -1
                        ep = 0.0
                        oc = 0
                        if h >= SLp:
                            ex = t
                            ep = SLp
                            oc = -1
                        else:
                            lastc = C[t]
                            lastj = t
                            j = t + 1
                            while j < b:
                                if H[j] == H[j]:
                                    if H[j] >= SLp:
                                        ex = j
                                        ep = SLp
                                        oc = -1
                                        break
                                    if L[j] <= TPp:
                                        ex = j
                                        ep = TPp
                                        oc = 1
                                        break
                                    lastc = C[j]
                                    lastj = j
                                j += 1
                            if ex < 0:
                                ex = lastj
                                ep = lastc
                                oc = 0
                        out[nt, 0] = k
                        out[nt, 1] = ipk
                        out[nt, 2] = itr
                        out[nt, 3] = t
                        out[nt, 4] = ex
                        out[nt, 5] = P
                        out[nt, 6] = T
                        out[nt, 7] = X
                        out[nt, 8] = TPp
                        out[nt, 9] = SLp
                        out[nt, 10] = ep
                        out[nt, 11] = oc
                        out[nt, 12] = up
                        nt += 1
                        if C[ex] == C[ex]:
                            cprev = C[ex]
                        t = ex + 1
                        mode = 0
                        Hs = -1e18
                        ih = -1
                        continue
                    if l < T:
                        T = l
                        itr = t
            if C[t] == C[t]:
                cprev = C[t]
            t += 1
    return nt


def trades(S, sel, rho, m, r, q, s, H=None, L=None, C=None, U=None):
    H = S["H"] if H is None else H
    L = S["L"] if L is None else L
    C = S["C"] if C is None else C
    U = S["U"] if U is None else U
    out = np.zeros((int(sel.sum()) * 40 + 10, len(COLS)))
    n = run_cell(H, L, C, U, S["so"], S["sw"], S["se"], sel, rho, m, r, q, s, out)
    D = pd.DataFrame(out[:n], columns=COLS)
    for c in ("k", "ipk", "itr", "ifill", "iexit", "oc"):
        D[c] = D[c].astype(np.int64)
    M = S["meta"]
    D["yr"] = M["yr"].to_numpy()[D["k"]]
    D["session"] = M["session"].to_numpy()[D["k"]]
    D["day"] = (M["lock"].to_numpy()[D["k"]] + 3 * 60) // 1440
    D["t_fill"] = M["lock"].to_numpy()[D["k"]] + D["ifill"] - S["sw"][D["k"]]
    D["t_exit"] = M["lock"].to_numpy()[D["k"]] + D["iexit"] - S["sw"][D["k"]]
    D["gross"] = D["X"] - D["exitp"]
    D["net"] = D["gross"] - SPREAD
    D["p0"] = (D["SL"] - D["X"]) / (D["SL"] - D["TP"])
    return D


def ct(x, day):
    x, day = np.asarray(x, float), np.asarray(day)
    if len(x) < 3:
        return float(np.mean(x)) if len(x) else 0.0, np.inf
    u, inv = np.unique(day, return_inverse=True)
    if len(u) < 3:
        return float(x.mean()), np.inf
    Ssum, N = np.bincount(inv, weights=x), np.bincount(inv)
    mu = Ssum.sum() / N.sum()
    se = np.sqrt(((Ssum - mu * N) ** 2).sum() * len(u) / (len(u) - 1)) / N.sum()
    return float(mu), float(se)


def permute(S, rng):
    H, L, C = S["H"].copy(), S["L"].copy(), S["C"].copy()
    for o, a, b in zip(S["so"], S["sw"], S["se"]):
        v = np.flatnonzero(np.isfinite(S["C"][a:b]) & np.isfinite(S["H"][a:b])) + a
        if len(v) < 3:
            continue
        pre = np.flatnonzero(np.isfinite(S["C"][o:a]))
        anchor = S["C"][o + pre[-1]] if len(pre) else S["C"][v[0]]
        prevc = np.r_[anchor, S["C"][v[:-1]]]
        dh, dl, dc = S["H"][v] - prevc, S["L"][v] - prevc, S["C"][v] - prevc
        p = rng.permutation(len(v))
        nc = anchor + np.cumsum(dc[p])
        npv = np.r_[anchor, nc[:-1]]
        H[v], L[v], C[v] = npv + dh[p], npv + dl[p], nc
    return H, L, C, sig_all(C, S["so"], S["se"])


def zone_flag(D, S, tol=0.5):
    keys = S["meta"]["key"].to_numpy()
    z = np.zeros(len(D), bool)
    for i, (k, P, T) in enumerate(zip(D["k"].to_numpy(), D["P"].to_numpy(), D["T"].to_numpy())):
        Z = S["zones"][keys[k]]
        for a in np.flatnonzero((P >= Z[:, 0] - tol) & (P <= Z[:, 1] + tol)):
            if np.any((Z[:, 1] < Z[a, 0]) & (T <= Z[:, 1] + tol)):
                z[i] = True
                break
    return z


def add_factors(D, S):
    D = D.copy()
    D["Z"] = zone_flag(D, S)
    D["run_u"] = (D["P"] - D["T"]) / D["u"]
    D["speed"] = D["run_u"] / np.maximum(D["itr"] - D["ipk"], 1)
    D["bounce_min"] = D["ifill"] - D["itr"]
    return D
