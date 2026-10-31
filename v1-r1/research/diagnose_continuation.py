"""Training-only conditional continuation and gap-clock diagnosis; no parameter search."""
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE.parent.parent/'swing-causal-execution'))
import numpy as np
import pandas as pd
from run import load_prices

mins,bid,ask=load_prices(HERE.parent.parent/'microstructure-edge-map'/'cache',tuple(range(2010,2017)))
mid=(bid+ask)/2
t=pd.read_csv(HERE/'baseline_2010_2016.private.csv')
assert t.year.max()==2016 and t.year.min()==2010
factor=10*33.77
report={}
for horizon in (60,120):
    checkpoint=t.t_entry.to_numpy()+horizon
    idx=np.searchsorted(mins,checkpoint)
    idx=np.minimum(idx,len(mins)-1)
    # Current observed quote: only include still-open trades, and exclude missing checkpoints.
    keep=(mins[idx]==checkpoint)&(checkpoint<t.t_exit.to_numpy())
    g=t.loc[keep].copy()
    g['current_liquidation_net']=(g.side.to_numpy()*(mid[idx[keep]]-g.entry_mid.to_numpy())-.168)*factor
    g['future_change']=g.net_thb-g.current_liquidation_net
    g['state']=np.where(g.current_liquidation_net>=0,'nonnegative','negative')
    g['state_theta']=pd.cut(g.current_liquidation_net/(g.theta_usd*factor),[-np.inf,-1,0,1,np.inf]).astype(str)
    for cols in (['rule'],['rule','state'],['rule','state_theta']):
        report[f'continuation_at_{horizon}_minutes_by_{"_".join(cols)}']={str(key):{
            'n':len(h),'checkpoint_net':float(h.current_liquidation_net.sum()),
            'final_net':float(h.net_thb.sum()),'subsequent_change':float(h.future_change.sum()),
            'mean_subsequent_change':float(h.future_change.mean()),
            'fraction_subsequent_positive':float((h.future_change>0).mean())}
            for key,h in g.groupby(cols,observed=True)}
gap_i=np.flatnonzero(np.diff(mins)>30)+1
gaps=pd.DataFrame({'pre_hour':(mins[gap_i-1]//60)%24,'post_hour':(mins[gap_i]//60)%24,
                   'length':mins[gap_i]-mins[gap_i-1],
                   'pre_minute':mins[gap_i-1]%1440,'post_minute':mins[gap_i]%1440})
report['gap_clock_top20']={str(k):int(v) for k,v in gaps.groupby(['pre_hour','post_hour']).size().sort_values(ascending=False).head(20).items()}
report['gap_pre_minute_top10']={str(k):int(v) for k,v in gaps.pre_minute.value_counts().head(10).items()}
report['gap_post_minute_top10']={str(k):int(v) for k,v in gaps.post_minute.value_counts().head(10).items()}
report['gap_exit_clock']={str(k):{'n':len(g),'net':float(g.net_thb.sum()),'median_hold':float(g.hold_minutes.median())}
    for k,g in t.loc[t.exit_reason=='data_gap'].assign(entry_hour=(t.t_entry//60)%24,exit_hour=(t.t_exit//60)%24).groupby(['rule','exit_hour'])}
t['period']=np.where(t.year<=2013,'2010-2013','2014-2016')
for cols in (['rule','period','session'],['rule','period','side'],['rule','period','ratio_bin'],['rule','period','theta_bin']):
    report['stability_'+'_'.join(cols)]={str(k):{'n':len(g),'net':float(g.net_thb.sum())} for k,g in t.groupby(cols,observed=True)}
(HERE/'CONTINUATION_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if not k.startswith('stability')},indent=2))
