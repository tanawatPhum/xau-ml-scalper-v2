"""Post-hoc robustness of the playable fade cells (labelled; pre-registered verdicts unchanged).
1. Delayed execution: entry and exit 1 or 2 minutes after the decision close.
2. BID-only and ASK-only price series instead of mid.
3. Events in the wide-spread rollover window (NY 16:30-19:30) removed.
4. Loss tail of the fade trades."""

import numpy as np

from swing import (COST_BPS, EDGE_CACHE, NAMES, THETA_BPS, THETA_USD, USD_PER_BPS, YEARS,
                   ny_clock, process)

U = USD_PER_BPS
CELLS = [(3, "EXPAND deep"), (5, "COUNTER deep"), (5, "EXPAND mild")]
GROUPS = {"EXPAND (both)": [6, 7], "COUNTER deep": [5], "EXPAND deep": [7], "EXPAND mild": [6],
          "ALL patterns": list(range(8))}


def series(yr, kind):
    z = np.load(EDGE_CACHE / f"M1_{yr}.private.npz")
    base = int(z["base"])
    bid, ask = z["bid"], z["ask"]
    mid = (bid + ask) / 2
    pos = np.flatnonzero(np.isfinite(mid))
    px = {"mid": mid, "bid": bid, "ask": ask}[kind][pos]
    y = 1e4 * np.log(px)
    mins = (base + pos).astype(np.int64)
    blk = np.r_[0, np.cumsum(np.diff(pos) > 30)].astype(np.int64)
    sp = (ask - bid)[pos] / mid[pos] * 1e4
    return y, mins, blk, sp


def fade_trades(y, mins, blk, theta, delay):
    ev = process(y, mins, blk, theta)
    idx, eb = ev["idx"], blk[ev["idx"]]
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), len(y) - 1]
    nxt = np.r_[idx[1:], -1]
    same = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same, nxt, last_of_blk[eb])
    ent = np.minimum(idx + delay, len(y) - 1)
    ok = blk[ent] == eb
    ex = np.minimum(exit_i + delay, len(y) - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    pnl = -ev["dir"] * (y[ex] - y[ent]) - COST_BPS  # fade, net, in bps
    return ev, pnl, ok


def summarize(label, pnl, yr):
    out = []
    for per, m in (("2010-16", yr <= 2016), ("2017-22", yr >= 2017)):
        x = pnl[m] * U
        t = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else 0
        out.append(f"{per} net ${x.mean():+.3f} (t {t:+.1f}, n {len(x)})")
    yrs = sum(1 for y in range(2017, 2023) if (pnl[yr == y].mean() if (yr == y).any() else -1) > 0)
    print(f"    {label:34s} " + " | ".join(out) + f" | 2017-22 years net>0: {yrs}/6")


for tu, th in zip(THETA_USD, THETA_BPS, strict=True):
    if tu not in (3, 5, 10):
        continue
    print(f"\n######## theta ${tu}")
    for kind in ("mid", "bid", "ask"):
        for delay in ((0, 1, 2) if kind == "mid" else (0,)):
            P, C, Y, NM = [], [], [], []
            for yr in YEARS:
                y, mins, blk, sp = series(yr, kind)
                ev, pnl, ok = fade_trades(y, mins, blk, th, delay)
                _, nymin = ny_clock(ev["mins"])
                P.append(pnl[ok])
                C.append(ev["code"][ok])
                Y.append(np.full(ok.sum(), yr))
                NM.append(nymin[ok])
            P, C, Y, NM = map(np.concatenate, (P, C, Y, NM))
            print(f"  [{kind} prices, execution delay {delay} min]")
            for g, codes in GROUPS.items():
                m = np.isin(C, codes)
                summarize(g, P[m], Y[m])
            if kind == "mid" and delay == 0:
                roll = (NM >= 990) & (NM < 1170)
                print("  [mid, delay 0, rollover window NY 16:30-19:30 removed]")
                for g, codes in GROUPS.items():
                    m = np.isin(C, codes) & ~roll
                    summarize(g, P[m], Y[m])
                for ttu, name in CELLS:
                    if ttu != tu:
                        continue
                    m = (C == NAMES.index(name)) & (Y >= 2017)
                    x = P[m] * U
                    q = np.quantile(x, [0.01, 0.05, 0.5, 0.95, 0.99])
                    srt = np.sort(x)[::-1]
                    top = srt[: max(1, len(x) // 20)].sum() / x.sum() if x.sum() > 0 else np.nan
                    print(f"  loss tail {name} 2017-22: p1 {q[0]:+.2f} p5 {q[1]:+.2f} median "
                          f"{q[2]:+.2f} p95 {q[3]:+.2f} p99 {q[4]:+.2f} worst {x.min():+.2f} | "
                          f"best 5% trades = {top * 100:.0f}% of total net")
