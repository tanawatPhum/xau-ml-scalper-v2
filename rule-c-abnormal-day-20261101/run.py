"""Frozen single-hypothesis experiment; market reads guarded by period and lock."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,sys
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out';CACHE=ROOT/'numba_cache'
os.environ['NUMBA_CACHE_DIR']=str(CACHE)
sys.path.insert(0,str(ROOT.parent/'v1-r2'))
import v1_r2 as v
sys.path.insert(0,str(ROOT.parent/'rule-c-literature-20261101'))
import trial as old
os.environ['NUMBA_CACHE_DIR']=str(CACHE)
import numba,numpy as np,pandas as pd
numba.config.CACHE_DIR=str(CACHE)
sys.path.insert(0,str(ROOT))
from hypothesis import SPEC,signals
from executor import replay_absolute
from test_synthetic import check_signals,check_executor

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def sources():
    pp=[ROOT/f for f in ['PLAN.md','hypothesis.py','executor.py','test_synthetic.py','run.py']]
    pp += [ROOT.parent/'rule-c-literature-20261101'/f for f in ['trial.py','signals.py']]
    pp += [ROOT.parent/'rule-c-research-20261101'/'replay.py',v.ROOT/'v1_r2.py',v.ROOT/'PLAN.md',v.OUT/'LOCK.json',v.OUT/'LOCK.sha256']
    pp += list(v.d.sources())
    return {str(Path(p).resolve()):sha(p) for p in pp}
def verify_sources(expected):
    assert sources()==expected,'frozen source changed'
def checks():
    check_signals();check_executor();old.guards()
    for yy,phase in [([2017],'training'),([2020],'validation'),([2016,2017],'validation')]:
        try:permitted(yy,phase)
        except ValueError:pass
        else:raise AssertionError('year guard failed')
def permitted(years,phase):
    allowed={'training':list(range(2010,2017)),'validation':[2017,2018,2019],'history':[2016]}
    if phase not in allowed or years!=allowed[phase]:raise ValueError('forbidden market-year scope')
    if phase in ('validation','history'):
        lock=json.loads((OUT/'LOCK.json').read_text(encoding='utf-8'))
        assert sha(OUT/'LOCK.json')==(OUT/'LOCK.sha256').read_text().strip()
        if not lock['selected']:raise ValueError('failed training forbids validation/history reads')
def load(years,phase):
    permitted(years,phase)
    return v.add_session(v.d.load(years,'design' if phase=='training' else 'evaluate'))
def baseline(c,train):
    base,ov=old.guards();ab=v.run(c,base['rules'],ov,base['stop_theta'])
    actual=v.d.metrics(ab)
    if train:
        expected=v.read_lock()[0]['training_metrics']
        for k in ('net','dd','trades','recent','open_positions'):
            np.testing.assert_allclose(actual[k],expected[k],atol=1e-6,rtol=0)
    return ab,actual
def execute(c,sg,cost='fixed',stop=np.inf):
    half=(c['ask']-c['bid'])/2 if cost=='historical' else np.full(len(c['mins']),.084)
    fee,slip=(.01,.02) if cost=='example' else (0.,0.)
    return replay_absolute(c['mins'],c['mid'],half,sg['side'],sg['scale'],sg['expiry'],
                           c['calendar'].blocked,c['calendar'].deadline,stop,10.,33.77,fee,slip)
def eligibility(m,train):
    result=old.eligibility(m,train)
    result['checks']['positive_equity_C_and_combined']=m['lowest']>0 and m['combined_lowest']>0
    result['eligible']=bool(all(result['checks'].values()))
    result['failed']=[k for k,val in result['checks'].items() if not val]
    return result
def accounting(c,ab,r,cost):
    t,e,ex,opened=r;n=len(e);half=(c['ask']-c['bid'])/2 if cost=='historical' else np.full(n,.084)
    fee,slip=(.01,.02) if cost=='example' else (0.,0.)
    independent=np.zeros(n);factor=337.7;cash=0.;cursor=0
    for row in t:
        si,ei,xi=int(row[0]),int(row[1]),int(row[2]);side=int(row[3])
        assert c['mins'][ei]==c['mins'][si]+1
        gross=side*(c['mid'][xi]-c['mid'][ei])*factor
        net=gross-(half[ei]+half[xi]+2*slip+2*fee)*factor
        np.testing.assert_allclose(net,row[5],atol=1e-7,rtol=1e-10)
        independent[cursor:ei]=cash
        path=side*(c['mid'][ei:xi]-c['mid'][ei])-(half[ei]+half[ei:xi]+2*slip+2*fee)
        independent[ei:xi]=cash+path*factor
        cash+=net;cursor=xi
    if not opened:
        independent[cursor:]=cash
        np.testing.assert_allclose(independent,e,atol=1e-6,rtol=1e-10)
    # Independently reconstruct A/B union from half-open holding intervals.
    starts=ab.trades.t_entry.to_numpy();ends=ab.trades.t_exit.to_numpy()
    entrytime=c['mins'][t[:,1].astype(np.int64)]
    interval_union=np.array([np.any((starts<=x)&(ends>x)) for x in entrytime])
    exposure_union=ab.equity.gross_oz.to_numpy()[t[:,1].astype(np.int64)]>0
    np.testing.assert_array_equal(interval_union,exposure_union)
    return dict(status='PASS',closed_trades=len(t),minute_equity_checked=not bool(opened),
                independent_overlap_count=int(interval_union.sum()))
def prefix_checks(c,sg,r,history):
    ix=np.flatnonzero(sg['side']);cuts=[]
    if len(ix):
        first=int(ix[0]);cuts.extend([first,first+1,first+2])
    active=np.flatnonzero(r[2]>0)
    if len(active):cuts.append(int(active[min(10,len(active)-1)])+1)
    rows=[]
    for n in sorted(set(x for x in cuts if x>0)):
        cp=v.add_session(v.d.context(c['mins'][:n],c['bid'][:n],c['ask'][:n]))
        sp=signals(cp,history)
        for k in ['side','scale','expiry','z']:np.testing.assert_array_equal(sp[k],sg[k][:n])
        rp=execute(cp,sp);np.testing.assert_array_equal(rp[1],r[1][:n])
        np.testing.assert_array_equal(rp[0],r[0][r[0][:,2]<n])
        rows.append(dict(quotes=n,last_minute=int(cp['mins'][-1]),open_at_cut=int(rp[3]!=0)))
    return dict(status='PASS',cuts=rows)
def study(c,ab,train,history=None):
    sg=signals(c,history);results={};verify={};primary=None
    for label,stop in [('primary',np.inf),('stop3_sensitivity',3.)]:
        costs={};rr={}
        for cost in ('fixed','example','historical'):
            r=execute(c,sg,cost,stop);m=old.metrics(c,ab,r)
            verify[label+'_'+cost]=accounting(c,ab,r,cost)
            costs[cost]=dict(metrics=m,annual=old.annual(c,r));rr[cost]=r
        m=costs['fixed']['metrics'];m['example_net']=costs['example']['metrics']['net'];m['historical_net']=costs['historical']['metrics']['net']
        m.update(eligibility(m,train));results[label]=costs
        if label=='primary':primary=rr['fixed']
        print(('training' if train else 'validation'),label,json.dumps(m),flush=True)
    verify['prefix']=prefix_checks(c,sg,primary,history)
    t=primary[0];entry=t[:,1].astype(np.int64);exit=t[:,2].astype(np.int64);sig=t[:,0].astype(np.int64)
    expiry=np.minimum(sg['expiry'][sig],c['calendar'].deadline[entry])
    actual_exit=c['mins'][exit]
    assert np.all(actual_exit>=expiry) # primary has time/calendar exits only
    assert np.all((exit==0)|(c['mins'][exit-1]<expiry)) # first observed quote at deadline
    diag=dict(signals=int((sg['side']!=0).sum()),closed_trades=len(t),
              signals_not_filled=int((sg['side']!=0).sum())-len(t)-int(primary[3]!=0),
              early_NY_daily_deadline=int((c['calendar'].deadline[entry]<sg['expiry'][sig]).sum()),
              exit_at_06_or_later=int((c['calendar'].deadline[entry]>=sg['expiry'][sig]).sum()),
              late_absolute_expiry=int((actual_exit>expiry).sum()),
              last_quote_utc=str(pd.to_datetime(c['mins'][-1],unit='m',utc=True)))
    period='TRAINING' if train else 'VALIDATION'
    np.savez_compressed(OUT/(period+'.private.npz'),mins=c['mins'],trades=primary[0],equity_change=primary[1],
                        exposure=primary[2],signal_index=np.flatnonzero(sg['side']),signal_side=sg['side'][sg['side']!=0],
                        signal_z=sg['z'][sg['side']!=0],ab_equity=ab.equity.equity.to_numpy())
    return dict(spec=SPEC,results=results,counts=sg['counts'],execution=diag),verify
def freeze():
    OUT.mkdir(exist_ok=True)
    manifest=OUT/'INPUTS.json';amendment=None
    if manifest.exists():
        assert not (OUT/'TRAINING.json').exists() and not (OUT/'LOCK.json').exists()
        manifest=OUT/'INPUTS_v2.json'
        if manifest.exists():raise FileExistsError('protocol already amended')
        amendment=dict(previous_manifest_sha256=sha(OUT/'INPUTS.json'),
                       reason='Pre-outcome review: verify locked2016 history digest and training artifact on validation; correct inaccurate comment. No hypothesis or market outcomes changed.')
    checks();src=sources();data=v.d.data_hashes(list(range(2010,2017)))
    write(manifest,dict(frozen_utc=now(),sources=src,data_hashes=data,spec=SPEC,market_outcomes_read=False,amendment=amendment))
    manifest.with_suffix('.sha256').write_text(sha(manifest),encoding='ascii')
    print('FROZEN before market outcomes',manifest.name,sha(manifest),flush=True)
def design():
    if (OUT/'LOCK.json').exists():raise FileExistsError('already locked; no retuning')
    manifest=OUT/('INPUTS_v2.json' if (OUT/'INPUTS_v2.json').exists() else 'INPUTS.json')
    frozen=json.loads(manifest.read_text(encoding='utf-8'))
    assert sha(manifest)==manifest.with_suffix('.sha256').read_text().strip()
    verify_sources(frozen['sources']);v.d.study.verify_hashes(frozen['data_hashes']);checks()
    c=load(list(range(2010,2017)),'training');ab,bm=baseline(c,True)
    print('BASELINE_REPRODUCED',json.dumps(bm),flush=True)
    row,verification=study(c,ab,True)
    verify_sources(frozen['sources']);v.d.study.verify_hashes(frozen['data_hashes'])
    selected=[SPEC] if row['results']['primary']['fixed']['metrics']['eligible'] else []
    write(OUT/'TRAINING.json',dict(status='PASS' if selected else 'FAILED',row=row,ab_metrics=bm,
                                  years_read=list(range(2010,2017)),finished_utc=now()))
    lock=dict(locked_utc=now(),sources=frozen['sources'],training_data_hashes=frozen['data_hashes'],
              selected=selected,all_primary_specs=[SPEC],input_file=manifest.name,input_sha256=sha(manifest),
              training_sha256=sha(OUT/'TRAINING.json'),sensitivity_selection=False)
    write(OUT/'LOCK.json',lock);(OUT/'LOCK.sha256').write_text(sha(OUT/'LOCK.json'),encoding='ascii')
    write(OUT/'VERIFICATION.json',dict(status='PASS',checks=verification,baseline_reproduced=True,
          source_hash_before=frozen['sources'],source_hash_after=sources(),data_hashes_unchanged=True))
    print('LOCKED selected',len(selected),flush=True)
def evaluate():
    if (OUT/'VALIDATION.json').exists():raise FileExistsError('already evaluated')
    lock=json.loads((OUT/'LOCK.json').read_text(encoding='utf-8'))
    assert sha(OUT/'LOCK.json')==(OUT/'LOCK.sha256').read_text().strip();verify_sources(lock['sources'])
    assert sha(OUT/'TRAINING.json')==lock['training_sha256'],'locked training result changed'
    v.d.study.verify_hashes(lock['training_data_hashes'])
    if not lock['selected']:
        write(OUT/'VALIDATION.json',dict(status='NOT_OPENED_TRAINING_FAILED',years_read=[],rows=[],prices_2020_plus_read=False));return
    permitted([2016],'history');h=load([2016],'history')
    # Read only completed 2016 daily aggregates, never positions or warmed eff.
    history=signals(h)['completed_days']
    # Last observed 2016 date is intentionally not needed: December blackout/weekend means
    # it is invalid. Validate that explicitly rather than silently dropping a valid date.
    d=(h['mins']+180)//1440;mask=d==d[-1];mod=(h['mins'][mask]+180)%1440
    assert mask.sum()<1000 or mod[0]>120 or mod[-1]<1320,'last 2016 day needs explicit completion treatment'
    history=[x for x in history if str(np.datetime64(x['day'],'D')).startswith('2016')][-61:]
    data=v.d.data_hashes([2017,2018,2019]);c=load([2017,2018,2019],'validation');ab,bm=baseline(c,False)
    row,verification=study(c,ab,False,history)
    verify_sources(lock['sources']);v.d.study.verify_hashes(data);v.d.study.verify_hashes(lock['training_data_hashes'])
    write(OUT/'VALIDATION.json',dict(status='EXPLORATORY_PASS' if row['results']['primary']['fixed']['metrics']['eligible'] else 'NOT_CONFIRMED',
       row=row,ab_metrics=bm,verification=verification,years_read=[2017,2018,2019],feature_history_years=[2016],
       feature_history=history,ab_start_fresh=True,C_eff_start_fresh=True,data_hashes=data,prices_2020_plus_read=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['freeze','design','evaluate']);a=ap.parse_args()
    {'freeze':freeze,'design':design,'evaluate':evaluate}[a.phase]()
