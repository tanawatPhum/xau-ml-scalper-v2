import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def test_training_rejects_validation_year_before_open(tmp_path):
    from study import load_prices
    with pytest.raises(ValueError):
        load_prices([2010,2017],phase='design',cache=tmp_path/'absent')


@pytest.mark.parametrize('years', [[2020],[2023],[],[2011,2010],[2010,2010]])
def test_loader_rejects_invalid_study_scope(tmp_path,years):
    from study import load_prices
    with pytest.raises(ValueError):
        load_prices(years,phase='evaluate',cache=tmp_path/'absent')


def row(net=120,dd=8,loss=40,trades=60,recent=1):
    return dict(net=net,dd=dd,loss=loss,trades=trades,recent=recent,lowest=50)


def test_selection_requires_all_objectives_and_is_deterministic():
    from study import choose
    base=row(net=100,dd=10,loss=50,trades=100,recent=-1)
    candidates=[dict(id='higher-risk',metrics=row(net=200,dd=20)),
                dict(id='rare',metrics=row(net=400,dd=1,trades=2)),
                dict(id='good',metrics=row()),dict(id='more-loss',metrics=row(loss=51))]
    selected,passed=choose(candidates,base)
    assert passed and selected['id']=='good'
    assert choose(list(reversed(candidates)),base)[0]['id']=='good'


def test_failure_is_not_presented_as_training_pass():
    from study import choose
    selected,passed=choose([dict(id='fails',metrics=row(net=101))],row(net=100,dd=10,loss=50,trades=100,recent=-1))
    assert not passed


def test_changed_lock_is_rejected(tmp_path):
    from study import write_lock, read_lock
    path=tmp_path/'LOCK.json';payload={'rules':{'A':{}},'training_end':2016}
    write_lock(path,payload)
    assert read_lock(path)==payload
    path.write_text('{}')
    with pytest.raises(ValueError):read_lock(path)


def test_input_mutation_is_rejected(tmp_path):
    from study import sha, verify_hashes
    path=tmp_path/'input';path.write_bytes(b'original')
    hashes={str(path):sha(path)}
    verify_hashes(hashes)
    path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):verify_hashes(hashes)


def test_fractional_cache_base_is_rejected(tmp_path):
    import numpy as np
    from study import load_prices
    base=int(np.datetime64('2010-01-01','m').astype(int))
    np.savez(tmp_path/'M1_2010.private.npz',base=base+.5,bid=[100.],ask=[101.])
    with pytest.raises(ValueError,match='base'):load_prices([2010],cache=tmp_path)


def test_yearly_accounting_includes_open_equity_and_worst_trade():
    from types import SimpleNamespace
    import numpy as np
    import pandas as pd
    from study import yearly
    times=np.array(['2010-01-01','2010-12-31','2011-01-01','2011-12-31'],dtype='datetime64[m]').astype(int)
    result=SimpleNamespace(equity=pd.DataFrame(dict(t_minute=times,equity=[99000.,102000.,103000.,100000.])),
                           trades=pd.DataFrame(dict(t_exit=times[:3],net_thb=[-1000.,2500.,400.])))
    rows=yearly(result,[2010,2011])
    assert rows['2010']['equity_change']==2000
    assert rows['2010']['closed_net']==1500
    assert rows['2010']['worst']==-1000
    assert rows['2010']['dd']==1000
    assert rows['2011']['equity_change']==-2000
    assert rows['2011']['dd']==3000
