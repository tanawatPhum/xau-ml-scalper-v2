"""Close-only causal experiment executor; no orders, no future gap lookup."""
import numpy as np
from numba import njit

@njit(cache=True)
def replay(mins,mid,half,signals,scale,blocked,deadline,hold,stop,tp,oz=10.,fx=33.77,commission=0.,slip=0.):
    n=len(mins); eq=np.zeros(n); exposure=np.zeros(n)
    trades=np.zeros((n,8)); count=0; cash=0.; side=0; entry=-1; sig=-1
    fill=entrymid=dist=0.; pending=-1; exit_reason=0
    factor=oz*fx
    for i in range(n):
        now=mins[i]
        force=0
        if side:
            if now>=deadline[entry] or blocked[i]:force=4
            elif i>0 and now-mins[i-1]>30:force=5
            elif now>=mins[entry]+hold:force=1
        reason=force if force else exit_reason
        if side and reason:
            exitfill=mid[i]-side*(half[i]+slip)
            net=(side*(exitfill-fill)-2*commission)*factor
            cash+=(side*(exitfill-fill)-commission)*factor
            trades[count,:]=np.array([sig,entry,i,side,side*(mid[i]-entrymid)*factor,net,reason,dist])
            count+=1; side=0
        exit_reason=0
        if pending>=0:
            if side==0 and now==mins[pending]+1 and not blocked[i] and now<deadline[i]:
                side=signals[pending];entry=i;sig=pending;entrymid=mid[i]
                fill=mid[i]+side*(half[i]+slip);dist=scale[pending]
                cash-=commission*factor
            pending=-1
        if side:
            move=side*(mid[i]-entrymid)
            if move<=-stop*dist:exit_reason=2
            elif move>=tp*dist:exit_reason=3
        if side==0 and signals[i]!=0 and not blocked[i] and scale[i]>0 and np.isfinite(scale[i]):
            pending=i
        unreal=0.
        if side:
            liquidation=mid[i]-side*(half[i]+slip)
            unreal=(side*(liquidation-fill)-commission)*factor
        eq[i]=cash+unreal;exposure[i]=abs(side)*oz
    return trades[:count],eq,exposure,side

def smoke():
    m=np.arange(8,dtype=np.int64); p=np.array([100.,100.,102.,101.,101.,101.,101.,101.])
    half=np.full(8,.084); s=np.zeros(8,dtype=np.int8);s[0]=1
    scale=np.ones(8);b=np.zeros(8,dtype=np.bool_);d=np.full(8,100,dtype=np.int64)
    t,e,x,o=replay(m,p,half,s,scale,b,d,90,1.5,1.5)
    assert len(t)==1 and t[0,1]==1 and t[0,2]==3 # target detected2; actual exit3
    np.testing.assert_allclose(t[0,5],(1-.168)*337.7)
    np.testing.assert_allclose(e[-1],t[:,5].sum())
    a=replay(m[:3],p[:3],half[:3],s[:3],scale[:3],b[:3],d[:3],90,1.5,1.5)
    np.testing.assert_array_equal(e[:3],a[1]);assert a[3]==1 and len(a[0])==0
    mg=m.copy();mg[1:]+=1
    assert len(replay(mg,p,half,s,scale,b,d,90,1.5,1.5)[0])==0
    d[:]=2
    t,e,x,o=replay(m,p,half,s,scale,b,d,90,1.5,1.5)
    assert t[0,2]==2 and t[0,6]==4
    t,e,x,o=replay(m,p,half,s,scale,b,d,90,1.5,1.5,commission=.01,slip=.02)
    np.testing.assert_allclose(t[0,5],(2-.168-.04-.02)*337.7)
    np.testing.assert_allclose(e[-1],t[0,5])
    d[:]=100
    t,e,x,o=replay(m,np.full(8,100.),half,s,scale,b,d,2,1.5,1.5)
    assert t[0,1]==1 and t[0,2]==3 and t[0,6]==1
    print('replay synthetic checks PASS')

if __name__=='__main__':smoke()
