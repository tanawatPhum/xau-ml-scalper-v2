"""Hindsight oracle count of zone-to-zone run + small bounce + continuation (see ../PLAN.md)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BIDC = ROOT.parent / "swing-bzone" / "cache"
B68 = Path(r"C:\Users\ASUS\Documents\Codex\2026-10-30\task-6\deliverables\e68-a2-2011-2022")
YEARS = list(range(2011, 2017))
CUSH, MINB, SPREAD, OZ, FX = 0.50, 0.20, 0.168, 10, 33.77

ev = pd.read_csv(B68 / "EVENTS.private.csv.gz")
ev = ev[(ev["status"] == "ISSUED") & ev["year"].isin(YEARS)]
zn = pd.read_csv(B68 / "SELECTED_ZONES.private.csv.gz")
zn = zn[zn["delivered"] & zn["year"].isin(YEARS)]
ZS = {k: g[["lower", "upper"]].to_numpy() for k, g in zn.groupby("event_key")}
bid = {yr: np.load(BIDC / f"BID_{yr}.private.npz") for yr in YEARS}

rows, sessions = [], 0
for _, e in ev.iterrows():
    key = e["event_key"]
    if key not in ZS:
        continue
    yr = int(key[:4])
    b = bid[yr]
    base = int(b["base"])
    lo_m, hi_m = int(e["lock_minute"]) - base, int(e["end_minute"]) - base
    if lo_m < 0 or hi_m > len(b["high"]):
        continue
    H, L = b["high"][lo_m:hi_m], b["low"][lo_m:hi_m]
    Z = ZS[key]
    ctr = Z.mean(axis=1)
    sessions += 1
    last = -1
    arrivals = []
    for t in range(len(H)):
        if not np.isfinite(H[t]):
            continue
        touched = np.flatnonzero((H[t] >= Z[:, 0]) & (L[t] <= Z[:, 1]))
        if len(touched) == 0:
            continue
        if last < 0:
            last = int(touched[0])
            continue
        new = touched[touched != last]
        if len(new):
            z = int(new[np.argmax(np.abs(ctr[new] - ctr[last]))])
            arrivals.append((last, z, t))
            last = z
    for a, bz, tb in arrivals:
        down = ctr[bz] < ctr[a]
        out, tc = "none", None
        for t in range(tb + 1, len(H)):
            if not np.isfinite(H[t]):
                continue
            if down:
                if L[t] <= Z[bz, 0] - CUSH:
                    out, tc = "continue", t
                    break
                if H[t] >= Z[a, 0]:
                    out = "reverse"
                    break
            else:
                if H[t] >= Z[bz, 1] + CUSH:
                    out, tc = "continue", t
                    break
                if L[t] <= Z[a, 1]:
                    out = "reverse"
                    break
        r = dict(key=key, yr=yr, session=key.split("|")[1], down=bool(down), outcome=out, pattern=False,
                 gap=float(abs(ctr[bz] - ctr[a])))
        if out == "continue":
            seg = slice(tb, tc + 1)
            if down:
                th = tb + int(np.nanargmax(H[seg]))
                top = H[th]
                bounce = top - np.nanmin(L[tb:th + 1])
                ok = th > tb and bounce >= MINB
                lvl = Z[bz, 0] - CUSH
                tp_profit = top - lvl
                after = np.arange(th + 1, len(H))
                stop_hit = after[np.isfinite(H[after]) & (H[after] > top)]
                end = stop_hit[0] if len(stop_hit) else len(H)
                best = np.nanmin(L[th + 1:end]) if end > th + 1 else top
                max_profit = top - best
            else:
                th = tb + int(np.nanargmin(L[seg]))
                top = L[th]
                bounce = np.nanmax(H[tb:th + 1]) - top
                ok = th > tb and bounce >= MINB
                lvl = Z[bz, 1] + CUSH
                tp_profit = lvl - top
                after = np.arange(th + 1, len(L))
                stop_hit = after[np.isfinite(L[after]) & (L[after] < top)]
                end = stop_hit[0] if len(stop_hit) else len(L)
                best = np.nanmax(H[th + 1:end]) if end > th + 1 else top
                max_profit = best - top
            r.update(pattern=bool(ok), bounce=float(bounce), tp_profit=float(tp_profit), max_profit=float(max_profit),
                     wait_min=int(th - tb))
        rows.append(r)

D = pd.DataFrame(rows)
D.to_pickle(ROOT / "out" / "ARRIVALS.private.pkl")
days = D["key"].str[:10].nunique()
P = D[D["pattern"]]
toth = lambda s: (s - SPREAD) * OZ * FX  # noqa: E731
summary = dict(sessions=sessions, trading_days_with_sessions=int(days), arrivals=len(D),
               arrivals_per_session=len(D) / sessions, outcome_share=D["outcome"].value_counts(normalize=True).round(3).to_dict(),
               pattern=len(P), pattern_per_session=len(P) / sessions, pattern_per_day=len(P) / days,
               bounce_usd=P["bounce"].describe(percentiles=[.1, .5, .9]).round(2).to_dict(),
               tp_profit_usd=P["tp_profit"].describe(percentiles=[.1, .5, .9]).round(2).to_dict(),
               max_profit_usd=P["max_profit"].describe(percentiles=[.1, .5, .9]).round(2).to_dict(),
               wait_min=P["wait_min"].describe(percentiles=[.1, .5, .9]).round(1).to_dict())
yearly = {}
for yr in YEARS:
    p = P[P["yr"] == yr]
    d = D[D["yr"] == yr]
    yearly[yr] = dict(sessions=int(d["key"].nunique()), arrivals=len(d), cont=int((d.outcome == "continue").sum()),
                      rev=int((d.outcome == "reverse").sum()), pattern=len(p),
                      thb_tp=float(toth(p["tp_profit"]).sum()), thb_max=float(toth(p["max_profit"]).sum()))
by_session = D.groupby("session").agg(arrivals=("outcome", "size"), cont=("outcome", lambda s: (s == "continue").mean()),
                                      rev=("outcome", lambda s: (s == "reverse").mean()), pattern=("pattern", "sum")).round(3)
json.dump(dict(summary=summary, yearly=yearly, by_session=by_session.to_dict()), open(ROOT / "out" / "ORACLE.json", "w"), indent=1, default=float)
print(json.dumps(summary, indent=1, default=float))
print("year | sessions | arrivals | continue | reverse | pattern | oracle-TP THB (0.1 lot) | oracle-max THB")
for yr, r in yearly.items():
    print(f"{yr} | {r['sessions']} | {r['arrivals']} | {r['cont']} | {r['rev']} | {r['pattern']} | {r['thb_tp']:+,.0f} | {r['thb_max']:+,.0f}")
print(by_session.to_string())
