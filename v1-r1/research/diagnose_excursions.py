"""Training-only path diagnostics; future excursion labels are never entry features."""
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
factor=10*33.77
entry_i=np.searchsorted(mins,t.t_entry.to_numpy())
exit_i=np.searchsorted(mins,t.t_exit.to_numpy())
mae=[]
mfe=[]
for row,lo,hi in zip(t.itertuples(index=False),entry_i,exit_i):
    y=row.side*10000*np.log(mid[lo:hi]/row.entry_mid)/row.theta_bps
    mae.append(float(y.min()))
    mfe.append(float(y.max()))
t['mae_theta']=mae
t['mfe_theta']=mfe
t['pre_exit_net']=(t.side.to_numpy()*(mid[exit_i-1]-t.entry_mid.to_numpy())-.168)*factor
t['last_quote_change']=t.net_thb-t.pre_exit_net
report={}
for reason in ('data_gap','stop','swing'):
    report[reason]={r:{'n':len(g),'net':float(g.net_thb.sum()),'pre_exit_net':float(g.pre_exit_net.sum()),
        'last_quote_change':float(g.last_quote_change.sum()),
        'median_last_quote_change':float(g.last_quote_change.median())}
        for r,g in t.loc[t.exit_reason==reason].groupby('rule')}
report['excursion_overlap']={}
for rule,g in t.groupby('rule'):
    report['excursion_overlap'][rule]={}
    for level in (1,1.5,2,2.5):
        hit=g.mae_theta<=-level
        winner=g.net_thb>0
        report['excursion_overlap'][rule][str(level)]={
            'winner_count':int((hit & winner).sum()),'loser_count':int((hit & ~winner).sum()),
            'fraction_of_winners':float(hit[winner].mean()),'fraction_of_losers':float(hit[~winner].mean()),
            'final_net_of_hit':float(g.loc[hit,'net_thb'].sum())}
report['net_normalized_by_theta_quantiles']={str(k):{str(q):float(v) for q,v in (g.net_thb/(g.theta_usd*factor)).quantile([0,.05,.5,.95,1]).items()}
    for k,g in t.groupby(['rule','exit_reason'])}
(HERE/'EXCURSION_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
t.to_csv(HERE/'baseline_excursions_2010_2016.private.csv',index=False)
print(json.dumps(report,indent=2))
