"""Frozen event impulse; metadata supplied explicitly and no filesystem I/O."""
import numpy as np


def signals(c,event_minutes):
    mins=np.asarray(c['mins'],np.int64);mid=np.asarray(c['mid'],float);eff=np.asarray(c['eff'],float)
    if not (mins.shape==mid.shape==eff.shape):raise ValueError('context shape mismatch')
    if np.any(np.diff(mins)<=0):raise ValueError('quote timestamps not unique and increasing')
    if len(set(event_minutes))!=len(event_minutes):raise ValueError('duplicate event timestamp')
    side=np.zeros(len(mins),np.int8);scale=np.zeros(len(mins));records=[]
    for event in sorted(event_minutes):
        row=dict(event_utc_minute=int(event),status='window_unavailable');records.append(row)
        e=int(np.searchsorted(mins,event));a=e-1;i=e+4
        if a<0 or i>=len(mins):continue
        if not np.array_equal(mins[a:i+1],np.arange(event-1,event+5)):continue
        if c['calendar'].session_day[a]!=c['calendar'].session_day[i]:
            row['status']='different_session';continue
        if not (np.isfinite(mid[a:i+1]).all() and (mid[a:i+1]>0).all()):continue
        if not (np.isfinite(eff[e]) and eff[e]>0):
            row['status']='pre_event_volatility_unavailable';continue
        impulse=float(10000*np.log(mid[i]/mid[a]))
        ratio=float(abs(impulse)/(eff[e]*np.sqrt(5/60)))
        row.update(impulse_bps=impulse,jump_ratio=ratio,pre_event_eff_bps=float(eff[e]),
                   scale_usd=float(max(eff[e]*mid[a]/10000,.5)))
        if impulse==0 or ratio<2:
            row['status']='below_fixed_jump_threshold';continue
        side[i]=1 if impulse>0 else -1;scale[i]=row['scale_usd']
        row.update(status='signal',signal_utc_minute=int(mins[i]),expected_entry_utc_minute=int(event+5))
    return side,scale,records
