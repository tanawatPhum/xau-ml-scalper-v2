"""Frozen replay/cost/guard integration using synthetic quotes only."""
from types import SimpleNamespace
import numpy as np
from news_signals import signals
from run_diagnostic import lib, permitted, SPEC, CACHE, numba
from test_synthetic import context


def run():
    assert numba.config.CACHE_DIR==str(CACHE)
    for bad in ([2017,2018,2019],[2020],[2010,2020],list(range(2010,2023))):
        try:permitted(bad)
        except ValueError:pass
        else:raise AssertionError('forbidden years accepted')
    permitted(list(range(2010,2017)))
    c=context();n=len(c['mins'])
    c['bid']=c['mid']-.084;c['ask']=c['mid']+.084
    c['calendar'].blocked=np.zeros(n,dtype=np.bool_)
    c['calendar'].deadline=np.full(n,100,dtype=np.int64)
    side,scale,_=signals(c,[10]);r=lib.execute(c,SPEC,(side,scale))
    assert len(r[0])==1 and r[0][0,0]==14 and r[0][0,1]==15 and r[0][0,2]==30
    np.testing.assert_allclose(r[0][0,5],-.168*337.7,atol=1e-8)
    extra=lib.execute(c,SPEC,(side,scale),'example')
    np.testing.assert_allclose(extra[0][0,5],-(.168+.04+.02)*337.7,atol=1e-8)
    missing=c.copy();keep=c['mins']!=15
    for k in ('mins','mid','bid','ask','eff'):missing[k]=c[k][keep]
    missing['calendar']=SimpleNamespace(**{k:getattr(c['calendar'],k)[keep] for k in ('session_day','blocked','deadline')})
    a,b,_=signals(missing,[10]);assert len(lib.execute(missing,SPEC,(a,b))[0])==0
    adverse=c.copy();adverse['mid']=c['mid'].copy();adverse['mid'][18:]-=4.
    st=lib.execute(adverse,SPEC,(side,scale),stop=3.)
    assert st[0][0,2]==19 and st[0][0,6]==2
    # Union membership is binary: simultaneous A and B positions count one C entry.
    assert lib.overlap_count(np.array([0.,10.,20.,0.]),np.array([1,2,3]))==2
    lib.replay.py_func  # Confirm reused compiled executor exposes the original implementation.
    print('execution, costs, overlap and forbidden-year synthetic checks PASS')


if __name__=='__main__':run()
