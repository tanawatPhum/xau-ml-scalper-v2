"""Synthetic causality/execution checks; no market-data files."""
from datetime import datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import numpy as np
from news_signals import signals


def context(direction=1):
    mins=np.arange(50,dtype=np.int64)
    mid=np.full(50,1000.)
    mid[10:]=1000.*np.exp(direction*.001)
    eff=np.full(50,10.)
    return dict(mins=mins,mid=mid,eff=eff,calendar=SimpleNamespace(session_day=np.zeros(50,dtype=np.int64)))


def run():
    for direction in (1,-1):
        c=context(direction);side,scale,records=signals(c,[10])
        assert np.flatnonzero(side).tolist()==[14]
        assert side[14]==direction and scale[14]==1.
        assert abs(records[0]['jump_ratio']-10/(10*np.sqrt(5/60)))<1e-10
        changed=context(direction);changed['eff'][11:]=1e6
        changed['mid'][15:]=1234.
        a,b,_=signals(changed,[10]);np.testing.assert_array_equal(a,side);np.testing.assert_array_equal(b,scale)
        short={k:(v[:15] if isinstance(v,np.ndarray) else SimpleNamespace(session_day=v.session_day[:15])) for k,v in c.items()}
        a,b,_=signals(short,[10]);np.testing.assert_array_equal(a,side[:15]);np.testing.assert_array_equal(b,scale[:15])
    for missing in range(9,15):
        c=context();keep=c['mins']!=missing
        for k in ('mins','mid','eff'):c[k]=c[k][keep]
        c['calendar'].session_day=c['calendar'].session_day[keep]
        assert not signals(c,[10])[0].any()
    c=context();c['mid'][:]=1000.;assert not signals(c,[10])[0].any()
    c=context();c['eff'][10]=np.nan;assert not signals(c,[10])[0].any()
    c=context();c['calendar'].session_day[14]=1;assert not signals(c,[10])[0].any()
    try:signals(context(),[10,10])
    except ValueError:pass
    else:raise AssertionError('duplicate event accepted')
    for d,expected in [('2016-01-27',19),('2016-03-16',18),('2016-11-02',18),('2016-12-14',19)]:
        assert datetime.fromisoformat(d+'T14:00').replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc).hour==expected
    print('signal synthetic checks PASS')


if __name__=='__main__':run()
