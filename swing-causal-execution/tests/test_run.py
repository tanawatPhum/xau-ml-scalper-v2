import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def cache_fixture(tmp_path, year=2010):
    cache=tmp_path/'cache';cache.mkdir()
    base=int(np.datetime64(f'{year}-01-01T00:00','m').astype(int))
    mid=1500*np.exp(np.cumsum(np.random.default_rng(42).normal(0,.0005,3000)))
    np.savez(cache/f'M1_{year}.private.npz',base=base,bid=mid-.1,ask=mid+.1)
    return cache


@pytest.mark.parametrize('years', [(2020,), (2023,), (2010,2022), (), (2010,2010), (2011,2010)])
def test_year_boundary_rejected_before_price_file_access(tmp_path,years):
    from run import load_prices
    with pytest.raises(ValueError):
        load_prices(tmp_path/'does-not-exist',years)


def test_cache_loader_preserves_missing_minutes(tmp_path):
    from run import load_prices
    cache=cache_fixture(tmp_path)
    with np.load(cache/'M1_2010.private.npz') as z:
        bid=z['bid'].copy();ask=z['ask'].copy();base=z['base'].copy()
    bid[2]=np.nan
    np.savez(cache/'M1_2010.private.npz',base=base,bid=bid,ask=ask)
    mins,bid,ask=load_prices(cache,[2010])
    assert len(mins)==2999
    assert mins[2]-mins[1]==2


def test_cli_creates_new_reconciled_artifacts_and_refuses_overwrite(tmp_path):
    from run import main
    cache=cache_fixture(tmp_path);out=tmp_path/'result'
    args=['--years','2010','--cache',str(cache),'--output',str(out)]
    assert main(args)==0
    report=json.loads((out/'REPORT.json').read_text())
    assert report['summary']['trades']>0
    assert report['summary']['end_equity_thb']==pytest.approx(
        100000+report['summary']['realized_net_thb']+report['summary']['open_unrealized_thb'])
    with np.load(out/'EQUITY.private.npz') as z:
        assert z['equity'][-1]==pytest.approx(report['summary']['end_equity_thb'])
    assert (out/'TRADES.private.csv').is_file()
    assert report['source_hashes']
    with pytest.raises(FileExistsError):
        main(args)


def test_wrong_cache_year_rejected(tmp_path):
    from run import load_prices
    cache=cache_fixture(tmp_path,2011)
    (cache/'M1_2011.private.npz').rename(cache/'M1_2010.private.npz')
    with pytest.raises(ValueError):
        load_prices(cache,[2010])


def test_yearly_cash_reconciles_when_entry_commission_paid_before_exit():
    from engine import Config, simulate
    from run import yearly_report
    last=int(np.datetime64('2010-12-31T23:58','m').astype(int))
    mins=np.arange(last,last+4,dtype=np.int64)
    mid=np.array([100.,100.,105.,110.])
    r=simulate(mins,mid,mid,{'A':np.array([(0,-1,1000,1),(2,1,1000,0)],float)},
               Config(start=100,oz=1,fx=1,spread=0,commission=.25))
    rows=yearly_report(r,[2010,2011],100)
    assert rows['2010']['realized_net_thb']==pytest.approx(-.25)
    assert rows['2011']['realized_net_thb']==pytest.approx(9.75)


@pytest.mark.parametrize('year',[2020,2021,2022])
def test_explicit_opt_in_loads_authorized_years(tmp_path,year):
    from run import load_prices
    cache=cache_fixture(tmp_path,year)
    mins,bid,ask=load_prices(cache,[year],allow_2020_2022=True)
    assert len(mins)==3000 and len(bid)==len(ask)==3000


@pytest.mark.parametrize('years',[(2023,),(2010,2020,2023),(2009,),(2024,)])
def test_opt_in_still_rejects_protected_years_before_access(tmp_path,years):
    from run import load_prices
    with pytest.raises(ValueError):
        load_prices(tmp_path/'absent',years,allow_2020_2022=True)


def test_cli_opt_in_preserves_engine_and_records_scope(tmp_path):
    from run import main,sha256,ROOT
    before=sha256(ROOT/'engine.py')
    cache=cache_fixture(tmp_path,2020);out=tmp_path/'exam-audit'
    assert main(['--years','2020','--allow-2020-2022','--cache',str(cache),'--output',str(out)])==0
    report=json.loads((out/'REPORT.json').read_text())
    assert report['years']==[2020]
    assert report['allow_2020_2022'] is True
    assert report['kind']=='engineering_correction_not_holdout_exam'
    assert sha256(ROOT/'engine.py')==before
