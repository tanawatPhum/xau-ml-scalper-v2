"""Hand-calculated execution examples, independent of strategy profitability."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def replay(prices, events, *, minutes=None, **kw):
    from engine import Config, simulate
    mid = np.array(prices, float)
    mins = np.arange(len(mid), dtype=np.int64) if minutes is None else np.array(minutes, dtype=np.int64)
    # Explicit event stream: index, swing direction (+1 low), theta, eligible.
    signals = {r: np.array(e, float).reshape(-1, 4) for r, e in events.items()}
    return simulate(mins, mid-.1, mid+.1, signals, Config(oz=1, fx=1, start=100, spread=0, **kw))


def test_signal_fills_next_minute_and_exit_next_minute():
    r = replay([100, 99, 98, 97, 96], {'A': [(0, 1, 10, 1), (2, -1, 10, 0)]})
    t = r.trades.iloc[0]
    assert (t.t_signal, t.t_entry, t.t_exit) == (0, 1, 3)
    assert t.net_thb == pytest.approx(2)


def test_stop_cannot_fill_at_trigger_close():
    r = replay([100, 100, 104, 110], {'A': [(0, 1, 1, 1)]})
    t = r.trades.iloc[0]
    assert (t.t_exit, t.exit_reason, t.net_thb) == (3, 'stop', -10)


def test_gap_exit_uses_first_quote_after_gap():
    r = replay([100, 100, 90, 120], {'A': [(0, 1, 10, 1)]}, minutes=[0, 1, 2, 100])
    t = r.trades.iloc[0]
    assert (t.t_exit, t.exit_reason, t.net_thb) == (100, 'data_gap', -20)
    assert r.equity.equity.tolist() == [100, 100, 110, 80]


def test_missed_entry_minute_is_cancelled():
    r = replay([100, 101, 102], {'A': [(0, 1, 10, 1)]}, minutes=[0, 2, 3])
    assert r.trades.empty and r.open_positions.empty
    assert r.diagnostics['cancelled_entries'] == 1


def test_pending_exit_survives_missing_quote():
    r = replay([100, 100, 105, 112], {'A': [(0, 1, 10, 1), (2, -1, 10, 0)]}, minutes=[0, 1, 2, 5])
    assert r.trades.iloc[0].t_exit == 5
    assert r.trades.iloc[0].net_thb == -12


def test_end_of_input_keeps_open_position():
    r = replay([100, 100, 105], {'A': [(0, 1, 10, 1)]})
    assert r.trades.empty and len(r.open_positions) == 1
    assert r.equity.balance.iloc[-1] == 100
    assert r.equity.equity.iloc[-1] == 95
    assert r.summary['max_equity_drawdown_thb'] == 5


def test_known_cutoff_flattens_and_disables_same_day_entries():
    r = replay([100, 100, 101, 102, 103], {'A': [(0, 1, 10, 1), (3, -1, 10, 1)]}, flat_minute_utc=2)
    assert r.trades.iloc[0].t_exit == 2
    assert r.trades.iloc[0].exit_reason == 'scheduled'
    assert r.open_positions.empty


def test_missing_cutoff_does_not_fill_before_missing_quote():
    r = replay([100, 100, 110, 120], {'A': [(0, 1, 10, 1)]}, minutes=[0, 1, 4, 5], flat_minute_utc=2)
    assert r.trades.iloc[0].t_exit == 4
    assert r.trades.iloc[0].net_thb == -10


@pytest.mark.parametrize('direction,prices', [(-1,[100,100,104,110]), (1,[100,100,96,90])])
def test_cost_ledger_for_long_and_short(direction, prices):
    from engine import Config, simulate
    m=np.array(prices,float); sig={'A':np.array([(0,direction,100,1),(2,-direction,100,0)],float)}
    r=simulate(np.arange(4),m-.1,m+.1,sig,Config(oz=1,fx=1,start=100,spread=.2,commission=.05,slippage=.1))
    t=r.trades.iloc[0]
    assert t.gross_mid_thb == pytest.approx(10)
    assert t.spread_cost_thb == pytest.approx(.2)
    assert t.slippage_cost_thb == pytest.approx(.2)
    assert t.commission_thb == pytest.approx(.1)
    assert t.net_thb == pytest.approx(9.5)
    assert r.equity.equity.iloc[1] == pytest.approx(99.5)
    assert r.equity.equity.iloc[-1] == pytest.approx(109.5)


def test_historical_spread_uses_correct_sides():
    from engine import Config, simulate
    r=simulate(np.arange(4), np.array([99,99,103,108.]), np.array([101,101,105,112.]),
               {'A':np.array([(0,-1,100,1),(2,1,100,0)],float)}, Config(oz=1,fx=1,start=100,cost_mode='historical'))
    t=r.trades.iloc[0]
    assert (t.entry_fill,t.exit_fill) == (101,108)
    assert t.net_thb == pytest.approx(7)
    assert t.spread_cost_thb == pytest.approx(3)


def test_portfolio_marks_both_rules_and_reconciles_costs():
    r=replay([100,100,110,120],{'A':[(0,-1,10000,1)],'B':[(0,1,10000,1)]})
    assert r.equity.equity.tolist() == [100]*4
    assert r.equity.gross_oz.tolist() == [0,2,2,2]
    assert len(r.open_positions)==2


def test_future_extension_cannot_rewrite_prefix():
    import pandas as pd
    events={'A':[(0,1,10,1),(2,-1,10,0),(4,1,10,1)]}
    a=replay([100,100,105,110,108,106],events)
    b=replay([100,100,105,110,108,106,120,80],events)
    pd.testing.assert_frame_equal(a.equity,b.equity.iloc[:6].reset_index(drop=True))
    pd.testing.assert_frame_equal(a.trades,b.trades[b.trades.t_exit<=5].reset_index(drop=True))


def test_signal_generation_is_causal_and_excludes_nonminute_returns():
    from engine import volatility, make_signals
    mins=np.r_[np.arange(50), np.arange(52,180)].astype(np.int64)
    mid=np.exp(np.arange(len(mins))*.0001)*100
    s60,_=volatility(mins,mid)
    # All valid adjacent returns are exactly 1 bp, including around the missing pair.
    assert s60[60] == pytest.approx(np.sqrt(60))
    a=make_signals(mins[:100],mid[:100]-.01,mid[:100]+.01)
    b=make_signals(mins,mid-.01,mid+.01)
    for rule in a:
        np.testing.assert_array_equal(a[rule],b[rule][b[rule][:,0]<100])
    changed=mid.copy();changed[60:]*=10
    s2,_=volatility(mins,changed)
    np.testing.assert_allclose(s60[:61],s2[:61],equal_nan=True)


@pytest.mark.parametrize('prices,minutes', [([100,101],[1,1]),([100,101],[2,1]),([100,-1],[1,2]),([100,np.nan],[1,2])])
def test_invalid_input_rejected(prices,minutes):
    with pytest.raises(ValueError):
        replay(prices,{},minutes=minutes)


def test_flat_and_empty_inputs_have_well_defined_reports():
    from engine import Config, make_signals, simulate
    for n in (0,1,200):
        m=np.full(n,100.)
        r=simulate(np.arange(n),m,m,make_signals(np.arange(n),m,m),Config())
        assert r.trades.empty
        assert r.summary['end_equity_thb']==100000
        assert r.summary['max_equity_drawdown_thb']==0


def test_real_signals_and_replay_are_prefix_invariant():
    import pandas as pd
    from engine import Config, make_signals, simulate
    rng=np.random.default_rng(42)
    mid=1500*np.exp(np.cumsum(rng.normal(0,.0005,3000)))
    mins=np.arange(len(mid))
    all_signals=make_signals(mins,mid-.01,mid+.01)
    assert sum(len(s) for s in all_signals.values())>20
    full=simulate(mins,mid-.01,mid+.01,all_signals,Config())
    for cut in (600,1500,2200):
        small=make_signals(mins[:cut],mid[:cut]-.01,mid[:cut]+.01)
        for rule in small:
            np.testing.assert_array_equal(small[rule],all_signals[rule][all_signals[rule][:,0]<cut])
        r=simulate(mins[:cut],mid[:cut]-.01,mid[:cut]+.01,small,Config())
        pd.testing.assert_frame_equal(r.equity,full.equity.iloc[:cut].reset_index(drop=True))
        pd.testing.assert_frame_equal(r.trades,full.trades[full.trades.t_exit<cut].reset_index(drop=True))


def test_open_entry_commission_reconciles_with_liquidation_equity():
    r=replay([100,100,105],{'A':[(0,-1,1000,1)]},commission=.25)
    assert r.summary['realized_net_thb']==pytest.approx(-.25)
    assert r.summary['closed_trade_net_thb']==0
    assert r.summary['commission_paid_thb']==pytest.approx(.25)
    assert r.summary['end_equity_thb']==pytest.approx(104.5)
    assert r.summary['end_equity_thb']==pytest.approx(
        100+r.summary['realized_net_thb']+r.summary['open_unrealized_thb'])


def test_dollar_filter_is_frozen_at_confirmation_not_fill():
    from engine import _swings
    mins=np.arange(6,dtype=np.int64)
    y=1e4*np.log(2162.)+np.array([0.,10.,0.,-30.,-20.,20.])
    ev=_swings(mins,y,np.full(6,10.),2.1626934441569983,2.5)
    low=ev[ev[:,0]==4]
    assert len(low)==1 and low[0,3]==0
    # Future fill is now far above the dollar threshold; eligibility cannot change.
    y[-1]+=1000
    again=_swings(mins,y,np.full(6,10.),2.1626934441569983,2.5)
    np.testing.assert_array_equal(ev[ev[:,0]<=4],again[again[:,0]<=4])


def test_cutoff_missed_across_midnight_fills_on_first_quote():
    r=replay([100,100,110],{'A':[(0,1,1000,1)]},minutes=[1436,1437,1441],flat_minute_utc=1439)
    assert r.trades.iloc[0].t_exit==1441
    assert r.trades.iloc[0].exit_reason=='scheduled'
