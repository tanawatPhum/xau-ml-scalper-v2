"""Literature transfer pilots. No market reads or baseline-position filters."""
from __future__ import annotations
import numpy as np
import pandas as pd


def candidates():
    # Frozen primary; stop sensitivity is reported, never a replacement selection.
    return [dict(id="C_Xu_midday_to_close", family="Xu_midday_to_close",
                 paper_doi="10.1016/j.resourpol.2020.101830",
                 timezone="America/New_York",
                 signal_minute=15*60+29, anchor_start=11*60+30, anchor_end=12*60,
                 hold=30, stop=1e12, tp=1e12),
            dict(id="C_Ma_night_reversal_momentum",family="Ma_night_reversal_momentum",
                 paper_doi="10.1016/j.gfj.2025.101084",timezone="Asia/Shanghai",
                 signal_minute=22*60,anchor_start=21*60,anchor_end=21*60+30,
                 hold=59,stop=1e12,tp=1e12)]


def signals(c, spec):
    mid=np.asarray(c["mid"],float);mins=np.asarray(c["mins"],np.int64)
    n=len(mins);side=np.zeros(n,np.int8);scale=np.zeros(n)
    if not n:return side,scale
    ny=pd.to_datetime(mins,unit="m",utc=True).tz_convert(spec["timezone"])
    day=ny.tz_localize(None).normalize().to_numpy(dtype="datetime64[D]").astype(np.int64)
    mod=(ny.hour*60+ny.minute).to_numpy()
    eff=np.asarray(c["eff"],float)
    if not (mid.shape==mins.shape==eff.shape):raise ValueError("context shape mismatch")
    if spec["family"] not in ("Xu_midday_to_close","Ma_night_reversal_momentum"):
        raise ValueError("unknown hypothesis")
    # Exact minutes, same New York date, with no gap in the source window.
    anchors={int(day[j]):j for j in np.flatnonzero(mod==spec["anchor_start"])}
    ends={int(day[j]):j for j in np.flatnonzero(mod==spec["anchor_end"])}
    gap=np.r_[0,np.cumsum(np.diff(mins)!=1)]
    for i in np.flatnonzero(mod==spec["signal_minute"]):
        a=anchors.get(int(day[i]));b=ends.get(int(day[i]))
        if a is None or b is None or not (a<b<i):continue
        if mins[b]-mins[a]!=spec["anchor_end"]-spec["anchor_start"] or gap[b]!=gap[a]:continue
        if c["calendar"].session_day[a]!=c["calendar"].session_day[i]:continue
        if not (np.isfinite(eff[i]) and eff[i]>0):continue
        move=mid[b]-mid[a]
        if not np.isfinite(move) or move==0:continue
        if spec["family"]=="Ma_night_reversal_momentum":
            # 21:00–21:30 impulse; 21:30–22:00 opposite partial retracement.
            # At22:00 all of these prices are already observed.
            if mins[i]-mins[a]!=60 or gap[i]!=gap[a]:continue
            retrace=mid[i]-mid[b]
            if not np.isfinite(retrace) or move*retrace>=0 or abs(retrace)>=abs(move):continue
        side[i]=1 if move>0 else -1
        scale[i]=max(float(eff[i]*mid[i]/10000.),.5)
    return side,scale
