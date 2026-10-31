"""Observed-close executor with absolute per-signal expiry. No future gap lookup or EOF close."""
import numpy as np
from numba import njit

@njit(cache=True)
def replay_absolute(mins,mid,half,signals,scale,expiry,blocked,deadline,stop=np.inf,
                    oz=10.,fx=33.77,commission=0.,slip=0.):
    n=len(mins);eq=np.zeros(n);exposure=np.zeros(n);trades=np.zeros((n,8))
    count=0;cash=0.;side=0;entry=-1;sig=-1;fill=0.;entrymid=0.;dist=0.
    pending=-1;exit_reason=0;absolute=0;factor=oz*fx
    for i in range(n):
        now=mins[i];force=0
        if side:
            if now>=deadline[entry] or blocked[i]:force=4
            elif now>=absolute:force=1
        reason=force if force else exit_reason
        if side and reason:
            exitfill=mid[i]-side*(half[i]+slip)
            net=(side*(exitfill-fill)-2*commission)*factor
            cash+=(side*(exitfill-fill)-commission)*factor
            trades[count,:]=np.array([sig,entry,i,side,side*(mid[i]-entrymid)*factor,net,reason,dist])
            count+=1;side=0
        exit_reason=0
        if pending>=0:
            if side==0 and now==mins[pending]+1 and not blocked[i] and now<deadline[i] and now<expiry[pending]:
                side=signals[pending];entry=i;sig=pending;entrymid=mid[i]
                fill=mid[i]+side*(half[i]+slip);dist=scale[pending];absolute=expiry[pending]
                cash-=commission*factor
            pending=-1
        if side and side*(mid[i]-entrymid)<=-stop*dist:exit_reason=2
        if side==0 and signals[i]!=0 and not blocked[i] and np.isfinite(scale[i]) and scale[i]>0:
            pending=i
        unreal=0.
        if side:
            liquidation=mid[i]-side*(half[i]+slip)
            unreal=(side*(liquidation-fill)-commission)*factor
        eq[i]=cash+unreal;exposure[i]=abs(side)*oz
    return trades[:count],eq,exposure,side
