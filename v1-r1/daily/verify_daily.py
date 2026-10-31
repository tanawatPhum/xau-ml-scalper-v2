"""Post-lock verification; no parameter or calendar changes."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import run_study as d


def main():
    lock=d.study.read_lock(d.OUT/'LOCK.json');ev=json.loads((d.OUT/'EVALUATION.json').read_text())
    d.study.verify_hashes(lock['source_hashes']);d.study.verify_hashes(ev['data_hashes'])
    assert ev['lock_sha256']==d.study.sha(d.OUT/'LOCK.json')
    assert lock['calendar_hash']==d.study.sha(d.OUT/'CALENDAR.json')
    for rel in ['out/LOCK.json','out/balanced/LOCK.json']:
        old=d.study.read_lock(d.ROOT.parent/rel);d.study.verify_hashes(old['source_hashes'])
    selected=lock['selected'];c=d.load([2010],'design');checks=[]
    for name,rules,stop in [('baseline',d.BASE_RULES,3.),('old_rx',d.P20,3.),('rx',selected['rules'],selected['stop_theta'])]:
        full=d.run(c,rules,stop)
        after=c['mins']>=int(np.datetime64('2010-07-01','m').astype(int))
        active=np.flatnonzero(after&(full.equity.gross_oz.to_numpy()>0))
        assert len(active)>0
        for n in [int(np.searchsorted(c['mins'],np.datetime64('2010-07-01','m').astype(int))),int(active[0])+1]:
            short=d.context(c['mins'][:n],c['bid'][:n],c['ask'][:n])
            for col in ('s60','sl','eff','y'):np.testing.assert_array_equal(short[col],c[col][:n])
            signals=d.build_signals(c,rules);prefix=d.build_signals(short,rules)
            for rule in signals:np.testing.assert_array_equal(prefix[rule],signals[rule][signals[rule][:,0]<n])
            result=d.run(short,rules,stop)
            np.testing.assert_array_equal(result.equity.to_numpy(),full.equity.iloc[:n].to_numpy())
            pd.testing.assert_frame_equal(result.trades,full.trades[full.trades.t_exit<=short['mins'][-1]].reset_index(drop=True),check_exact=True)
            checks.append(dict(name=name,quotes=n,closed_trades=len(result.trades),open_positions=result.summary['open_positions']))
    reconciled=[]
    for period,scenarios in ev['results'].items():
        for scenario,variants in scenarios.items():
            for name,m in variants.items():
                folder=d.OUT/'evaluation'/period/scenario/name
                report=json.loads((folder/'REPORT.json').read_text());t=pd.read_csv(folder/'TRADES.private.csv')
                with np.load(folder/'EQUITY.private.npz',allow_pickle=False) as z:
                    mins=z['t_minute'];e=z['equity']
                assert np.isclose(e[-1]-100000,m['net'],rtol=0,atol=1e-7)
                assert np.isclose(sum(x['equity_change'] for x in report['yearly'].values()),m['net'],rtol=0,atol=1e-7)
                assert np.isclose(t.net_thb.sum(),report['summary']['closed_trade_net_thb'],rtol=0,atol=1e-7)
                sch=d.schedule(t.t_entry.to_numpy(dtype=np.int64))
                late=t.t_exit.to_numpy()>sch.deadline
                cross=t.t_exit.to_numpy()>=sch.market_close
                assert int(cross.sum())==m['market_close_crossings']
                assert int(late.sum())==m['late_cutoff_exits']
                assert not sch.blocked.any(), 'entry during blackout or close window'
                bad=t.loc[cross].copy()
                bad['entry_NY']=pd.to_datetime(bad.t_entry,unit='m',utc=True).dt.tz_convert('America/New_York').astype(str)
                bad['exit_NY']=pd.to_datetime(bad.t_exit,unit='m',utc=True).dt.tz_convert('America/New_York').astype(str)
                bad.to_json(folder/'CLOSE_EXCEPTIONS.private.json',orient='records',indent=2)
                if period=='full' and scenario=='fixed' and name in ('baseline','old_rx'):
                    before=int(np.datetime64('2017-01-01','m').astype(int))
                    bad[bad.t_entry<before].to_json(d.OUT/f'{name.upper()}_TRAIN_CLOSE_EXCEPTIONS.private.json',orient='records',indent=2)
                reconciled.append(dict(period=period,scenario=scenario,variant=name,market_close_crossings=int(cross.sum())))
    d.study.verify_hashes(lock['source_hashes']);d.study.verify_hashes(ev['data_hashes'])
    d.study.write_json(d.OUT/'VERIFICATION.json',dict(status='PASS',actual_prefix_checks=checks,accounting=reconciled,
        original_sources_and_locks_unchanged=True,calendar_sha256=lock['calendar_hash'],lock_sha256=ev['lock_sha256'],
        source_hashes=lock['source_hashes'],verification_script_sha256=d.study.sha(__file__)))
    print('FINAL VERIFICATION PASS',len(checks),'actual prefixes;',len(reconciled),'reports reconciled')


if __name__=='__main__':main()
