"""Owner 22:02: v1 (official audit engine) that is always flat before the market closes, never holding across the
daily break. Schedule in New York local time (DST-aware): the gold daily break is 17:00-18:00 NY (checked in the data,
gaps.py). Rules, signals, fills and costs are the audit engine's (imported read-only from ../swing-causal-execution);
only the daily cutoff is replaced by a per-minute schedule.

S0  no schedule (must reproduce the audit's official run: end 613,359.55)
S1  flat at 16:55 NY every trading day, no entries 16:55-18:00 NY; any other gap (holiday early close, outage)
    closes after the gap (fully causal, no calendar)
S2  S1 + also flat in the last 5 minutes before every other gap > 30 min, as if the broker's holiday notice were
    known in advance (rare data outages are treated as known too - slightly optimistic)
"""
import json
import math
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "swing-causal-execution"))
import engine as E  # noqa: E402
from run import DEFAULT_CACHE, load_prices, yearly_report  # noqa: E402


@nb.njit(cache=True)
def _replay_sched(mins, mid, half_spread, events, oz, fx, commission, slip, blocked_a, crossed_a):
    """Copy of engine._replay; the only change: blocked / crossed come from per-minute arrays."""
    n = len(mins)
    trades = np.empty((len(events) + 1, 16))
    balance = np.zeros(n)
    unreal = np.zeros(n)
    exposure = np.zeros(n)
    cash = 0.
    side = 0.
    entry_i = signal_i = -1
    entry_fill = entry_half = theta = 0.
    pending_entry = -1
    pending_side = pending_theta = 0.
    pending_exit = 0
    exit_requested = -1
    j = k = cancelled = 0
    factor = oz * fx
    for i in range(n):
        now = mins[i]
        gap = i > 0 and now - mins[i - 1] > 30
        blocked = blocked_a[i]
        crossed_cutoff = crossed_a[i]
        scheduled = blocked or crossed_cutoff
        force = 4 if scheduled else (3 if gap else 0)
        reason = force if side and force else (pending_exit if side else 0)
        if reason:
            fill = mid[i] - side * (half_spread[i] + slip)
            net = (side * (fill - entry_fill) - 2 * commission) * factor
            cash += (side * (fill - entry_fill) - commission) * factor
            trades[k, 0] = mins[signal_i]
            trades[k, 1] = mins[entry_i]
            trades[k, 2] = now
            trades[k, 3] = side
            trades[k, 4] = mid[entry_i]
            trades[k, 5] = mid[i]
            trades[k, 6] = entry_fill
            trades[k, 7] = fill
            trades[k, 8] = theta
            trades[k, 9] = side * (mid[i] - mid[entry_i]) * factor
            trades[k, 10] = (entry_half + half_spread[i]) * factor
            trades[k, 11] = 2 * slip * factor
            trades[k, 12] = 2 * commission * factor
            trades[k, 13] = net
            trades[k, 14] = reason
            trades[k, 15] = (now - exit_requested) if not force else 0
            k += 1
            side = 0.
        pending_exit = 0
        if pending_entry >= 0:
            if not force and now == mins[pending_entry] + 1 and side == 0:
                side = pending_side
                signal_i, entry_i, theta = pending_entry, i, pending_theta
                entry_half = half_spread[i]
                entry_fill = mid[i] + side * (entry_half + slip)
                cash -= commission * factor
            else:
                cancelled += 1
            pending_entry = -1
        if j < len(events) and int(events[j, 0]) == i:
            if side:
                pending_exit, exit_requested = 1, now
            if events[j, 3] and not scheduled:
                pending_entry = i
                pending_side, pending_theta = -events[j, 1], events[j, 2]
            j += 1
        if side and i > entry_i and side * 1e4 * math.log(mid[i] / mid[entry_i]) <= -3 * theta:
            pending_exit, exit_requested = 2, now
        balance[i] = cash
        if side:
            liquidation = mid[i] - side * (half_spread[i] + slip)
            unreal[i] = (side * (liquidation - entry_fill) - commission) * factor
            exposure[i] = side * oz
    state = np.array([side, entry_i, signal_i, entry_fill, theta, pending_entry, pending_exit], dtype=np.float64)
    return trades[:k], balance, unreal, exposure, state, cancelled


def schedule(mins, mode):
    n = len(mins)
    if mode == "S0":
        return np.zeros(n, np.bool_), np.zeros(n, np.bool_)
    ny = pd.to_datetime(mins * 60, unit="s", utc=True).tz_convert("America/New_York")
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    blocked = (mod >= 16 * 60 + 55) & (mod < 18 * 60)
    day = (ny + pd.Timedelta(hours=6)).normalize().tz_localize(None).to_numpy().astype("datetime64[D]").astype(np.int64)
    crossed = np.r_[False, day[1:] != day[:-1]]
    if mode == "EX":
        # Exness metals: daily break 20:58-22:01 server GMT+0 in US summer time = 16:58-18:01 NY all year;
        # weekly open Sunday 22:05 GMT (summer) = 18:05 NY. Flat 3 minutes before the close.
        dow = ny.dayofweek.to_numpy()  # Monday 0 ... Sunday 6
        blocked = (mod >= 16 * 60 + 55) | (mod < 0)
        blocked &= mod < 18 * 60 + 1
        blocked |= (dow == 6) & (mod >= 18 * 60) & (mod < 18 * 60 + 5)
    if mode in ("S2", "EX"):
        gap_next = np.r_[np.diff(mins) > 30, True]          # last quote before every gap (and end of data)
        start_of_last = np.where(gap_next, mins, np.nan)
        nxt = pd.Series(start_of_last).bfill().to_numpy()   # minute of the last quote before the next gap
        blocked |= (nxt - mins) <= 4
    return blocked, crossed


def simulate_sched(mins, bid, ask, mode, config):
    mid = (bid + ask) / 2
    signals = E.make_signals(mins, bid, ask)
    half = (ask - bid) / 2 if config.cost_mode == "historical" else np.full(len(mid), config.spread / 2)
    blocked, crossed = schedule(mins, mode)
    balance, unreal = np.zeros(len(mid)), np.zeros(len(mid))
    parts = []
    for rule, raw in signals.items():
        ts, bal, unr, exp, state, can = _replay_sched(mins, mid, half, np.asarray(raw, float), config.oz, config.fx,
                                                      config.commission, config.slippage, blocked, crossed)
        f = pd.DataFrame(ts, columns=E.TRADE_COLUMNS)
        f["rule"] = rule
        f["exit_reason"] = f.reason_code.map(E.REASONS)
        parts.append(f)
        balance += bal
        unreal += unr
        assert state[0] == 0, "open position at end of data"
    trades = pd.concat(parts, ignore_index=True).sort_values(["t_exit", "rule"], kind="stable").reset_index(drop=True)
    balance += config.start
    eq = balance + unreal
    path = pd.DataFrame(dict(t_minute=mins, balance=balance, unrealized=unreal, equity=eq))
    dd, pct = E._drawdown(eq, config.start)
    return trades, path, dict(trades=len(trades), end_equity_thb=float(eq[-1]), net_thb=float(eq[-1] - config.start),
                              max_equity_drawdown_thb=dd, max_equity_drawdown_pct=pct, lowest_equity_thb=float(min(config.start, eq.min())))


class R:  # minimal object for run.yearly_report
    def __init__(self, trades, equity):
        self.trades, self.equity = trades, equity


years = list(range(2010, 2023))
mins, bid, ask = load_prices(DEFAULT_CACHE, years, allow_2020_2022=True)
cfg = E.Config()
out = {}
MODES = sys.argv[1:] or ["S0", "S1", "S2"]
for mode in MODES:
    T, P, S = simulate_sched(mins, bid, ask, mode, cfg)
    Y = yearly_report(R(T, P), years, cfg.start)
    # verification: no closed trade spans a >30-minute gap or a 17:00 NY break
    te = pd.to_datetime(T.t_entry * 60, unit="s", utc=True).dt.tz_convert("America/New_York")
    tx = pd.to_datetime(T.t_exit * 60, unit="s", utc=True).dt.tz_convert("America/New_York")
    dday = ((tx + pd.Timedelta(hours=6)).dt.normalize() != (te + pd.Timedelta(hours=6)).dt.normalize())
    gi = np.searchsorted(mins, T.t_entry.to_numpy())
    gx = np.searchsorted(mins, T.t_exit.to_numpy())
    gaps_cum = np.r_[0, np.cumsum(np.diff(mins) > 30)]
    spans_gap = (gaps_cum[gx] - gaps_cum[gi]) > 0
    v = T[T.t_exit >= int(np.datetime64("2020-01-01", "m").astype(np.int64))]
    out[mode] = dict(summary=S, yearly=Y, exit_reasons=T.exit_reason.value_counts().to_dict(),
                     trades_crossing_trading_day=int(dday.sum()), trades_spanning_gap=int(spans_gap.sum()),
                     by_rule={r: dict(trades=len(g), net_thb=float(g.net_thb.sum()), win=float((g.net_thb > 0).mean())) for r, g in T.groupby("rule")},
                     net_2020_2022_closed=float(v.net_thb.sum()))
    T.to_csv(HERE / "out" / f"TRADES_{mode}.private.csv", index=False)
    print(mode, json.dumps({k: round(x, 2) if isinstance(x, float) else x for k, x in S.items()}), flush=True)
    print("   exits", out[mode]["exit_reasons"], "| crossing a trading day", out[mode]["trades_crossing_trading_day"],
          "| spanning a gap", out[mode]["trades_spanning_gap"], flush=True)
if "S0" in out:
    assert abs(out["S0"]["summary"]["end_equity_thb"] - 613359.5516496036) < 0.01, "S0 does not reproduce the audit run"
    print("S0 reproduces the audit official run")
json.dump(out, open(HERE / "out" / f"FLAT_DAILY_{'_'.join(MODES)}.json", "w"), indent=1, default=float)
rows = []
for y in map(str, years):
    rows.append(dict(year=y, **{f"{m}_net": out[m]["yearly"][y]["closed_trade_net_thb"] for m in out},
                     **{f"{m}_end": out[m]["yearly"][y]["end_equity_thb"] for m in out},
                     **{f"{m}_dd": out[m]["yearly"][y]["max_equity_drawdown_thb"] for m in out}))
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).round(0).to_string(index=False))
for m in out:
    print(m, "by rule", {r: (v["trades"], round(v["net_thb"]), round(v["win"], 3)) for r, v in out[m]["by_rule"].items()},
          "| 2020-22 closed net", round(out[m]["net_2020_2022_closed"]))
