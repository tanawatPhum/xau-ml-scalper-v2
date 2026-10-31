import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))


def minutes(*ts):return pd.to_datetime(list(ts),utc=True).as_unit('ns').asi8//60_000_000_000


def replay(times,prices,events,**kwargs):
    from execution import simulate
    p=np.array(prices,float)
    return simulate(minutes(*times),p-.084,p+.084,{'A':np.array(events,float).reshape(-1,4)},**kwargs)


def test_preknown_close_flattens_and_cancels_new_entry():
    r=replay(['2010-06-02 20:52','2010-06-02 20:53','2010-06-02 20:54','2010-06-02 20:55','2010-06-02 20:56'],
             [100,100,101,102,103],[(0,-1,1000,1),(2,-1,1000,1)])
    assert len(r.trades)==1 and r.trades.iloc[0].exit_reason=='scheduled'
    assert r.trades.iloc[0].t_exit==minutes('2010-06-02 20:55')[0]
    assert r.summary['open_positions']==0
    assert r.diagnostics['market_close_crossings']==0


def test_missing_cutoff_fills_after_gap_without_inventing_old_price():
    r=replay(['2010-06-02 20:52','2010-06-02 20:53','2010-06-02 20:54','2010-06-02 22:01'],
             [100,100,101,90],[(0,-1,1000,1)])
    assert len(r.trades)==1
    assert r.trades.iloc[0].exit_mid==90
    assert r.diagnostics['market_close_crossings']==1
    assert r.diagnostics['late_cutoff_exits']==1


def test_eof_does_not_change_past_equity_or_force_exit():
    ts=['2010-06-02 15:00','2010-06-02 15:01','2010-06-02 15:02','2010-06-02 15:03']
    full=replay(ts,[100,100,101,99],[(0,-1,1000,1)])
    short=replay(ts[:3],[100,100,101],[(0,-1,1000,1)])
    np.testing.assert_array_equal(short.equity.equity,full.equity.equity.iloc[:3])
    assert short.summary['open_positions']==1 and len(short.trades)==0


def test_stop_detected_at_close_fills_next_observed_quote():
    r=replay(['2010-06-02 15:00','2010-06-02 15:01','2010-06-02 15:02','2010-06-02 15:03'],
             [100,100,98,97],[(0,-1,50,1)],stop_theta=2.)
    assert r.trades.iloc[0].exit_reason=='stop'
    assert r.trades.iloc[0].exit_mid==97


def test_quotes_when_configured_market_closed_cannot_be_executed():
    import pytest
    with pytest.raises(ValueError,match='outside'):
        replay(['2010-06-02 20:58','2010-06-02 20:59'],[100,200],[])


def test_transaction_costs_reconcile():
    from baseline_engine import Config
    r=replay(['2010-06-02 20:53','2010-06-02 20:54','2010-06-02 20:55'],
             [100,100,102],[(0,-1,1000,1)],config=Config(commission=.01,slippage=.02))
    t=r.trades.iloc[0]
    expected=(2-.168-2*.02-2*.01)*10*33.77
    assert np.isclose(t.net_thb,expected)
    assert np.isclose(r.summary['net_equity_thb'],expected)


def test_missed_friday_cutoff_can_exit_during_holiday_entry_blackout():
    r=replay(['2010-10-08 18:46','2010-10-08 18:47','2010-10-10 22:05','2010-10-10 22:06'],
             [100,100,99,105],[(0,-1,1000,1),(2,-1,1000,1)])
    assert len(r.trades)==1
    assert r.trades.iloc[0].t_exit==minutes('2010-10-10 22:05')[0]
    assert r.summary['open_positions']==0
    assert r.diagnostics['market_close_crossings']==1
