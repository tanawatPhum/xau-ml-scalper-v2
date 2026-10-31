"""Daily-flat RX design2010-2016; immutable selection; reused evaluation2010-2019."""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import itertools
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import study
from strategy import BASE_RULES,POLICIES,prepare,build_signals
from calendar_rules import schedule,manifest
import execution as engine

OUT=ROOT/'out'
P20={'A':dict(BASE_RULES['A'],policy='long_only'),
     'B':dict(k=2.,long_vol=False,min_usd=3.,leg=3.5,policy='vol_le15')}


def sources():
    paths=[ROOT/p for p in ('calendar_rules.py','execution.py','run_study.py','DESIGN.md')]
    paths += [ROOT.parent/p for p in ('baseline_engine.py','strategy.py','study.py')]
    return {str(p.resolve()):study.sha(p) for p in paths}


def data_hashes(years):return {str((study.CACHE/f'M1_{y}.private.npz').resolve()):study.sha(study.CACHE/f'M1_{y}.private.npz') for y in years}


def context(mins,bid,ask):
    cal=schedule(mins);keep=cal.available
    c=prepare(mins[keep],bid[keep],ask[keep])
    c['calendar']=schedule(c['mins'])
    c['raw_quotes']=len(mins);c['excluded_quotes']=int((~keep).sum())
    return c


def load(years,phase):return context(*study.load_prices(years,phase=phase))


def run(c,rules,stop_theta=3.,config=None):
    return engine.simulate(c['mins'],c['bid'],c['ask'],build_signals(c,rules),
        config or engine.Config(),stop_theta=stop_theta,calendar=c['calendar'])


def metrics(result):
    return {**study.metrics(result),**{k:result.diagnostics[k] for k in (
        'late_cutoff_exits','market_close_crossings','session_crossings','trades_spanning_data_gap','scheduled_exits')}}


def select(candidates,base):
    eligible=[r for r in candidates if r['metrics']['net']>base['net']
        and r['metrics']['dd']<base['dd'] and r['metrics']['loss']<=base['loss']
        and r['metrics']['recent']>=base['recent'] and r['metrics']['lowest']>0
        and r['metrics']['trades']>=500 and r['metrics']['market_close_crossings']==0
        and r['metrics']['session_crossings']==0]
    if not eligible:return dict(id='BASE',rules=BASE_RULES,stop_theta=3.,metrics=base),False
    return sorted(eligible,key=lambda r:(-r['metrics']['net']/max(r['metrics']['dd'],1.),r.get('complexity',0),r['id']))[0],True


def save(folder,result,years,c):
    study.save_result(folder,result,years,c)
    path=folder/'REPORT.json';doc=json.loads(path.read_text())
    doc.update(metrics=metrics(result),diagnostics=result.diagnostics)
    study.write_json(path,doc)


def check():
    OUT.mkdir(exist_ok=True)
    before=sources();data=data_hashes([2010])
    c=load([2010],'design');rows=[]
    for name,rules in [('baseline',BASE_RULES),('old_rx',P20)]:
        full=run(c,rules)
        start=int(np.datetime64('2010-09-01','m').astype(int))
        pos=np.flatnonzero((c['mins']>=start)&(full.equity.gross_oz.to_numpy()>0))
        assert len(pos),'need a nonempty open-position prefix'
        for n in [int(np.searchsorted(c['mins'],start)),int(pos[0])+1]:
            short=context(c['mins'][:n],c['bid'][:n],c['ask'][:n])
            for col in ('s60','sl','eff','y'):
                np.testing.assert_array_equal(short[col],c[col][:n])
            a,b=build_signals(short,rules),build_signals(c,rules)
            for rule in a:np.testing.assert_array_equal(a[rule],b[rule][b[rule][:,0]<n])
            result=run(short,rules)
            np.testing.assert_array_equal(result.equity.to_numpy(),full.equity.iloc[:n].to_numpy())
            expected=full.trades[full.trades.t_exit<=short['mins'][-1]].reset_index(drop=True)
            import pandas as pd
            pd.testing.assert_frame_equal(result.trades,expected,check_exact=True)
            rows.append(dict(name=name,quotes=n,last_minute=int(short['mins'][-1]),
                             trades=len(result.trades),open_positions=result.summary['open_positions']))
    study.verify_hashes(before);study.verify_hashes(data)
    study.write_json(OUT/'CAUSAL_CHECKS.json',dict(status='PASS',checks=rows,source_hashes=before,data_hashes=data))
    print('ACTUAL PREFIX CHECKS PASS',json.dumps(rows),flush=True)


def design():
    if (OUT/'LOCK.json').exists():raise FileExistsError('already locked; no retuning')
    OUT.mkdir(exist_ok=True)
    source=sources();data=data_hashes(list(range(2010,2017)))
    study.write_json(OUT/'CALENDAR.json',manifest())
    c=load(list(range(2010,2017)),'design')
    base=metrics(run(c,BASE_RULES));old=metrics(run(c,P20))
    study.write_json(OUT/'BASE_TRAIN.json',base);study.write_json(OUT/'OLD_RX_TRAIN.json',old)
    print('DAILY BASE TRAIN',json.dumps(base),flush=True)
    allrows=[];picks={}
    for rule in ('A','B'):
        rows={}
        ks=(.75,1.,1.25,1.5) if rule=='A' else (1.,1.25,1.5,2.)
        floors=(1.5,2.1626934441569983,3.,4.) if rule=='A' else (0.,1.5,2.1626934441569983,3.)
        def add(p):
            k=study.key(p)
            if k not in rows:rows[k]=dict(rule=rule,params=p,metrics=metrics(run(c,{rule:p})))
        for k,u,leg in itertools.product(ks,floors,(2.5,3.5,5.)):
            add(dict(k=k,long_vol=rule=='A',min_usd=u,leg=leg,policy='all'))
        by_ratio=lambda r:(-r['metrics']['net']/max(r['metrics']['dd'],1.),study.key(r['params']))
        by_net=lambda r:(-r['metrics']['net'],study.key(r['params']))
        seedrows=sorted(rows.values(),key=by_ratio)[:3]+sorted(rows.values(),key=by_net)[:2]
        seedparams=[r['params'] for r in seedrows]+[BASE_RULES[rule],P20[rule]]
        seeds={study.key({**p,'policy':'all'}):{**p,'policy':'all'} for p in seedparams}
        for p in seeds.values():
            for policy in POLICIES:add({**p,'policy':policy})
        chosen=[rows[study.key(BASE_RULES[rule])],rows[study.key(P20[rule])]]
        chosen+=sorted(rows.values(),key=by_net)[:3]+sorted(rows.values(),key=by_ratio)[:3]
        picks[rule]=list({study.key(r['params']):r for r in chosen}.values())
        allrows+=list(rows.values());study.write_json(OUT/'SINGLE_RULE_TRAIN.json',allrows)
        print('DAILY RULE',rule,'cells',len(rows),'shortlist',len(picks[rule]),flush=True)
    portfolios=[]
    for i,(a,b,stop) in enumerate(itertools.product(picks['A'],picks['B'],(2.,2.5,3.))):
        rules={'A':a['params'],'B':b['params']}
        complexity=sum(p[k]!=BASE_RULES[r][k] for r,p in rules.items() for k in p)+int(stop!=3.)
        portfolios.append(dict(id=f'D{i:03d}',rules=rules,stop_theta=stop,complexity=complexity,metrics=metrics(run(c,rules,stop))))
    selected,passed=select(portfolios,base)
    study.write_json(OUT/'PORTFOLIO_TRAIN.json',portfolios)
    study.verify_hashes(source);study.verify_hashes(data)
    lock=dict(locked_utc=datetime.now(timezone.utc).isoformat(),training_end=2016,selected=selected,training_pass=passed,
        baseline_metrics=base,old_rx_metrics=old,single_rule_cells=len(allrows),portfolio_cells=len(portfolios),
        source_hashes=source,training_data_hashes=data,calendar_hash=study.sha(OUT/'CALENDAR.json'),
        raw_quotes=c['raw_quotes'],retained_quotes=len(c['mins']),excluded_quotes=c['excluded_quotes'],
        config=asdict(engine.Config()),validation='Reused/exploratory2017-2019; no post-lock redesign')
    study.write_lock(OUT/'LOCK.json',lock)
    print('DAILY LOCK',json.dumps({k:lock[k] for k in ('locked_utc','selected','training_pass','single_rule_cells','portfolio_cells')}),flush=True)


def evaluate():
    lock=study.read_lock(OUT/'LOCK.json')
    study.verify_hashes(lock['source_hashes']);study.verify_hashes(lock['training_data_hashes'])
    if study.sha(OUT/'CALENDAR.json')!=lock['calendar_hash']:raise ValueError('calendar changed')
    if (OUT/'evaluation').exists():raise FileExistsError('already evaluated')
    data=data_hashes(list(range(2010,2020)))
    scenarios={'fixed':engine.Config(),'cost_example':engine.Config(commission=.01,slippage=.02),'historical':engine.Config(cost_mode='historical')}
    selected=lock['selected'];results={};scopes={}
    for period,years in [('full',list(range(2010,2020))),('validation',[2017,2018,2019])]:
        c=load(years,'evaluate');results[period]={}
        scopes[period]=dict(raw_quotes=c['raw_quotes'],retained_quotes=len(c['mins']),excluded_quotes=c['excluded_quotes'])
        for scenario,cfg in scenarios.items():
            results[period][scenario]={}
            for name,rules,stop in [('baseline',BASE_RULES,3.),('old_rx',P20,3.),('rx',selected['rules'],selected['stop_theta'])]:
                r=run(c,rules,stop,cfg);m=metrics(r)
                results[period][scenario][name]=m
                save(OUT/'evaluation'/period/scenario/name,r,years,cfg)
                print(period,scenario,name,json.dumps(m),flush=True)
    v=results['validation']['fixed'];b=v['baseline'];r=v['rx']
    passed=(r['net']>b['net'] and r['dd']<b['dd'] and r['loss']<=b['loss']
            and r['market_close_crossings']==0 and r['session_crossings']==0)
    study.verify_hashes(lock['source_hashes']);study.verify_hashes(data)
    if study.sha(OUT/'CALENDAR.json')!=lock['calendar_hash']:raise ValueError('calendar changed')
    doc=dict(results=results,scopes=scopes,training_pass=lock['training_pass'],validation_pass=passed,
        status='IMPROVED_ON_REUSED_VALIDATION' if lock['training_pass'] and passed else 'NOT_CONFIRMED',
        lock_sha256=study.sha(OUT/'LOCK.json'),source_hashes=lock['source_hashes'],data_hashes=data,
        finished_utc=datetime.now(timezone.utc).isoformat())
    study.write_json(OUT/'EVALUATION.json',doc)
    print('DAILY VERDICT',doc['status'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['check','design','evaluate'])
    args=parser.parse_args();{'check':check,'design':design,'evaluate':evaluate}[args.phase]()
