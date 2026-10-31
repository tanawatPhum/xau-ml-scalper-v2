"""Recurring price-path experiments. No fixed daily quota or A/B veto."""
import importlib.util,json,sys,os
from pathlib import Path
import numpy as np
from numba import njit
ROOT=Path(__file__).resolve().parent
os.environ['NUMBA_CACHE_DIR']=str(ROOT/'numba_cache')
# Avoid this file's name colliding with the frozen parent's study module.
sys.path[:]=[p for p in sys.path if Path(p or '.').resolve()!=ROOT]
sys.path.insert(0,str(ROOT.parent/'rule-c-research-20261101'))
import research_study as s

def candidates():
    return [dict(id=f'path_w{w}_k{k}_d{d}_h{h}',family='price_path',params=dict(w=w,k=k,d=d),hold=h,stop=1.,tp=2.)
            for w in (15,30,60) for k in (1,2) for d in (1,-1) for h in (30,90)]

@njit(cache=True)
def path_signals(mins,y,mid,eff,session,w,k,d):
    n=len(mins);side=np.zeros(n,np.int8);scale=np.zeros(n)
    start=0;previous=False;last=-10**12
    for i in range(n):
        if i==0 or mins[i]-mins[i-1]!=1 or session[i]!=session[i-1]:
            start=i;previous=False
        valid=False;imp=0.
        if i-start>=2*w:
            imp=y[i-w]-y[i-2*w];pull=y[i]-y[i-w]
            v=eff[i-2*w]*np.sqrt(w/60.)
            valid=np.isfinite(v) and v>0 and abs(imp)>=k*v and imp*pull<0 and .2*abs(imp)<=abs(pull)<=.5*abs(imp)
        if valid and not previous and mins[i]-last>=30:
            side[i]=d*(1 if imp>0 else -1);scale[i]=max(abs(imp)*mid[i]/10000.*.5,.5);last=mins[i]
        previous=valid
    return side,scale

def signals(c,spec):
    p=spec['params'];return path_signals(c['mins'],c['y'],c['mid'],c['eff'],c['calendar'].session_day,p['w'],p['k'],p['d'])

original_metrics=s.metrics
def metrics(c,ab,r):
    m=original_metrics(c,ab,r);sessions=c['calendar'].session_day
    ei=r[0][:,1].astype(int);traded=np.unique(sessions[ei]);n=len(np.unique(sessions))
    m.update(observed_sessions=n,traded_sessions=len(traded),zero_trade_sessions=n-len(traded),
        trades_per_session=m['trades']/n,active_session_fraction=len(traded)/n,
        net_per_trade=m['net']/max(m['trades'],1))
    return m

original_execute=s.execute
def execute(c,spec,sg,cost='fixed'):
    r=original_execute(c,spec,sg,cost)
    if cost=='example':
        cut=int(np.searchsorted(c['mins'],int(np.datetime64('2014-01-01','m').astype(int))))
        recent=float(r[1][-1]-(r[1][cut-1] if cut else 0.))
        RECENT[spec['id']]=recent
    return r
RECENT={}

def eligible(m,train=True):
    recent_example=list(RECENT.values())[-1] if RECENT else -np.inf
    m['recent_example_net']=recent_example
    return bool(m['net']>0 and m['gross_wins']>m['gross_losses'] and m['example_net']>0
        and m['trades']>=(500 if train else 150) and m['overlap']<=.30 and m['lowest']>0
        and (not train or (m['net_2014_on']>0 and recent_example>0))
        and not m['market_close_crossings'] and not m['session_crossings'] and not m['open_positions'])

def sources():
    files=[ROOT/'PLAN.md',ROOT/'study.py']+[ROOT.parent/'rule-c-research-20261101'/p for p in ('research_study.py','replay.py')]
    return {str(p):s.sha(p) for p in files}

def tests():
    from types import SimpleNamespace
    n=100;m=np.arange(n,dtype=np.int64);y=np.r_[np.linspace(0,20,31),np.linspace(19.8,12,30),np.full(39,12.)]
    c=dict(mins=m,y=y,mid=100*np.exp(y/1e4),eff=np.ones(n),calendar=SimpleNamespace(session_day=np.zeros(n,dtype=np.int64)))
    for spec in candidates():
        sg=signals(c,spec)
        for end in (30,46,61,80):
            cp={k:(v[:end] if isinstance(v,np.ndarray) else SimpleNamespace(session_day=v.session_day[:end])) for k,v in c.items()}
            sp=signals(cp,spec)
            for a,b in zip(sp,sg):np.testing.assert_array_equal(a,b[:end])
    x=next(x for x in candidates() if x['params']==dict(w=15,k=1,d=1))
    a=signals(c,x)[0];b=signals(c,{**x,'params':dict(w=15,k=1,d=-1)})[0]
    assert np.count_nonzero(a)>0;np.testing.assert_array_equal(a,-b)
    print('Synthetic direction and96 prefix checks PASS',flush=True)

if __name__=='__main__':
    tests();s.ROOT=ROOT;s.OUT=ROOT/'out';s.sources=sources;s.signals=signals;s.metrics=metrics;s.execute=execute;s.eligible=eligible
    s.reclaim.candidates=candidates;s.structure.candidates=lambda:[]
    {'design':s.design,'evaluate':s.evaluate}[sys.argv[1]]()
