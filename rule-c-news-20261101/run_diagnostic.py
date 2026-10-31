"""One frozen FOMC declared-time proxy diagnostic; design prices only."""
from datetime import datetime, timezone
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
CACHE=ROOT/'numba_cache'
os.environ['NUMBA_CACHE_DIR']=str(CACHE)
import numba
numba.config.CACHE_DIR=str(CACHE)
LIB_PATH=ROOT.parent/'rule-c-literature-20261101'/'trial.py'
sys.path.insert(0,str(LIB_PATH.parent))
module_spec=importlib.util.spec_from_file_location('prior_trial_helpers',LIB_PATH)
lib=importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(lib)
os.environ['NUMBA_CACHE_DIR']=str(CACHE)
numba.config.CACHE_DIR=str(CACHE)
sys.path.insert(0,str(ROOT))
from news_signals import signals
from audit_metadata import snapshot

SPEC=dict(id='C_FOMC_declared_time_jump_continuation',hold=15,stop=1e12,tp=1e12,
          response_minutes=5,jump_threshold=2.,fill_delay_minutes=1,primary_min_train=20,
          primary_min_validation=8,actual_latency_verified=False)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def source_hashes():
    paths=[ROOT/p for p in ('PLAN.md','DATA_AUDIT.md','news_signals.py','run_diagnostic.py','test_synthetic.py',
                            'test_execution.py','audit_metadata.py','build_manifest.py','INPUTS.json',
                            'DATA_VERIFICATION.json','event_manifest.json','design_events.json')]
    paths+=list((ROOT/'source_evidence').glob('*.txt'))
    paths+=[LIB_PATH,LIB_PATH.parent/'signals.py',ROOT.parent/'rule-c-research-20261101'/'replay.py',
            lib.v.ROOT/'v1_r2.py',lib.v.ROOT/'PLAN.md',lib.v.OUT/'LOCK.json',lib.v.OUT/'LOCK.sha256']
    paths += [Path(p) for p in lib.v.d.sources()]
    return {str(p.resolve()):sha(p) for p in paths}


def permitted(years):
    if years!=list(range(2010,2017)):raise ValueError('this diagnostic permits only exact design2010–2016')


def eligibility(m):
    checks=dict(minimum_trades=m['trades']>=20,net_positive=m['net']>0,
                profit_factor_above_one=m['gross_wins']>m['gross_losses'],
                example_cost_positive=m['example_net']>0,recent_positive=m['net_2014_2016']>0,
                natural_overlap=m['overlap'] is not None and m['overlap']<=.30,
                no_close_crossings=m['market_close_crossings']==0,
                no_session_crossings=m['session_crossings']==0,no_terminal_position=m['open_positions']==0,
                solvent=m['lowest']>0 and m['combined_lowest']>0,
                solvent_lot05=m['lot05']['lowest']>0 and m['lot05']['combined_lowest']>0)
    return dict(eligible=all(checks.values()),checks=checks,failed=[k for k,v in checks.items() if not v])


def summarize(c,ab,sg,stop):
    result=lib.execute(c,SPEC,sg,stop=stop)
    m=lib.metrics(c,ab,result)
    m['example_net']=float(lib.execute(c,SPEC,sg,'example',stop=stop)[1][-1])
    m['historical_net']=float(lib.execute(c,SPEC,sg,'historical',stop=stop)[1][-1])
    m.update(eligibility(m))
    m['gross_mid_net']=float(result[0][:,4].sum())
    return result,dict(metrics=m,yearly=lib.annual(c,result))


def main():
    years=list(range(2010,2017));permitted(years)
    OUT.mkdir(exist_ok=True)
    if (OUT/'PRE_RUN_LOCK.json').exists():raise FileExistsError('already frozen/run; no rerun or retuning')
    lib.guards()
    raw=json.loads((ROOT/'design_events.json').read_text())
    assert len(raw)==8 and all(r['eligible_for_diagnostic'] and r['source_verified'] and r['date'].startswith('2016-') for r in raw)
    events=[int(datetime.fromisoformat(r['declared_release_at_utc']).timestamp()//60) for r in raw]
    assert len(events)==len(set(events))
    before=source_hashes();data=lib.v.d.data_hashes(years)
    original=snapshot();assert original==json.loads((ROOT/'INPUTS.json').read_text())['source_hashes']
    lock=dict(frozen_utc=datetime.now(timezone.utc).isoformat(),spec=SPEC,source_hashes=before,
              design_data_hashes=data,known_event_count=8,source_actual_latency_verified=False,
              selection_impossible_before_prices='8 available events < minimum20',price_years_allowed=years)
    write(OUT/'PRE_RUN_LOCK.json',lock);(OUT/'PRE_RUN_LOCK.sha256').write_text(sha(OUT/'PRE_RUN_LOCK.json'))
    print('Protocol, source and design-data hashes frozen before price load',flush=True)
    c,ab=lib.load(years,'design')
    side,scale,event_records=signals(c,events);sg=(side,scale)
    assert int(np.count_nonzero(side))<=8
    primary,primary_row=summarize(c,ab,sg,1e12)
    stop_result,stop_row=summarize(c,ab,sg,3.)
    assert not primary_row['metrics']['eligible']
    # Confirm real signal prefix invariance with volatility recomputed from that prefix.
    active=np.flatnonzero(primary[2]>0)
    prefix=dict(status='NO_OPEN_TRADE_AVAILABLE')
    if len(active):
        n=int(active[min(3,len(active)-1)])+1
        cp=lib.v.add_session(lib.v.d.context(c['mins'][:n],c['bid'][:n],c['ask'][:n]))
        ps,pc,_=signals(cp,events)
        np.testing.assert_array_equal(ps,side[:n]);np.testing.assert_array_equal(pc,scale[:n])
        pr=lib.execute(cp,SPEC,(ps,pc))
        np.testing.assert_allclose(pr[1],primary[1][:n],rtol=0,atol=0)
        np.testing.assert_array_equal(pr[0],primary[0][primary[0][:,2]<n])
        prefix=dict(status='PASS',quotes=n,open_at_cut=bool(pr[3]))
    details=[]
    for t in primary[0]:
        si,ei,xi=map(int,t[:3]);event=int(c['mins'][si]-4)
        assert event in events and int(c['mins'][ei])==event+5
        details.append(dict(event_utc_minute=event,signal_utc_minute=int(c['mins'][si]),
                            entry_utc_minute=int(c['mins'][ei]),exit_utc_minute=int(c['mins'][xi]),
                            side=int(t[3]),gross_mid_thb=float(t[4]),net_thb=float(t[5]),
                            exit_reason=int(t[6]),scale_usd=float(t[7])))
    assert source_hashes()==before and snapshot()==original
    lib.v.d.study.verify_hashes(data)
    row=dict(spec=SPEC,primary=primary_row,stop3_sensitivity=stop_row,event_records=event_records,
             trades=details,prefix_check=prefix,ab_metrics=lib.v.d.metrics(ab),years_read=years,
             source_actual_latency_verified=False,selection=[])
    write(OUT/'TRAINING.json',row)
    write(OUT/'LOCK.json',dict(locked_utc=datetime.now(timezone.utc).isoformat(),selected=[],
                              pre_run_lock_sha256=sha(OUT/'PRE_RUN_LOCK.json'),source_hashes=before,
                              design_data_hashes=data,price_years_read=years))
    (OUT/'LOCK.sha256').write_text(sha(OUT/'LOCK.json'))
    write(OUT/'VALIDATION.json',dict(status='NOT_RUN_INSUFFICIENT_DESIGN_EVENTS',years_read=[],rows=[]))
    write(OUT/'VERIFICATION.json',dict(source_hashes_unchanged=True,input_metadata_unchanged=True,
                                      design_data_hashes_unchanged=True,baseline_training_reproduced=True,
                                      prefix=prefix,primary_signals=int(np.count_nonzero(side)),
                                      actual_latency_verified=False,validation_prices_read=False,
                                      post2019_prices_read=False,gvz_or_us500_read=False))
    print(json.dumps(dict(primary=primary_row['metrics'],stop3=stop_row['metrics'],prefix=prefix),indent=2),flush=True)


if __name__=='__main__':main()
