"""Frozen, bounded Rule C research. Does not update any strategy version."""
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'v1-r2'))
import v1_r2 as v
from replay import replay,smoke
import reclaim,structure
OUT=ROOT/'out'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf-8')
def sources():return {str(p):sha(p) for p in [ROOT/x for x in ('PLAN.md','replay.py','reclaim.py','structure.py','research_study.py')]}
def guards():
    l,ov=v.read_lock();b=v.r1_lock()['selected']
    assert sha(v.ROOT/'v1_r2.py')==l['code_sha256']
    assert sha(v.ROOT/'PLAN.md')==l['plan_sha256']
    assert sha(v.d.OUT/'LOCK.json')==l['r1_lock_sha256']
    return b,ov
def load(years):
    assert min(years)>=2010 and max(years)<=2019
    b,ov=guards();c=v.add_session(v.d.load(years,'design' if max(years)<=2016 else 'evaluate'))
    ab=v.run(c,b['rules'],ov,b['stop_theta'])
    return c,ab
def signals(c,s):return (reclaim if s['family']=='reclaim' else structure).signals(c,s)
def execute(c,s,signal,cost='fixed'):
    half=(c['ask']-c['bid'])/2 if cost=='historical' else np.full(len(c['mins']),.084)
    fee,slip=(.01,.02) if cost=='example' else (0.,0.)
    return replay(c['mins'],c['mid'],half,*signal,c['calendar'].blocked,c['calendar'].deadline,s['hold'],s['stop'],s['tp'],10.,33.77,fee,slip)
def dd(e,start=100000.):
    a=e+start;p=np.maximum.accumulate(np.r_[start,a])[1:]
    return float((p-a).max()),float(((p-a)/p).max()*100)
def daily(c,e):
    day=c['mins']//1440;ends=np.r_[np.flatnonzero(day[1:]!=day[:-1]),len(day)-1]
    return np.diff(np.r_[0.,e[ends]])
def metrics(c,ab,result):
    t,e,x,opened=result;n=len(t);ei=t[:,1].astype(int);xi=t[:,2].astype(int)
    wins=float(t[t[:,5]>0,5].sum());loss=float(-t[t[:,5]<0,5].sum())
    pf=wins/loss if loss>0 else None
    overlap=float((ab.equity.gross_oz.to_numpy()[ei]>0).mean()) if n else 1.
    dy=daily(c,e);std=dy.std(ddof=1);tt=float(dy.mean()/std*np.sqrt(len(dy))) if std else 0.
    recent=int(np.searchsorted(c['mins'],int(np.datetime64('2014-01-01','m').astype(int))))
    recentnet=float(e[-1]-(e[recent-1] if recent else 0.))
    end=ab.equity.equity.to_numpy()-100000.+e
    return dict(net=float(e[-1]),gross_wins=wins,gross_losses=loss,profit_factor=pf,trades=n,
        overlap=overlap,dd=dd(e)[0],dd_pct=dd(e)[1],lowest=float(min(100000.,(e+100000.).min())),
        daily_t=tt,net_2014_on=recentnet,worst=float(t[:,5].min()) if n else 0.,
        market_close_crossings=int((c['mins'][xi]>=c['calendar'].market_close[ei]).sum()),
        session_crossings=int((c['calendar'].session_day[xi]!=c['calendar'].session_day[ei]).sum()),
        open_positions=int(opened!=0),combined_net=float(end[-1]),combined_dd=dd(end)[0],combined_dd_pct=dd(end)[1],
        overlap_exposure_fraction=float(((x>0)&(ab.equity.gross_oz.to_numpy()>0)).sum()/max((x>0).sum(),1)))
def eligible(m,train=True):
    return (m['net']>0 and m['gross_wins']>m['gross_losses'] and m['overlap']<=.30 and m['trades']>=(100 if train else 20)
        and (not train or m['net_2014_on']>0) and m['example_net']>0 and not m['market_close_crossings']
        and not m['session_crossings'] and not m['open_positions'])
def annual(c,result):
    t,e,_,_=result;out={};prev=0.
    for y in range(int(np.datetime64(int(c['mins'][0]),'m').astype('datetime64[Y]').astype(int))+1970,2020):
        lo=int(np.datetime64(f'{y}-01-01','m').astype(int));hi=int(np.datetime64(f'{y+1}-01-01','m').astype(int))
        ix=np.flatnonzero((c['mins']>=lo)&(c['mins']<hi))
        if not len(ix):continue
        a=e[ix]; peak=np.maximum.accumulate(np.r_[prev,a])[1:]
        out[str(y)]=dict(net=float(a[-1]-prev),end_equity=float(100000.+a[-1]),dd=float((peak-a).max()))
        prev=float(a[-1])
    return out
def prefix_check(c,s,sg,r):
    n=min(100003,len(c['mins'])-1)
    cp=v.add_session(v.d.context(c['mins'][:n],c['bid'][:n],c['ask'][:n]))
    sp=signals(cp,s)
    for a,b in zip(sp,sg):np.testing.assert_allclose(a,b[:n],rtol=0,atol=0,equal_nan=True)
    rp=execute(cp,s,sp)
    np.testing.assert_array_equal(rp[1],r[1][:n])
    np.testing.assert_array_equal(rp[0],r[0][r[0][:,2]<n])

def design():
    OUT.mkdir(exist_ok=True)
    if (OUT/'LOCK.json').exists():raise FileExistsError('already locked')
    smoke();guards();before=sources()
    data_before=v.d.data_hashes(list(range(2010,2017)))
    write(OUT/'RUN_INPUTS.json',dict(sources=before,data_hashes=data_before))
    specs=reclaim.candidates()+structure.candidates();assert len(specs)==24
    write(OUT/'CANDIDATES.json',specs)
    c,ab=load(list(range(2010,2017)));rows=[];days=[]
    for s in specs:
        sg=signals(c,s);r=execute(c,s,sg);m=metrics(c,ab,r)
        ex=execute(c,s,sg,'example');m['example_net']=float(ex[1][-1]);m['eligible']=eligible(m)
        prefix_check(c,s,sg,r)
        rows.append(dict(spec=s,metrics=m,yearly=annual(c,r)));days.append(daily(c,r[1]))
        print(s['id'],json.dumps(m),flush=True)
    mat=np.asarray(days).T;N=len(mat);squares=(mat*mat).sum(axis=0)
    rng=np.random.default_rng(20261101)
    sums=rng.choice(np.array([-1.,1.]),size=(1000,N))@mat
    denom=np.sqrt(np.maximum((N*squares-sums*sums)/(N-1),1e-20))
    maxima=(sums/denom).max(axis=1)
    for row in rows:row['metrics']['max_t_null_p']=float((1+(maxima>=row['metrics']['daily_t']).sum())/1001)
    selected=[]
    for fam in sorted(set(s['family'] for s in specs)):
        ok=[r for r in rows if r['spec']['family']==fam and r['metrics']['eligible']]
        if ok:selected.append(sorted(ok,key=lambda r:(-r['metrics']['daily_t'],-r['metrics']['net']/max(r['metrics']['dd'],1),r['spec']['id']))[0]['spec'])
    assert sources()==before
    v.d.study.verify_hashes(data_before)
    write(OUT/'TRAINING.json',dict(rows=rows,ab_metrics=v.d.metrics(ab),bootstrap_max_t_95=float(np.quantile(maxima,.95)),prefix_checks=len(rows)))
    lock=dict(locked_utc=datetime.now(timezone.utc).isoformat(),sources=before,selected=selected,
        baseline_lock_sha256=sha(v.OUT/'LOCK.json'),training_data_hashes=data_before)
    write(OUT/'LOCK.json',lock);(OUT/'LOCK.sha256').write_text(sha(OUT/'LOCK.json'))
    print('LOCKED',json.dumps(selected),flush=True)

def evaluate():
    lock=json.loads((OUT/'LOCK.json').read_text());assert sha(OUT/'LOCK.json')==(OUT/'LOCK.sha256').read_text().strip()
    assert sources()==lock['sources'];guards();assert sha(v.OUT/'LOCK.json')==lock['baseline_lock_sha256']
    v.d.study.verify_hashes(lock['training_data_hashes'])
    if (OUT/'VALIDATION.json').exists():raise FileExistsError('already evaluated')
    if not lock['selected']:
        write(OUT/'VALIDATION.json',dict(status='NO_TRAINING_CANDIDATE',results=[],years_read=[]));return
    data_before=v.d.data_hashes([2017,2018,2019])
    c,ab=load([2017,2018,2019]);results=[]
    for s in lock['selected']:
        sg=signals(c,s);r=execute(c,s,sg);m=metrics(c,ab,r)
        example=execute(c,s,sg,'example');historical=execute(c,s,sg,'historical')
        m['example_net']=float(example[1][-1]);m['historical_net']=float(historical[1][-1]);m['eligible']=eligible(m,False)
        prefix_check(c,s,sg,r)
        np.savez_compressed(OUT/(s['id']+'_validation.private.npz'),trades=r[0],equity_change=r[1],mins=c['mins'])
        results.append(dict(spec=s,metrics=m,yearly=annual(c,r)))
        print('VALIDATION',s['id'],json.dumps(m),flush=True)
    assert sources()==lock['sources']
    v.d.study.verify_hashes(data_before)
    write(OUT/'VALIDATION.json',dict(status='EXPLORATORY_PASS' if any(x['metrics']['eligible'] for x in results) else 'NOT_CONFIRMED',results=results,ab_metrics=v.d.metrics(ab),years_read=[2017,2018,2019],data_hashes=data_before))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['design','evaluate']);a=ap.parse_args()
    {'design':design,'evaluate':evaluate}[a.phase]()
