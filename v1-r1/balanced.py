"""Disclosed secondary selection from the existing training table, no new search.

The initial fallback remains immutable. Remove only the self-imposed50% trade
floor, keeping profit, DD, total-loss, solvency and recent-period gates.
This amendment is post-search; its validation is explicitly exploratory/reused.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json

import study
from strategy import prepare

OUT=study.OUT/'balanced'
SCENARIOS={
    'fixed':study.engine.Config(),
    'cost_example':study.engine.Config(commission=.01,slippage=.02),
    'historical':study.engine.Config(cost_mode='historical'),
}


def select(candidates,base):
    # A zero reference count disables ONLY the count floor in the original gate.
    return study.choose(candidates,{**base,'trades':0})


def verify_comparator(manifest,cache=study.CACHE):
    if set(manifest)!={f'M1_{y}.private.npz' for y in range(2010,2020)}:
        raise ValueError('comparison requires exactly2010-2019 data')
    study.verify_hashes({str(cache/p):h for p,h in manifest.items()})


def lock():
    original=study.read_lock(study.OUT/'LOCK.json')
    study.verify_hashes(original['source_hashes'])
    study.verify_hashes({str(study.CACHE/p):h for p,h in original['training_data_hashes'].items()})
    sources={str((study.ROOT/p).resolve()):study.sha(study.ROOT/p)
             for p in ('baseline_engine.py','strategy.py','study.py','balanced.py')}
    reports=[study.OUT/'PORTFOLIO_TRAIN.json',study.OUT/'BASE_TRAIN.json',study.OUT/'LOCK.json',study.OUT/'EVALUATION.json']
    # These hashes preserve comparators; their outcomes do not enter select().
    reports += [study.OUT/'evaluation'/period/scenario/'baseline/REPORT.json'
                for period in ('full','validation') for scenario in SCENARIOS]
    inputs={str(p.resolve()):study.sha(p) for p in reports}
    candidates=json.loads((study.OUT/'PORTFOLIO_TRAIN.json').read_text())
    base=json.loads((study.OUT/'BASE_TRAIN.json').read_text())
    selected,passed=select(candidates,base)
    comparison_data=json.loads((study.OUT/'EVALUATION.json').read_text())['input_hashes']
    verify_comparator(comparison_data)
    study.verify_hashes(sources);study.verify_hashes(inputs)
    OUT.mkdir(exist_ok=True)
    payload=dict(locked_utc=datetime.now(timezone.utc).isoformat(),training_end=2016,
        selected_id=selected['id'],rules=selected['rules'],selected_metrics=selected['metrics'],
        baseline_metrics=base,amended_training_pass=passed,original_training_pass=False,
        amendment='Remove only50%trade-count floor; no new candidates, no price retuning.',
        validation_status='Exploratory reused validation after disclosed post-search gate amendment; initial fallback outcomes already available.',
        source_hashes=sources,input_report_hashes=inputs,training_data_hashes=original['training_data_hashes'],
        comparison_data_hashes=comparison_data,
        config=asdict(SCENARIOS['fixed']))
    study.write_lock(OUT/'LOCK.json',payload)
    print('SECONDARY LOCK',json.dumps(payload),flush=True)


def evaluate():
    frozen=study.read_lock(OUT/'LOCK.json')
    study.verify_hashes(frozen['source_hashes']);study.verify_hashes(frozen['input_report_hashes'])
    study.verify_hashes({str(study.CACHE/p):h for p,h in frozen['training_data_hashes'].items()})
    verify_comparator(frozen['comparison_data_hashes'])
    if (OUT/'evaluation').exists():raise FileExistsError('secondary evaluation already exists')
    data={f'M1_{y}.private.npz':study.sha(study.CACHE/f'M1_{y}.private.npz') for y in range(2010,2020)}
    if data!=frozen['comparison_data_hashes']:raise ValueError('comparison data changed')
    results={}
    for period,years in [('full',list(range(2010,2020))),('validation',[2017,2018,2019])]:
        c=prepare(*study.load_prices(years,phase='evaluate'));results[period]={}
        for scenario,cfg in SCENARIOS.items():
            result=study.run(c,frozen['rules'],cfg)
            study.save_result(OUT/'evaluation'/period/scenario/'rx',result,years,cfg)
            base=json.loads((study.OUT/'evaluation'/period/scenario/'baseline/REPORT.json').read_text())
            results[period][scenario]=dict(baseline=base['metrics'],rx=study.metrics(result))
            print(period,scenario,json.dumps(study.metrics(result)),flush=True)
    study.verify_hashes(frozen['source_hashes']);study.verify_hashes(frozen['input_report_hashes'])
    study.verify_hashes({str(study.CACHE/p):h for p,h in data.items()})
    v=results['validation']['fixed'];b=v['baseline'];r=v['rx']
    confirmed=r['net']>b['net'] and r['dd']<b['dd'] and r['loss']<b['loss']
    output=dict(results=results,amended_training_pass=frozen['amended_training_pass'],
        validation_both_objectives=confirmed,
        status='IMPROVED_EXPLORATORY_REUSED_VALIDATION' if confirmed and frozen['amended_training_pass'] else 'NOT_CONFIRMED',
        lock_sha256=study.sha(OUT/'LOCK.json'),finished_utc=datetime.now(timezone.utc).isoformat(),input_hashes=data)
    study.write_json(OUT/'EVALUATION.json',output)
    print('SECONDARY VERDICT',output['status'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['lock','evaluate'])
    args=parser.parse_args();lock() if args.phase=='lock' else evaluate()
