"""Causal boundary tests on invented quotes only; no market-file reads."""
import os
from pathlib import Path
os.environ['NUMBA_CACHE_DIR']=str(Path(__file__).resolve().parent/'numba_cache')
import numpy as np
from types import SimpleNamespace
from hypothesis import signals, SPEC
from executor import replay_absolute

def context(days=63, negative=False):
    mins=[];mid=[]
    for d in range(days):
        minute=np.arange(1440,dtype=np.int64)
        r=(.001 if d%2 else -.001) if d!=60 else (-.10 if negative else .10)
        mins.extend(d*1440+minute-180)
        mid.extend(100*np.exp(r*minute/1439))
    mins=np.array(mins,np.int64);mid=np.array(mid)
    cal=SimpleNamespace(blocked=np.zeros(len(mins),bool),deadline=np.full(len(mins),10**12,np.int64))
    return dict(mins=mins,mid=mid,eff=np.ones(len(mins)),calendar=cal)

def subset(c,keep):
    return {k:(SimpleNamespace(blocked=v.blocked[keep],deadline=v.deadline[keep]) if k=='calendar' else v[keep]) for k,v in c.items()}

def check_signals():
    c=context();s=signals(c);ix=np.flatnonzero(s['side'])
    assert ix.tolist()==[61*1440],ix
    assert s['side'][ix[0]]==-1 and s['scale'][ix[0]]==.5
    assert s['expiry'][ix[0]]==61*1440+360-180
    ref=np.array([.001 if d%2 else -.001 for d in range(60)])
    np.testing.assert_allclose(s['z'][ix[0]],(.10-ref.mean())/ref.std(ddof=1),rtol=1e-11)
    assert signals(context(negative=True))['side'][61*1440]==1
    for n in [60*1440,61*1440,61*1440+1,61*1440+7]:
        short=signals(subset(c,slice(None,n)))
        for k in ['side','scale','expiry','z']:
            np.testing.assert_array_equal(short[k],s[k][:n])
    # Missing previous date cannot carry the abnormal day into the following date.
    keep=(c['mins']+180)//1440!=61
    assert not np.any(signals(subset(c,keep))['side'])
    # Incomplete last previous day: insufficient quotes or missing near-end quote.
    day=(c['mins']+180)//1440;mod=(c['mins']+180)%1440
    for keep in [~((day==60)&(mod>=900)),~((day==60)&(mod>=1319)),~((day==60)&(mod<121))]:
        assert not np.any(signals(subset(c,keep))['side'])
    blocked=c['calendar'].blocked.copy();blocked[61*1440:61*1440+61]=True
    c['calendar'].blocked=blocked
    s=signals(c);assert np.flatnonzero(s['side']).tolist()==[61*1440+61]
    c['calendar'].blocked[61*1440:61*1440+360]=True
    assert not np.any(signals(c)['side'])
    c=context();c['eff'][61*1440]=np.nan
    assert not np.any(signals(c)['side']) # no second try on the same date

def check_executor():
    m=np.arange(9,dtype=np.int64);p=np.array([100.,100.,102.,103.,104.,105.,106.,107.,108.])
    s=np.zeros(9,np.int8);s[0]=1;scale=np.ones(9);exp=np.full(9,5,np.int64)
    b=np.zeros(9,bool);d=np.full(9,100,np.int64);h=np.full(9,.084)
    def run(mm=m,pp=p,dd=d,ss=s,ee=exp,st=np.inf,fee=0.,slip=0.):
        return replay_absolute(mm,pp,h[:len(mm)],ss[:len(mm)],scale[:len(mm)],ee[:len(mm)],b[:len(mm)],dd[:len(mm)],st,10.,33.77,fee,slip)
    t,e,x,o=run();assert t[0,1]==1 and t[0,2]==5 and t[0,6]==1 and not o
    np.testing.assert_allclose(e[-1],(5-.168)*337.7)
    earlier=d.copy();earlier[:]=3
    t,e,x,o=run(dd=earlier);assert t[0,2]==3 and t[0,6]==4
    gap=m.copy();gap[1:]+=1
    assert len(run(mm=gap)[0])==0 # exact-next-minute cancellation
    gap=m.copy();gap[5:]+=3
    assert run(mm=gap)[0][0,2]==5 # first actual quote >= expiry
    for n in [1,2,4,5,6]:
        short=run(mm=m[:n],pp=p[:n]);full=run()
        np.testing.assert_array_equal(short[1],full[1][:n])
        np.testing.assert_array_equal(short[0],full[0][full[0][:,2]<n])
        assert (short[3]!=0)==(2<=n<=5)
    t,e,_,_=run(fee=.01,slip=.02)
    np.testing.assert_allclose(t[0,5],(5-.168-.02-.04)*337.7)
    np.testing.assert_allclose(t[0,5],e[-1])
    s[0]=-1;t,e,_,_=run();np.testing.assert_allclose(t[0,5],(-5-.168)*337.7)
    t,e,_,_=run(st=1.);assert t[0,2]==3 and t[0,6]==2
    # Expiry exactly at prospective entry forbids entry.
    exp[:]=1;assert len(run()[0])==0 and run()[3]==0

if __name__=='__main__':
    check_signals();check_executor();print('PASS synthetic daily history, quality, missing dates, first eligible, expiry, exact fill, two sides, costs, prefix and EOF')
