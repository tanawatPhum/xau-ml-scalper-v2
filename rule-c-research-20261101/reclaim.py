"""Experimental, causal failed-breakout/reclaim signal family.

At minute t, the prior ``lookback`` closes define an unbuffered range. All
lookback prior rows and t must be adjacent minutes in the same session. An
excursion strictly outside that range plus ``buffer`` times the preceding
row's effective volatility in USD/oz arms one pending breakout. The boundary
is frozen until the first close that reaches/crosses it in the next 1..10
minutes, when the signal fades the breakout. No A/B state is inspected.

Gaps, session changes, and invalid prices clear pending state. Excursions
expire after ten minutes; a confirmation bar cannot also arm a new breakout.
At a signal, scale=max(eff[t]*mid[t]/1e4, 0.5); invalid confirmation volatility
discards that pending signal. Exits are specified for the external executor.
Running this file performs synthetic checks only and reads no market data.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
from numba import njit


def candidates():
    """Return the eight fixed research variants, without data-driven selection."""
    return [
        {
            "id": f"reclaim_l{lookback}_b{int(buffer * 100):02d}_h{hold}",
            "family": "reclaim",
            "params": {"lookback": lookback, "buffer": buffer},
            "hold": hold,
            "stop": 1.5,
            "tp": 1.5,
        }
        for lookback in (60, 240)
        for buffer in (0.0, 0.25)
        for hold in (30, 90)
    ]


@njit(cache=True)
def _signal_loop(mins, mid, eff, session, upper, lower, lookback, buffer):
    n = len(mid)
    side = np.zeros(n, dtype=np.int8)
    scale = np.zeros(n, dtype=np.float64)
    adjacent = 0
    pending = 0
    breakout_minute = 0
    boundary = 0.0
    for i in range(n):
        if i == 0 or mins[i] - mins[i - 1] != 1 or session[i] != session[i - 1]:
            pending = 0
            adjacent = 0
        else:
            adjacent += 1
        if not np.isfinite(mid[i]) or mid[i] <= 0.0:
            pending = 0
            adjacent = 0
            continue

        if pending != 0:
            if mins[i] - breakout_minute > 10:
                pending = 0
            else:
                reclaimed = ((pending == 1 and mid[i] <= boundary)
                             or (pending == -1 and mid[i] >= boundary))
                if reclaimed:
                    if np.isfinite(eff[i]) and eff[i] >= 0.0:
                        value = eff[i] * mid[i] / 1e4
                        if np.isfinite(value):
                            side[i] = -pending
                            scale[i] = max(value, 0.5)
                    pending = 0
                # Active excursions and confirmations cannot start a second
                # excursion on the same row.
                continue

        if adjacent < lookback:
            continue
        if (not np.isfinite(upper[i]) or not np.isfinite(lower[i])
                or lower[i] <= 0.0 or not np.isfinite(eff[i - 1])
                or eff[i - 1] < 0.0):
            continue
        prior_vol = eff[i - 1] * mid[i - 1] / 1e4
        if not np.isfinite(prior_vol):
            continue
        if mid[i] > upper[i] + buffer * prior_vol:
            pending = 1
            boundary = upper[i]
            breakout_minute = mins[i]
        elif mid[i] < lower[i] - buffer * prior_vol:
            pending = -1
            boundary = lower[i]
            breakout_minute = mins[i]
    return side, scale


def signals(c, spec):
    """Return int8 entry sides and float64 USD/oz scales, zero off-signal."""
    lookback = int(spec["params"]["lookback"])
    buffer = float(spec["params"]["buffer"])
    if lookback not in (60, 240) or buffer not in (0.0, 0.25):
        raise ValueError("Unsupported reclaim parameters")
    mins = np.asarray(c["mins"], dtype=np.int64)
    mid = np.asarray(c["mid"], dtype=np.float64)
    eff = np.asarray(c["eff"], dtype=np.float64)
    session = np.asarray(c["calendar"].session_day, dtype=np.int64)
    if any(a.ndim != 1 or len(a) != len(mid) for a in (mins, mid, eff, session)):
        raise ValueError("Reclaim inputs must be aligned one-dimensional arrays")
    rolling = pd.Series(mid).rolling(lookback, min_periods=lookback)
    upper = rolling.max().shift(1).to_numpy(dtype=np.float64)
    lower = rolling.min().shift(1).to_numpy(dtype=np.float64)
    return _signal_loop(mins, mid, eff, session, upper, lower, lookback, buffer)


def _synthetic_checks():
    """Hand-checked fixtures catch early entries, stale boundaries, and leakage."""
    specs = candidates()
    assert len(specs) == 8 and len({s["id"] for s in specs}) == 8
    assert all(s["stop"] == 1.5 and s["tp"] == 1.5 for s in specs)

    def context(prices, *, minutes=None, sessions=None, eff=None):
        mid = np.asarray(prices, dtype=np.float64)
        n = len(mid)
        return {
            "mins": np.arange(n, dtype=np.int64) if minutes is None else minutes,
            "mid": mid,
            "eff": np.full(n, 100.0) if eff is None else eff,
            "s60": np.zeros(n), "sl": np.zeros(n), "y": np.full(n, 2010),
            "calendar": SimpleNamespace(
                session_day=np.zeros(n, dtype=np.int64) if sessions is None else sessions
            ),
        }

    def selected(lookback=60, buffer=0.0, hold=30):
        return next(s for s in specs if s["params"]["lookback"] == lookback
                    and s["params"]["buffer"] == buffer and s["hold"] == hold)

    # The breakout bar is excluded from the range; returning to its old edge
    # must confirm, while merely returning below the updated high must not.
    c = context([100.0] * 60 + [102.0, 101.0, 100.0, 100.0])
    side, scale = signals(c, selected())
    assert side.dtype == np.int8 and scale.dtype == np.float64
    assert np.flatnonzero(side).tolist() == [62] and side[62] == -1
    assert scale[62] == 1.0
    c["eff"][62] = 200.0
    assert signals(c, selected())[1][62] == 2.0  # Confirmation volatility.

    c = context([100.0] * 60 + [98.0, 99.0, 100.0])
    assert signals(c, selected())[0][-1] == 1
    c["eff"][:] = 0.0
    assert signals(c, selected())[1][-1] == 0.5

    # Ten minutes is inclusive, eleven is expired; the range stays frozen.
    c = context([100.0] * 60 + [102.0] * 10 + [100.0])
    assert np.flatnonzero(signals(c, selected())[0]).tolist() == [70]
    c = context([100.0] * 60 + [102.0] * 11 + [100.0])
    assert not np.any(signals(c, selected())[0])

    # Prior (not breakout-bar) volatility determines the excursion buffer.
    c = context([100.0] * 60 + [100.2, 100.0])
    c["eff"][60] = 1.0
    assert signals(c, selected(buffer=0.0))[0][-1] == -1
    assert not np.any(signals(c, selected(buffer=0.25))[0])
    c = context([100.0] * 60 + [100.3, 100.0])
    assert signals(c, selected(buffer=0.25))[0][-1] == -1

    # Pending excursions never survive a missing minute or session change.
    c = context([100.0] * 60 + [102.0, 100.0])
    c["mins"][-1] += 1
    assert not np.any(signals(c, selected())[0])
    c = context([100.0] * 60 + [102.0, 100.0])
    c["calendar"].session_day[-1] = 1
    assert not np.any(signals(c, selected())[0])

    # A gap inside the prior lookback invalidates it even when the latest
    # two rows are consecutive; missing bars cannot compress wall time.
    c = context([100.0] * 60 + [102.0, 100.0])
    c["mins"][30:] += 1
    assert not np.any(signals(c, selected())[0])
    c = context([100.0] * 60 + [102.0, 100.0])
    c["calendar"].session_day[30:] = 1
    assert not np.any(signals(c, selected())[0])
    c = context([100.0] * 59 + [102.0, 100.0])
    assert not np.any(signals(c, selected())[0])

    # The long variant must wait for all 240 prior closes, then behave like
    # the short variant. Exit horizon must never alter entry generation.
    c = context([100.0] * 239 + [102.0, 100.0])
    assert not np.any(signals(c, selected(lookback=240))[0])
    c = context([100.0] * 240 + [102.0, 101.0, 100.0])
    long_side, long_scale = signals(c, selected(lookback=240))
    assert np.flatnonzero(long_side).tolist() == [242] and long_side[242] == -1
    other_side, other_scale = signals(c, selected(lookback=240, hold=90))
    np.testing.assert_array_equal(long_side, other_side)
    np.testing.assert_array_equal(long_scale, other_scale)

    # A prior range must warm up again following a session boundary. The
    # first eligible bar may arm, and its following reclaim may confirm.
    c = context([100.0] * 120 + [102.0, 100.0])
    c["calendar"].session_day[60:] = 1
    assert np.flatnonzero(signals(c, selected())[0]).tolist() == [121]

    # Unusable confirmation volatility cannot emit an unpriced signal.
    c = context([100.0] * 60 + [102.0, 100.0])
    c["eff"][-1] = np.nan
    assert not np.any(signals(c, selected())[0])

    # Prefix equivalence catches shifted/centered ranges and future-dependent
    # state. Include both lookbacks, a gap, sessions, and volatility changes.
    rng = np.random.default_rng(1729)
    c = context(100.0 + np.cumsum(rng.normal(0.0, 0.3, 700)),
                eff=rng.uniform(10.0, 100.0, 700))
    c["mins"][390:] += 2
    c["calendar"].session_day[520:] = 1
    for spec in specs:
        full_side, full_scale = signals(c, spec)
        assert np.all(np.isfinite(full_scale[full_side != 0]))
        assert np.all(full_scale[full_side != 0] > 0.0)
        for end in (0, 1, 59, 60, 61, 239, 240, 241, 389, 390, 391, 519, 520, 521, 699):
            prefix = {k: v[:end] for k, v in c.items() if k != "calendar"}
            prefix["calendar"] = SimpleNamespace(session_day=c["calendar"].session_day[:end])
            actual_side, actual_scale = signals(prefix, spec)
            np.testing.assert_array_equal(actual_side, full_side[:end])
            np.testing.assert_array_equal(actual_scale, full_scale[:end])
    print("reclaim: synthetic timing, session/gap, scale, and causal-prefix checks passed")


if __name__ == "__main__":
    _synthetic_checks()
