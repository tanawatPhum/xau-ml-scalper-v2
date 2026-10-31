"""Causal entry customization over the unchanged execution/swing snapshot.

Every swing confirmation remains in the stream: policies mask only entry
eligibility, so a rejected entry can still close an existing position.
"""
from numbers import Real

import numpy as np

import baseline_engine


BASE_RULES = {
    name: dict(params, policy='all')
    for name, params in baseline_engine.RULES.items()
}
POLICIES = (
    'all', 'skip_asia', 'skip_ny', 'skip_late', 'vol_ge075', 'vol_ge1',
    'vol_le15', 'long_only', 'short_only', 'utc_morning', 'utc_london',
)


def prepare(mins, bid, ask):
    """Validate quotes and cache causal price/volatility arrays for a search."""
    mins, bid, ask = baseline_engine.validate_prices(mins, bid, ask)
    mid = (bid + ask) / 2
    s60, sl = baseline_engine.volatility(mins, mid)
    eff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    return dict(mins=mins, bid=bid, ask=ask, mid=mid, y=1e4*np.log(mid),
                s60=s60, sl=sl, eff=eff)


def signals_for(context, params):
    """Return fresh [confirmation index, direction, theta, eligible] rows.

Hours are UTC and all filter features are read at the confirmation index.
The trade fades the swing direction, so a direction of -1 enters long.
"""
    for key in ('k', 'min_usd', 'leg'):
        value = params[key]
        if (not isinstance(value, Real) or not np.isfinite(value)
                or value < 0 or (key == 'k' and value == 0)):
            raise ValueError(f'{key} must be finite and '
                             + ('positive' if key == 'k' else 'nonnegative'))
    if not isinstance(params['long_vol'], (bool, np.bool_)):
        raise ValueError('long_vol must be boolean')
    policy = params.get('policy', 'all')
    if policy not in POLICIES:
        raise ValueError(f'unknown entry policy: {policy}')

    vol = context['eff'] if params['long_vol'] else context['s60']
    events = baseline_engine._swings(
        context['mins'], context['y'], params['k'] * vol,
        params['min_usd'], params['leg']).copy()
    if policy == 'all' or not len(events):
        return events

    indices = events[:, 0].astype(np.int64)
    if policy in ('long_only', 'short_only'):
        keep = events[:, 1] == (-1 if policy == 'long_only' else 1)
    elif policy.startswith('vol_'):
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = context['s60'][indices] / context['sl'][indices]
        if policy == 'vol_ge075':
            keep = ratio >= .75
        elif policy == 'vol_ge1':
            keep = ratio >= 1.
        else:
            keep = ratio <= 1.5
        keep &= np.isfinite(ratio)
    else:
        hours = (context['mins'][indices] % 1440) // 60
        if policy == 'skip_asia':
            keep = hours >= 7
        elif policy == 'skip_ny':
            keep = (hours < 13) | (hours >= 21)
        elif policy == 'skip_late':
            keep = hours < 21
        elif policy == 'utc_morning':
            keep = hours < 12
        else:  # utc_london
            keep = (hours >= 7) & (hours < 12)
    events[:, 3] *= keep
    return events


def build_signals(context, rules=None):
    """Build independent event streams for the supplied rule mapping."""
    rules = BASE_RULES if rules is None else rules
    return {name: signals_for(context, params) for name, params in rules.items()}
