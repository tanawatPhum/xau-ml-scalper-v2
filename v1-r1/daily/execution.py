"""Daily RX execution: audited replay extended with a timestamp-only calendar.
No future gaps or forced end-of-data liquidation.
"""
from dataclasses import dataclass
import math

import numba as nb
import numpy as np
import pandas as pd
from calendar_rules import schedule

RULES = {'A': dict(k=1., long_vol=True, min_usd=2.1626934441569983, leg=2.5),
         'B': dict(k=1.5, long_vol=False, min_usd=0., leg=3.5)}
REASONS = {1: 'swing', 2: 'stop', 3: 'data_gap', 4: 'scheduled'}
TRADE_COLUMNS = ['t_signal', 't_entry', 't_exit', 'side', 'entry_mid', 'exit_mid',
                 'entry_fill', 'exit_fill', 'theta_bps', 'gross_mid_thb',
                 'spread_cost_thb', 'slippage_cost_thb', 'commission_thb',
                 'net_thb', 'reason_code', 'exit_delay_minutes']


@dataclass(frozen=True)
class Config:
    start: float = 100_000.
    oz: float = 10.
    fx: float = 33.77
    cost_mode: str = 'fixed'
    spread: float = .168
    commission: float = 0.  # USD/oz per side
    slippage: float = 0.    # USD/oz adverse per fill
    flat_minute_utc: int | None = None

    def __post_init__(self):
        for key in ('start', 'oz', 'fx'):
            if not math.isfinite(getattr(self, key)) or getattr(self, key) <= 0:
                raise ValueError(f'{key} must be finite and positive')
        for key in ('spread', 'commission', 'slippage'):
            if not math.isfinite(getattr(self, key)) or getattr(self, key) < 0:
                raise ValueError(f'{key} must be finite and nonnegative')
        if self.cost_mode not in ('fixed', 'historical'):
            raise ValueError('cost_mode must be fixed or historical')
        if self.flat_minute_utc is not None and (
                not isinstance(self.flat_minute_utc, int) or not 0 <= self.flat_minute_utc < 1440):
            raise ValueError('flat_minute_utc must be an integer in [0,1440)')


@dataclass
class Result:
    trades: pd.DataFrame
    open_positions: pd.DataFrame
    equity: pd.DataFrame
    summary: dict
    diagnostics: dict


def validate_prices(mins, bid, ask):
    mins, bid, ask = np.asarray(mins), np.asarray(bid, float), np.asarray(ask, float)
    if any(a.ndim != 1 for a in (mins, bid, ask)) or not (len(mins) == len(bid) == len(ask)):
        raise ValueError('prices must be equal-length one-dimensional arrays')
    if not np.isfinite(mins).all() or np.any(mins != np.floor(mins)):
        raise ValueError('timestamps must be finite integer UTC minutes')
    mins = mins.astype(np.int64)
    if np.any(np.diff(mins) <= 0):
        raise ValueError('timestamps must be strictly increasing and unique')
    if not (np.isfinite(bid).all() and np.isfinite(ask).all()) or np.any(bid <= 0) or np.any(ask < bid):
        raise ValueError('quotes must be finite, positive and not crossed')
    return mins, bid, ask


def volatility(mins, mid):
    """Prior adjacent-minute returns only; long history excludes cross-gap pairs."""
    mins, mid, _ = validate_prices(mins, mid, mid)
    n = len(mid)
    if not n:
        return np.empty(0), np.empty(0)
    r = np.r_[0., np.diff(1e4 * np.log(mid))]
    adjacent = np.r_[False, np.diff(mins) == 1]
    cs = np.r_[0., np.cumsum(np.where(adjacent, r*r, 0.))]
    cc = np.r_[0, np.cumsum(adjacent)]
    first = np.maximum.accumulate(np.where(np.r_[True, np.diff(mins) > 30], np.arange(n), 0))
    i = np.arange(n)
    out = []
    for win, minimum in ((60, 30), (1440, 720)):
        lo = np.maximum(i-win, first+1) if win == 60 else np.maximum(i-win, 1)
        lo = np.minimum(lo, i)
        count = cc[i]-cc[lo]
        ss = np.maximum(cs[i]-cs[lo], 0.)
        ok = (count >= minimum) & (ss > 1e-12)
        out.append(np.where(ok, np.sqrt(ss/np.maximum(count, 1)*60), np.nan))
    return tuple(out)


@nb.njit(cache=True)
def _swings(mins, y, threshold, min_usd, min_leg):
    n = len(y)
    events = np.empty((n, 4))
    count = 0
    mode = 0
    hi = lo = 0.
    hi_i = lo_i = 0
    previous = np.nan
    for i in range(n):
        if i == 0 or mins[i]-mins[i-1] > 30:
            hi = lo = y[i]
            hi_i = lo_i = i
            mode = 0
            previous = np.nan
            continue
        v, t = y[i], threshold[i]
        live = np.isfinite(t) and t > 0
        direction = 0
        extreme = 0.
        if mode == 0:
            if v > hi:
                hi, hi_i = v, i
            if v < lo:
                lo, lo_i = v, i
            if live and v-lo >= t and lo_i < i:
                direction, extreme = 1, lo
            elif live and hi-v >= t and hi_i < i:
                direction, extreme = -1, hi
        elif mode == 1:
            if v > hi:
                hi, hi_i = v, i
            elif live and hi-v >= t:
                direction, extreme = -1, hi
        else:
            if v < lo:
                lo, lo_i = v, i
            elif live and v-lo >= t:
                direction, extreme = 1, lo
        if direction:
            leg = direction*(previous-extreme)/t
            eligible = np.isfinite(previous) and leg >= min_leg and t*math.exp(v/1e4)/1e4 >= min_usd
            events[count, 0] = i
            events[count, 1] = direction
            events[count, 2] = t
            events[count, 3] = eligible
            count += 1
            previous = extreme
            mode = direction
            if direction == 1:
                hi, hi_i = v, i
            else:
                lo, lo_i = v, i
    return events[:count]


def make_signals(mins, bid, ask):
    mins, bid, ask = validate_prices(mins, bid, ask)
    mid = (bid+ask)/2
    s60, sl = volatility(mins, mid)
    eff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    return {r: _swings(mins, 1e4*np.log(mid), p['k']*(eff if p['long_vol'] else s60),
                       p['min_usd'], p['leg']) for r, p in RULES.items()}


@nb.njit(cache=True)
def _replay(mins, mid, half_spread, events, oz, fx, commission, slip, blocked_a, deadlines, stop_theta):
    n = len(mins)
    trades = np.empty((len(events)+1, 16))
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
    factor = oz*fx
    for i in range(n):
        now = mins[i]
        gap = i > 0 and now-mins[i-1] > 30
        blocked = blocked_a[i]
        crossed_cutoff = side != 0 and now >= deadlines[entry_i]
        scheduled = blocked or crossed_cutoff
        force = 4 if scheduled else (3 if gap else 0)
        reason = force if side and force else (pending_exit if side else 0)
        if reason:
            fill = mid[i]-side*(half_spread[i]+slip)
            net = (side*(fill-entry_fill)-2*commission)*factor
            cash += (side*(fill-entry_fill)-commission)*factor
            trades[k, 0] = mins[signal_i]
            trades[k, 1] = mins[entry_i]
            trades[k, 2] = now
            trades[k, 3] = side
            trades[k, 4] = mid[entry_i]
            trades[k, 5] = mid[i]
            trades[k, 6] = entry_fill
            trades[k, 7] = fill
            trades[k, 8] = theta
            trades[k, 9] = side*(mid[i]-mid[entry_i])*factor
            trades[k, 10] = (entry_half+half_spread[i])*factor
            trades[k, 11] = 2*slip*factor
            trades[k, 12] = 2*commission*factor
            trades[k, 13] = net
            trades[k, 14] = reason
            trades[k, 15] = (now-exit_requested) if not force else 0
            k += 1
            side = 0.
        pending_exit = 0
        if pending_entry >= 0:
            if not force and now == mins[pending_entry]+1 and side == 0:
                side = pending_side
                signal_i, entry_i, theta = pending_entry, i, pending_theta
                entry_half = half_spread[i]
                entry_fill = mid[i]+side*(entry_half+slip)
                cash -= commission*factor
            else:
                cancelled += 1
            pending_entry = -1
        # Current close can only submit actions for a subsequent observed quote.
        if j < len(events) and int(events[j, 0]) == i:
            if side:
                pending_exit, exit_requested = 1, now
            if events[j, 3] and not scheduled:
                pending_entry = i
                pending_side, pending_theta = -events[j, 1], events[j, 2]
            j += 1
        if side and i > entry_i and side*1e4*math.log(mid[i]/mid[entry_i]) <= -stop_theta*theta:
            pending_exit, exit_requested = 2, now
        balance[i] = cash
        if side:
            liquidation = mid[i]-side*(half_spread[i]+slip)
            unreal[i] = (side*(liquidation-entry_fill)-commission)*factor
            exposure[i] = side*oz
    state = np.array([side, entry_i, signal_i, entry_fill, theta, pending_entry, pending_exit], dtype=np.float64)
    return trades[:k], balance, unreal, exposure, state, cancelled


def _drawdown(values, start):
    peak = np.maximum.accumulate(np.r_[start, values])[1:]
    dd = peak-values
    return (float(dd.max()), float(np.max(dd/peak)*100)) if len(dd) else (0., 0.)


def simulate(mins, bid, ask, signals=None, config=None, stop_theta=3., calendar=None):
    """Replay precomputed causal confirmations or generate A/B signals directly."""
    config = config or Config()
    if config.flat_minute_utc is not None:raise ValueError('use NY calendar, not fixed UTC cutoff')
    if not math.isfinite(stop_theta) or stop_theta <= 0:raise ValueError('stop_theta must be positive')
    mins, bid, ask = validate_prices(mins, bid, ask)
    calendar = schedule(mins) if calendar is None else calendar
    if not np.array_equal(calendar.mins,mins):raise ValueError('calendar timestamps mismatch')
    if not calendar.available.all():raise ValueError('quotes outside configured trading calendar')
    mid = (bid+ask)/2
    signals = make_signals(mins, bid, ask) if signals is None else signals
    half = (ask-bid)/2 if config.cost_mode == 'historical' else np.full(len(mid), config.spread/2)
    balance, unreal, gross, netoz = (np.zeros(len(mid)) for _ in range(4))
    parts, opened = [], []
    cancelled = pending = 0
    for rule, raw in signals.items():
        events = np.asarray(raw, float)
        if events.ndim != 2 or events.shape[1] != 4 or not np.isfinite(events).all():
            raise ValueError('signals must have four finite columns')
        if len(events) and (np.any(events[:,0] != np.floor(events[:,0])) or np.any(events[:,0] < 0)
                            or np.any(events[:,0] >= len(mid)) or np.any(np.diff(events[:,0]) <= 0)
                            or np.any(np.abs(events[:,1]) != 1) or np.any(events[:,2] <= 0)
                            or np.any((events[:,3] != 0) & (events[:,3] != 1))):
            raise ValueError('invalid signal indices, direction, theta or eligibility')
        ts, bal, unr, exp, state, can = _replay(mins, mid, half, events, config.oz, config.fx,
            config.commission, config.slippage, calendar.blocked, calendar.deadline, stop_theta)
        frame = pd.DataFrame(ts, columns=TRADE_COLUMNS)
        frame['rule'] = rule
        frame['exit_reason'] = frame.reason_code.map(REASONS)
        for c in ('t_signal', 't_entry', 't_exit', 'side', 'reason_code', 'exit_delay_minutes'):
            frame[c] = frame[c].astype(np.int64)
        parts.append(frame)
        balance += bal
        unreal += unr
        gross += np.abs(exp)
        netoz += exp
        cancelled += can
        pending += int(state[5] >= 0)+int(state[6] > 0)
        if state[0]:
            opened.append(dict(rule=rule, side=int(state[0]), t_entry=int(mins[int(state[1])]),
                               entry_fill=state[3], theta_bps=state[4], unrealized_thb=float(unr[-1]),
                               entry_commission_thb=config.commission*config.oz*config.fx))
    trades = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=TRADE_COLUMNS+['rule','exit_reason'])
    trades = trades.sort_values(['t_exit','rule'], kind='stable').reset_index(drop=True)
    balance += config.start
    eq = balance+unreal
    path = pd.DataFrame(dict(t_minute=mins, balance=balance, unrealized=unreal, equity=eq, gross_oz=gross, net_oz=netoz))
    dd, pct = _drawdown(eq, config.start)
    bdd, _ = _drawdown(balance, config.start)
    end = float(eq[-1]) if len(eq) else config.start
    paid_open_commission = len(opened)*config.commission*config.oz*config.fx
    summary = dict(trades=len(trades), open_positions=len(opened), end_balance_thb=float(balance[-1]) if len(eq) else config.start,
                   end_equity_thb=end, net_equity_thb=end-config.start,
                   realized_net_thb=float(balance[-1]-config.start) if len(eq) else 0.,
                   closed_trade_net_thb=float(trades.net_thb.sum()),
                   open_unrealized_thb=float(unreal[-1]) if len(eq) else 0., max_equity_drawdown_thb=dd,
                   max_equity_drawdown_pct=pct, max_balance_drawdown_thb=bdd,
                   lowest_equity_thb=min(config.start,float(eq.min())) if len(eq) else config.start,
                   max_gross_oz=float(gross.max()) if len(eq) else 0.,
                   nonpositive_equity_minutes=int((eq <= 0).sum()),
                   first_nonpositive_utc_minute=int(mins[np.flatnonzero(eq <= 0)[0]]) if np.any(eq <= 0) else None,
                   gross_mid_thb=float(trades.gross_mid_thb.sum()), spread_cost_thb=float(trades.spread_cost_thb.sum()),
                   slippage_cost_thb=float(trades.slippage_cost_thb.sum()), commission_thb=float(trades.commission_thb.sum()),
                   open_entry_commission_thb=paid_open_commission,
                   commission_paid_thb=float(trades.commission_thb.sum())+paid_open_commission)
    diagnostics = dict(cancelled_entries=cancelled, pending_orders_at_end=pending,
                       gap_count=int((np.diff(mins)>30).sum()),
                       close_based_stop=True, terminal_liquidation=False)
    ei=np.searchsorted(mins,trades.t_entry.to_numpy(dtype=np.int64))
    xi=np.searchsorted(mins,trades.t_exit.to_numpy(dtype=np.int64))
    gap_cum=np.r_[0,np.cumsum(np.diff(mins)>30)] if len(mins) else np.empty(0,int)
    diagnostics.update(late_cutoff_exits=int((trades.t_exit.to_numpy()>calendar.deadline[ei]).sum()),
        market_close_crossings=int((trades.t_exit.to_numpy()>=calendar.market_close[ei]).sum()),
        session_crossings=int((calendar.session_day[ei]!=calendar.session_day[xi]).sum()),
        trades_spanning_data_gap=int((gap_cum[xi]>gap_cum[ei]).sum()),
        scheduled_exits=int((trades.exit_reason=='scheduled').sum()),stop_theta=stop_theta)
    return Result(trades, pd.DataFrame(opened), path, summary, diagnostics)
