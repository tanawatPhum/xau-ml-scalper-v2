import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def metrics(**changes):
    return dict(net=120.,dd=8.,loss=30.,trades=600,lowest=99.,recent=5.,
                market_close_crossings=0,session_crossings=0,**changes)


def test_selection_serves_profit_and_loss_not_low_profit_ratio():
    from run_study import select
    base=metrics();base.update(net=100.,dd=10.,loss=40.,recent=0.)
    rows=[dict(id='low_profit',metrics={**metrics(),'net':90,'dd':1}),
          dict(id='higher_risk',metrics={**metrics(),'net':200,'dd':11}),
          dict(id='rare',metrics={**metrics(),'trades':20}),
          dict(id='cross_close',metrics={**metrics(),'market_close_crossings':1}),
          dict(id='good',metrics=metrics())]
    assert select(rows,base)[0]['id']=='good'
    assert select(list(reversed(rows)),base)[0]['id']=='good'


def test_no_improvement_retains_baseline_instead_of_altering_gate():
    from run_study import select
    base=metrics()
    row,passed=select([dict(id='worse',metrics={**base,'net':10})],base)
    assert not passed and row['id']=='BASE'
    assert row['stop_theta']==3.
