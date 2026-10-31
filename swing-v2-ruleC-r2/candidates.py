"""Rule C round 2 candidates (see PLAN.md): R1 fade the extended leg, R3 fade big moves into scheduled times.
Audit-engine data and volatility (read-only import), Exness schedule, fills at the next minute close. 2010-2022 built;
selection reads 2010-16 only. Output out/C2_TRADES.private.csv."""
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "swing-causal-execution"))
import engine as E  # noqa: E402
from run import DEFAULT_CACHE, load_prices  # noqa: E402

TH_MIN = 2.1626934441569983
mins, bid, ask = load_prices(DEFAULT_CACHE, list(range(2010, 2023)), allow_2020_2022=True)
mid = (bid + ask) / 2
y = 1e4 * np.log(mid)
n = len(mins)
ny = pd.to_datetime(mins * 60, unit="s", utc=True).tz_convert("America/New_York")
mod = (ny.hour * 60 + ny.minute).to_numpy()
dow = ny.dayofweek.to_numpy()
blocked = (mod >= 16 * 60 + 55) & (mod < 18 * 60 + 1)
blocked |= (dow == 6) & (mod >= 18 * 60) & (mod < 18 * 60 + 5)
gap_next = np.r_[np.diff(mins) > 30, True]
nxt_gap = pd.Series(np.where(gap_next, mins, np.nan)).bfill().to_numpy()
blocked |= (nxt_gap - mins) <= 4
cut = np.where(blocked, np.arange(n), n - 1)
cut = np.minimum.accumulate(cut[::-1])[::-1]
s60, sl = E.volatility(mins, mid)
eff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
TH = {"A": 1.0 * eff, "B": 1.5 * s60}


@nb.njit(cache=True)
def r1(mins, y, mid, th, blocked, m, s, th_min, out):
    n = len(y)
    k = 0
    mode = 0
    hi = lo = 0.0
    hi_i = lo_i = 0
    leg_dir = 0
    leg_ext = 0.0
    trig = False
    pos = 0.0
    e_i = -1
    pth = 0.0
    pend_e = -1
    pend_dir = 0.0
    pend_th = 0.0
    pend_x = 0
    for i in range(n):
        gap = i == 0 or mins[i] - mins[i - 1] > 30
        # fills at this close
        if pos != 0.0 and (gap or blocked[i] or pend_x > 0):
            reason = 3 if gap else (4 if blocked[i] else pend_x)
            out[k, 0] = mins[e_i]
            out[k, 1] = mins[i]
            out[k, 2] = pos
            out[k, 3] = pos * (mid[i] - mid[e_i]) - 0.168
            out[k, 4] = pth * mid[e_i] / 1e4
            out[k, 5] = reason
            k += 1
            pos = 0.0
        pend_x = 0
        if pend_e >= 0:
            if pos == 0.0 and not gap and not blocked[i] and mins[i] == mins[pend_e] + 1:
                pos = pend_dir
                e_i = i
                pth = pend_th
            pend_e = -1
        # zigzag at this close (same state machine as the audit engine)
        if gap:
            hi = lo = y[i]
            hi_i = lo_i = i
            mode = 0
            leg_dir = 0
            trig = True
            continue
        v = y[i]
        t = th[i]
        live = (t == t) and t > 0
        direction = 0
        extreme = 0.0
        if mode == 0:
            if v > hi:
                hi, hi_i = v, i
            if v < lo:
                lo, lo_i = v, i
            if live and v - lo >= t and lo_i < i:
                direction, extreme = 1, lo
            elif live and hi - v >= t and hi_i < i:
                direction, extreme = -1, hi
        elif mode == 1:
            if v > hi:
                hi, hi_i = v, i
            elif live and hi - v >= t:
                direction, extreme = -1, hi
        else:
            if v < lo:
                lo, lo_i = v, i
            elif live and v - lo >= t:
                direction, extreme = 1, lo
        if direction != 0:
            if pos != 0.0:
                pend_x = 1  # the faded leg has pulled back: exit at the next close
            mode = direction
            if direction == 1:
                hi, hi_i = v, i
            else:
                lo, lo_i = v, i
            leg_dir = direction
            leg_ext = extreme
            trig = False
        elif pos == 0.0 and pend_e < 0 and not trig and leg_dir != 0 and live and not blocked[i]:
            if leg_dir * (v - leg_ext) >= m * t and t * mid[i] / 1e4 >= th_min:
                pend_e = i
                pend_dir = -float(leg_dir)
                pend_th = t
                trig = True
        if pos != 0.0 and i > e_i and pend_x == 0 and pos * (y[i] - y[e_i]) <= -s * pth:
            pend_x = 2
    return k


rows = []
for typ in ("A", "B"):
    for m in (2.5, 3.5, 5.0):
        for s in (2.0, 3.0):
            out = np.zeros((n // 50, 6))
            k = r1(mins, y, mid, TH[typ], blocked, m, s, TH_MIN, out)
            f = pd.DataFrame(out[:k], columns=["t_entry", "t_exit", "dir", "net", "theta_usd", "reason"])
            f["cell"] = f"R1_{typ}_m{m}_s{s}"
            rows.append(f)
            print("R1", typ, m, s, k, flush=True)

# R3: fade big moves into scheduled times
SLOTS = {"LBMA_AM": ("Europe/London", 10, 30), "LBMA_PM": ("Europe/London", 15, 0), "US_data": ("America/New_York", 8, 30),
         "US_equity_open": ("America/New_York", 9, 30), "COMEX_settle": ("America/New_York", 13, 30)}
dates = pd.to_datetime(np.unique(((mins // 1440) * 1440) * 60), unit="s").normalize()
pos_of = pd.Series(np.arange(n), index=mins)
for h in (15, 30):
    evs = []
    for slot, (tz, hh, mm) in SLOTS.items():
        loc = (dates + pd.Timedelta(hours=hh, minutes=mm)).tz_localize(tz, ambiguous="NaT", nonexistent="NaT").dropna()
        tmin = (loc.tz_convert("UTC").asi8 // 60_000_000_000).astype(np.int64)
        ok = np.isin(tmin, mins) & np.isin(tmin - h, mins)
        tmin = np.unique(tmin[ok])
        T_ = pos_of[tmin].to_numpy()
        S_ = pos_of[tmin - h].to_numpy()
        same = (T_ - S_) == h  # no missing minute inside the window
        T_, S_ = T_[same], S_[same]
        move = y[T_] - y[S_]
        a = np.abs(move)
        thr = np.full(len(a), np.nan)
        for j in range(len(a)):
            past = a[max(0, j - 250):j]
            if len(past) >= 100:
                thr[j] = np.quantile(past, 0.8)
        sel = a >= thr
        for T, mv in zip(T_[sel], move[sel]):
            evs.append((int(T), slot, -np.sign(mv)))
    evs.sort()
    busy = -1
    rec = []
    for T, slot, d in evs:
        e = T + 1
        if e >= n or mins[e] != mins[T] + 1 or blocked[e] or e <= busy:
            continue
        x = int(np.searchsorted(mins, mins[e] + h + 1))
        x = min(x, int(cut[e]), n - 1)
        rec.append((mins[e], mins[x], d, d * (mid[x] - mid[e]) - 0.168, np.nan, 1, slot))
        busy = x
    f = pd.DataFrame(rec, columns=["t_entry", "t_exit", "dir", "net", "theta_usd", "reason", "slot"])
    f["cell"] = f"R3_pooled_h{h}"
    rows.append(f)
    print("R3 h", h, len(f), flush=True)
D = pd.concat(rows, ignore_index=True)
D["net_thb"] = D["net"] * 10 * 33.77
D["yr"] = pd.to_datetime(D["t_exit"] * 60, unit="s").dt.year
D["day"] = (D["t_entry"] * 60 + 3 * 3600) // 86400
D.to_csv(HERE / "out" / "C2_TRADES.private.csv", index=False)
dev = D[D.yr <= 2016]
print(dev.groupby("cell").agg(n=("net", "size"), net=("net", "mean"), win=("net", lambda v: (v > 0).mean()), thb=("net_thb", "sum")).round(3).to_string())
