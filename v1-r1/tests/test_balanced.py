"""Secondary selection changes only the declared trade-count floor."""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def test_secondary_selection_relaxes_only_trade_count():
    from balanced import select
    base=dict(net=100,dd=10,loss=50,trades=100,lowest=50,recent=-10)
    def row(name,**changes):
        return dict(id=name,metrics={**base,'net':120,'dd':5,'loss':25,'trades':46,'recent':-5,**changes})
    rows=[row('good'),row('too_little_profit',net=104),row('too_much_dd',dd=9.1),
          row('too_much_loss',loss=51),row('worse_recent',recent=-11),row('bankrupt',lowest=0)]
    selected,passed=select(rows,base)
    assert passed and selected['id']=='good'
    assert select(list(reversed(rows)),base)[0]['id']=='good'


def test_secondary_selection_keeps_failure_visible():
    from balanced import select
    base=dict(net=100,dd=10,loss=50,trades=100,lowest=50,recent=-10)
    selected,passed=select([dict(id='fails',metrics=base)],base)
    assert not passed


def test_changed_comparison_data_is_rejected(tmp_path):
    import pytest
    from study import sha
    from balanced import verify_comparator
    manifest={}
    for year in range(2010,2020):
        path=tmp_path/f'M1_{year}.private.npz';path.write_bytes(b'original')
        manifest[path.name]=sha(path)
    verify_comparator(manifest,tmp_path)
    (tmp_path/'M1_2017.private.npz').write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):verify_comparator(manifest,tmp_path)
