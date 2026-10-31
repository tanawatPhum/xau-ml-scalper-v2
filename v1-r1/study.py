"""Bounded answer-key design on2010-16, then immutable-lock causal evaluation."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import baseline_engine as engine

ROOT=Path(__file__).resolve().parent
CACHE=ROOT.parent/'microstructure-edge-map/cache'
OUT=ROOT/'out'
POLICIES=('all','skip_asia','skip_ny','skip_late','vol_ge075','vol_ge1','vol_le15',
          'long_only','short_only','utc_morning','utc_london')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def verify_hashes(hashes):
    for path,expected in hashes.items():
        if sha(path)!=expected:raise ValueError(f'input changed during study: {path}')


def load_prices(years,phase='design',cache=CACHE):
    years=tuple(years)
    if phase not in ('design','evaluate'):raise ValueError('unknown phase')
    last=2016 if phase=='design' else 2019
    if not years or any(type(y) is not int or not 2010<=y<=last for y in years) or tuple(sorted(set(years)))!=years:
        raise ValueError(f'{phase} only permits increasing unique2010-{last} years')
    parts=[]
    for y in years:
        with np.load(Path(cache)/f'M1_{y}.private.npz',allow_pickle=False) as z:
            raw_base=z['base'];bid=z['bid'];ask=z['ask']
        if raw_base.ndim!=0 or not np.isfinite(raw_base) or raw_base!=np.floor(raw_base):
            raise ValueError('cache base must be a scalar integer minute')
        base=int(raw_base)
        lo=int(np.datetime64(f'{y}-01-01','m').astype(int));hi=int(np.datetime64(f'{y+1}-01-01','m').astype(int))
        if base!=lo or bid.ndim!=1 or ask.shape!=bid.shape or len(bid)>hi-lo:raise ValueError('invalid cache grid')
        ok=~np.isnan(bid)&~np.isnan(ask);pos=np.flatnonzero(ok)
        parts.append(engine.validate_prices(base+pos,bid[ok],ask[ok]))
    return tuple(np.concatenate([p[i] for p in parts]) for i in range(3))


def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write_lock(path,payload):
    path=Path(path)
    with path.open('x',encoding='utf-8') as f:json.dump(payload,f,indent=2,allow_nan=False)
    path.with_suffix('.sha256').write_text(sha(path)+'\n',encoding='ascii')


def read_lock(path):
    path=Path(path)
    if sha(path)!=path.with_suffix('.sha256').read_text().strip():raise ValueError('LOCK changed')
    return json.loads(path.read_text())


def metrics(result):
    s=result.summary;t=result.trades
    cut=int(np.datetime64('2014-01-01','m').astype(int))
    times=result.equity.t_minute.to_numpy();q=int(np.searchsorted(times,cut))
    before=float(result.equity.equity.iloc[q-1]) if q else 100000.
    return dict(net=s['net_equity_thb'],dd=s['max_equity_drawdown_thb'],
        dd_pct=s['max_equity_drawdown_pct'],loss=float(-t.loc[t.net_thb<0,'net_thb'].sum()),
        trades=len(t),worst=float(t.net_thb.min()) if len(t) else 0.,lowest=s['lowest_equity_thb'],
        recent=s['end_equity_thb']-before,early=before-100000.,open_positions=s['open_positions'])


def choose(candidates,base):
    def eligible(c):
        m=c['metrics']
        return (m['net']>=base['net']*1.05 and m['dd']<=base['dd']*.9 and m['loss']<=base['loss']
                and m['trades']>=base['trades']*.5 and m['lowest']>0 and m['recent']>base['recent'])
    valid=[c for c in candidates if eligible(c)]
    pool=valid or candidates
    if not pool:raise ValueError('no candidates')
    return sorted(pool,key=lambda c:(-c['metrics']['net']/max(c['metrics']['dd'],1.),c.get('complexity',0),c['id']))[0],bool(valid)


def run(context,rules,config=None):
    from strategy import build_signals
    return engine.simulate(context['mins'],context['bid'],context['ask'],build_signals(context,rules),config or engine.Config())


def key(p):return json.dumps(p,sort_keys=True)


def design():
    from strategy import prepare,BASE_RULES
    if (OUT/'LOCK.json').exists():raise FileExistsError('design already locked; do not retune')
    OUT.mkdir(parents=True,exist_ok=True)
    sources={str((ROOT/p).resolve()):sha(ROOT/p) for p in ('baseline_engine.py','strategy.py','study.py')}
    data={f'M1_{y}.private.npz':sha(CACHE/f'M1_{y}.private.npz') for y in range(2010,2017)}
    c=prepare(*load_prices(list(range(2010,2017))))
    base=metrics(run(c,BASE_RULES));write_json(OUT/'BASE_TRAIN.json',base)
    print('TRAIN BASE',json.dumps(base),flush=True)
    allrows=[];shortlists={}
    for rule in ('A','B'):
        rowmap={}
        ks=(.75,1.,1.25,1.5) if rule=='A' else (1.,1.25,1.5,2.)
        dollars=(1.5,2.1626934441569983,3.,4.) if rule=='A' else (0.,1.5,2.1626934441569983,3.)
        for k,u,leg in itertools.product(ks,dollars,(2.5,3.5,5.)):
            p=dict(k=k,long_vol=rule=='A',min_usd=u,leg=leg,policy='all')
            m=metrics(run(c,{rule:p}));row=dict(rule=rule,params=p,metrics=m)
            rowmap[key(p)]=row
        def rank(row):return (-row['metrics']['net']/max(row['metrics']['dd'],1.),key(row['params']))
        seeds=sorted(rowmap.values(),key=rank)[:3]
        seeds.append(rowmap[key(BASE_RULES[rule])])
        seeds={key(r['params']):r for r in seeds}.values()
        for seed in seeds:
            for policy in POLICIES:
                p={**seed['params'],'policy':policy}
                if key(p) not in rowmap:
                    rowmap[key(p)]=dict(rule=rule,params=p,metrics=metrics(run(c,{rule:p})))
        candidates=sorted(rowmap.values(),key=rank)
        picks=candidates[:5]
        baseline=rowmap[key(BASE_RULES[rule])]
        if key(baseline['params']) not in {key(r['params']) for r in picks}:picks.append(baseline)
        else:picks=candidates[:6]
        shortlists[rule]=picks;allrows+=list(rowmap.values())
        print('RULE',rule,'cells',len(rowmap),'top',json.dumps(picks[0]),flush=True)
        write_json(OUT/'SINGLE_RULE_TRAIN.json',allrows)
    portfolios=[]
    for i,(a,b) in enumerate(itertools.product(shortlists['A'],shortlists['B'])):
        rules={'A':a['params'],'B':b['params']};m=metrics(run(c,rules))
        complexity=sum(p[k]!=BASE_RULES[r][k] for r,p in rules.items() for k in p)
        portfolios.append(dict(id=f'P{i:02d}',rules=rules,metrics=m,complexity=complexity))
    selected,passed=choose(portfolios,base)
    write_json(OUT/'PORTFOLIO_TRAIN.json',portfolios)
    verify_hashes(sources)
    verify_hashes({str(CACHE/p):h for p,h in data.items()})
    lock=dict(locked_utc=datetime.now(timezone.utc).isoformat(),training_end=2016,rules=selected['rules'],
              selected_id=selected['id'],training_pass=passed,selected_metrics=selected['metrics'],baseline_metrics=base,
              single_rule_cells=len(allrows),portfolio_cells=len(portfolios),source_hashes=sources,training_data_hashes=data,
              policy='no redesign after2017-2019; no2020+ reads',config=asdict(engine.Config()))
    write_lock(OUT/'LOCK.json',lock)
    print('LOCKED',json.dumps(lock),flush=True)


def yearly(result,years):
    rows={};prev=100000.
    for yr in years:
        lo=int(np.datetime64(f'{yr}-01-01','m').astype(int));hi=int(np.datetime64(f'{yr+1}-01-01','m').astype(int))
        q=result.equity.loc[(result.equity.t_minute>=lo)&(result.equity.t_minute<hi)]
        t=result.trades.loc[(result.trades.t_exit>=lo)&(result.trades.t_exit<hi)]
        e=q.equity.to_numpy();peak=np.maximum.accumulate(np.r_[prev,e])[1:]
        end=float(e[-1]) if len(e) else prev
        rows[str(yr)]=dict(trades=len(t),closed_net=float(t.net_thb.sum()),equity_change=end-prev,end_equity=end,
                          dd=float((peak-e).max()) if len(e) else 0.,loss=float(-t.loc[t.net_thb<0,'net_thb'].sum()),
                          worst=float(t.net_thb.min()) if len(t) else 0.)
        prev=end
    return rows


def save_result(folder,result,years,config):
    folder.mkdir(parents=True,exist_ok=False)
    write_json(folder/'REPORT.json',dict(summary=result.summary,metrics=metrics(result),yearly=yearly(result,years),config=asdict(config)))
    result.trades.to_csv(folder/'TRADES.private.csv',index=False)
    np.savez_compressed(folder/'EQUITY.private.npz',**{c:result.equity[c].to_numpy() for c in result.equity})
    result.open_positions.to_json(folder/'OPEN.private.json',orient='records',indent=2)


def evaluate():
    from strategy import prepare,BASE_RULES
    lock=read_lock(OUT/'LOCK.json')
    verify_hashes(lock['source_hashes'])
    verify_hashes({str(CACHE/p):h for p,h in lock['training_data_hashes'].items()})
    if (OUT/'evaluation').exists():raise FileExistsError('evaluation already exists; no automatic rerun')
    data={f'M1_{y}.private.npz':sha(CACHE/f'M1_{y}.private.npz') for y in range(2010,2020)}
    configs={'fixed':engine.Config(),'cost_example':engine.Config(commission=.01,slippage=.02),
             'historical':engine.Config(cost_mode='historical')}
    results={}
    for period,years in [('full',list(range(2010,2020))),('validation',[2017,2018,2019])]:
        c=prepare(*load_prices(years,phase='evaluate'))
        results[period]={}
        for scenario,cfg in configs.items():
            results[period][scenario]={}
            for name,rules in [('baseline',BASE_RULES),('rx',lock['rules'])]:
                r=run(c,rules,cfg);results[period][scenario][name]=metrics(r)
                save_result(OUT/'evaluation'/period/scenario/name,r,years,cfg)
                print(period,scenario,name,json.dumps(metrics(r)),flush=True)
    val=results['validation']['fixed'];b=val['baseline'];r=val['rx']
    confirmed=r['net']>b['net'] and r['dd']<b['dd'] and r['loss']<b['loss']
    verify_hashes(lock['source_hashes'])
    verify_hashes({str(CACHE/p):h for p,h in data.items()})
    verdict=dict(training_pass=lock['training_pass'],validation_both_objectives=confirmed,
        status='IMPROVED_ON_REUSED_VALIDATION' if lock['training_pass'] and confirmed else 'NOT_CONFIRMED',
        results=results,lock_sha256=sha(OUT/'LOCK.json'),finished_utc=datetime.now(timezone.utc).isoformat(),
        input_hashes=data)
    write_json(OUT/'EVALUATION.json',verdict)
    print('VERDICT',verdict['status'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['design','evaluate'])
    args=p.parse_args();design() if args.phase=='design' else evaluate()
