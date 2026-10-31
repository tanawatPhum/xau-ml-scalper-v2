"""Synthetic-only checks for causal signal customization and baseline parity."""
import importlib
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import baseline_engine as baseline


POLICIES = (
    'all', 'skip_asia', 'skip_ny', 'skip_late', 'vol_ge075', 'vol_ge1',
    'vol_le15', 'long_only', 'short_only', 'utc_morning', 'utc_london',
)


def strategy():
    return importlib.import_module('strategy')


@pytest.fixture(scope='module')
def prices():
    rng = np.random.default_rng(1827)
    i = np.arange(10_000)
    scale = np.take([1.2, 4., .7, 3.], (i // 500) % 4)
    returns = rng.normal(size=len(i)) * scale + .8 * np.sin(i / 40)
    mid = 1900 * np.exp(np.cumsum(returns) / 1e4)
    mins = 23_142_240 + i
    mins[5500:] += 61
    return mins, mid - .084, mid + .084


def test_default_signals_and_simulation_match_frozen_baseline(prices):
    api = strategy()
    context = api.prepare(*prices)
    actual = api.build_signals(context)
    expected = baseline.make_signals(*prices)
    assert set(actual) == {'A', 'B'}
    for rule in expected:
        assert len(expected[rule]) > 10
        assert np.count_nonzero(expected[rule][:, 3]) > 0
        np.testing.assert_array_equal(actual[rule], expected[rule])
        # Omitting policy also means the unchanged baseline.
        np.testing.assert_array_equal(
            api.signals_for(context, baseline.RULES[rule]), expected[rule])
    old = baseline.simulate(*prices)
    new = baseline.simulate(*prices, signals=actual)
    pd.testing.assert_frame_equal(new.trades, old.trades)
    pd.testing.assert_frame_equal(new.equity, old.equity)
    pd.testing.assert_frame_equal(new.open_positions, old.open_positions)
    assert new.summary == old.summary
    assert new.diagnostics == old.diagnostics


@pytest.mark.parametrize('policy', POLICIES)
@pytest.mark.parametrize('rule', ['A', 'B'])
def test_real_signals_are_prefix_invariant_nonvacuously(prices, policy, rule):
    api = strategy()
    params = dict(baseline.RULES[rule], policy=policy)
    full = api.signals_for(api.prepare(*prices), params)
    eligible = 0
    for end in (1600, 3000, 4500, 6100, 8000):
        prefix = api.signals_for(api.prepare(*(x[:end] for x in prices)), params)
        assert len(prefix) > 3
        eligible += np.count_nonzero(prefix[:, 3])
        np.testing.assert_array_equal(prefix, full[full[:, 0] < end])
    assert eligible > 0, 'must exercise eligible entries, not only empty outputs'


def controlled_context(n=144):
    # Real swing detector: alternating two-basis-point turns, threshold one.
    y = np.log(2000.) * 1e4 + 2 * (np.arange(n) % 2)
    mid = np.exp(y / 1e4)
    return dict(mins=np.arange(n, dtype=np.int64) * 10, bid=mid-.084,
                ask=mid+.084, mid=mid, y=y, s60=np.ones(n),
                sl=np.ones(n), eff=np.ones(n))


PARAMS = dict(k=1., long_vol=True, min_usd=0., leg=0.)


@pytest.mark.parametrize('policy,allowed_hours', [
    ('skip_asia', tuple(range(7, 24))),
    ('skip_ny', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 21, 22, 23)),
    ('skip_late', tuple(range(21))),
    ('utc_morning', tuple(range(12))),
    ('utc_london', (7, 8, 9, 10, 11)),
])
def test_hour_filters_use_confirmation_time_and_keep_exit_rows(policy, allowed_hours):
    api = strategy()
    context = controlled_context()
    raw = api.signals_for(context, PARAMS)
    actual = api.signals_for(context, dict(PARAMS, policy=policy))
    indices = raw[:, 0].astype(int)
    hours = (context['mins'][indices] % 1440) // 60
    expected = raw[:, 3] * np.isin(hours, allowed_hours)
    np.testing.assert_array_equal(actual[:, :3], raw[:, :3])
    np.testing.assert_array_equal(actual[:, 3], expected)
    assert 0 < actual[:, 3].sum() < raw[:, 3].sum()
    # Turns at hour boundaries have their extreme in the preceding hour.
    boundary = np.isin(context['mins'][indices], [420, 720, 780, 1260])
    assert np.count_nonzero(boundary) == 4


@pytest.mark.parametrize('policy,eligible_indices', [
    ('vol_ge075', [3, 4, 5, 6, 7]),
    ('vol_ge1', [5, 6, 7]),
    ('vol_le15', [2, 3, 4, 5, 6]),
])
def test_ratio_filters_use_confirmation_ratio_and_reject_nonfinite(policy, eligible_indices):
    api = strategy()
    context = controlled_context(10)
    context['s60'] = np.array([1., np.nan, .7499, .75, .9999, 1., 1.5, 1.5001, np.inf, 0.])
    context['sl'][-1] = 0.  # zero / zero must not satisfy the upper-bound filter.
    raw = api.signals_for(context, PARAMS)
    actual = api.signals_for(context, dict(PARAMS, policy=policy))
    np.testing.assert_array_equal(actual[:, :3], raw[:, :3])
    assert actual[actual[:, 3] == 1, 0].astype(int).tolist() == eligible_indices


@pytest.mark.parametrize('policy,direction', [('long_only', -1), ('short_only', 1)])
def test_side_filters_follow_fade_entry_side_and_keep_exit_rows(policy, direction):
    api = strategy()
    context = controlled_context()
    raw = api.signals_for(context, PARAMS)
    actual = api.signals_for(context, dict(PARAMS, policy=policy))
    np.testing.assert_array_equal(actual[:, :3], raw[:, :3])
    np.testing.assert_array_equal(actual[:, 3], raw[:, 3] * (raw[:, 1] == direction))
    assert 0 < actual[:, 3].sum() < raw[:, 3].sum()


def test_filtered_confirmation_still_closes_an_existing_position():
    api = strategy()
    # The 12:59 entry fills at 13:00; the rejected 13:00 confirmation
    # still submits its exit for 13:01.
    context = controlled_context(6)
    context['mins'] = np.arange(777, 783, dtype=np.int64)
    actual = api.signals_for(context, dict(PARAMS, policy='skip_ny'))
    result = baseline.simulate(context['mins'], context['bid'], context['ask'],
                               signals={'A': actual})
    assert len(result.trades) == 1
    assert result.trades.iloc[0].t_signal == 779
    assert result.trades.iloc[0].t_exit == 781
    assert result.trades.iloc[0].exit_reason == 'swing'
    assert result.open_positions.empty


def test_filtering_does_not_mutate_context_parameters_or_source_events(monkeypatch, prices):
    api = strategy()
    context = api.prepare(*prices)
    before = {key: value.copy() for key, value in context.items()}
    params = dict(PARAMS, policy='skip_asia')
    params_before = params.copy()
    source = baseline._swings(context['mins'], context['y'], context['eff'], 0., 0.)
    source_before = source.copy()
    # The detector normally returns fresh arrays. Returning a shared real
    # detector result verifies the customization boundary does not alter it.
    monkeypatch.setattr(baseline, '_swings', lambda *args: source)
    actual = api.signals_for(context, params)
    assert not np.shares_memory(actual, source)
    np.testing.assert_array_equal(source, source_before)
    for key in context:
        np.testing.assert_array_equal(context[key], before[key])
    assert params == params_before


def test_prepare_volatility_excludes_current_close(prices):
    api = strategy()
    mins, bid, ask = (x[:2000].copy() for x in prices)
    original = api.prepare(mins, bid, ask)
    bid[-1] *= 2
    ask[-1] *= 2
    changed = api.prepare(mins, bid, ask)
    assert changed['y'][-1] != original['y'][-1]
    for name in ('s60', 'sl', 'eff'):
        np.testing.assert_array_equal(changed[name], original[name])


@pytest.mark.parametrize('mins,bid,ask', [
    ([0, 1], [1.], [1., 1.]),
    ([0, .5], [1., 1.], [1., 1.]),
    ([1, 0], [1., 1.], [1., 1.]),
    ([0, 0], [1., 1.], [1., 1.]),
    ([0, 1], [1., np.nan], [1., 2.]),
    ([0, 1], [1., 2.], [1., 1.]),
])
def test_prepare_rejects_invalid_prices(mins, bid, ask):
    with pytest.raises(ValueError):
        strategy().prepare(mins, bid, ask)


@pytest.mark.parametrize('update', [
    {'policy': 'unrecognized'}, {'k': 0}, {'k': np.inf}, {'min_usd': -1},
    {'leg': np.nan}, {'long_vol': 'false'},
])
def test_rejects_invalid_parameters(update):
    with pytest.raises(ValueError):
        strategy().signals_for(controlled_context(), dict(PARAMS, **update))


def test_empty_prices_produce_empty_events():
    api = strategy()
    context = api.prepare([], [], [])
    for events in api.build_signals(context).values():
        assert events.shape == (0, 4)
