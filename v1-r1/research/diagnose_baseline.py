"""Read only 2010-2016 prices; diagnose the frozen causal baseline, no search."""
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
os.environ['NUMBA_CACHE_DIR'] = str(HERE / 'numba_cache')
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent.parent / 'swing-causal-execution'))
import numpy as np
import pandas as pd
from engine import Config, simulate, volatility
from run import load_prices, yearly_report

YEARS = tuple(range(2010, 2017))
mins, bid, ask = load_prices(HERE.parent.parent / 'microstructure-edge-map' / 'cache', YEARS)
assert np.min(mins) >= np.datetime64('2010-01-01', 'm').astype(np.int64)
assert np.max(mins) < np.datetime64('2017-01-01', 'm').astype(np.int64)
mid = (bid + ask) / 2
s60, sl = volatility(mins, mid)
res = simulate(mins, bid, ask, config=Config())
t = res.trades.copy()
ix = np.searchsorted(mins, t.t_signal.to_numpy())
assert np.array_equal(mins[ix], t.t_signal)
t['theta_usd'] = t.theta_bps.to_numpy() * mid[ix] / 10000
t['vol_ratio'] = s60[ix] / sl[ix]
t['utc_hour'] = (t.t_signal // 60) % 24
t['session'] = pd.cut(t.utc_hour, [-1, 6, 11, 16, 23], labels=['00-06', '07-11', '12-16', '17-23'])
t['year'] = pd.to_datetime(t.t_signal, unit='m', utc=True).dt.year
t['hold_minutes'] = t.t_exit - t.t_entry
t['theta_bin'] = pd.cut(t.theta_usd, [0, 1, 1.5, 2, 2.5, 3, 4, 6, 10, np.inf], right=False).astype(str)
t['ratio_bin'] = pd.cut(t.vol_ratio, [0, .5, .75, 1, 1.25, 1.5, 2, np.inf], right=False).astype(str)
t['hold_bin'] = pd.cut(t.hold_minutes, [0, 2, 5, 10, 20, 40, 60, 120, 240, np.inf], right=False).astype(str)

def summary(g):
    p = g.net_thb.to_numpy()
    loss = p[p < 0]
    win = p[p > 0]
    return dict(n=len(g), net=round(float(p.sum()), 2), gross=round(float(g.gross_mid_thb.sum()), 2),
                win_rate=round(float((p>0).mean()), 4), mean=round(float(p.mean()), 2),
                profit_factor=round(float(win.sum() / -loss.sum()), 4) if len(loss) else None,
                loss_sum=round(float(loss.sum()), 2), mean_loss=round(float(loss.mean()), 2) if len(loss) else None,
                mean_win=round(float(win.mean()), 2) if len(win) else None,
                hold_median=float(g.hold_minutes.median()), theta_median=float(g.theta_usd.median()),
                worst=round(float(p.min()), 2))

def grouped(columns):
    return {str(key): summary(g) for key,g in t.groupby(columns, observed=True, dropna=False)}

report = {'scope': list(YEARS), 'summary': res.summary, 'yearly': yearly_report(res, YEARS, 100000),
          'by_rule': grouped('rule'), 'by_rule_year': grouped(['rule','year']),
          'by_rule_theta': grouped(['rule','theta_bin']), 'by_rule_hour': grouped(['rule','utc_hour']),
          'by_rule_session': grouped(['rule','session']), 'by_rule_side': grouped(['rule','side']),
          'by_rule_ratio': grouped(['rule','ratio_bin']), 'by_rule_hold': grouped(['rule','hold_bin']),
          'by_rule_reason': grouped(['rule','exit_reason'])}
for rule,g in t.groupby('rule'):
    loss = g.loc[g.net_thb<0].sort_values('net_thb')
    report.setdefault('loss_concentration',{})[rule] = {
        str(frac): {'loss_count':max(1,int(len(loss)*frac)),
                    'loss_fraction':float(loss.head(max(1,int(len(loss)*frac))).net_thb.sum()/loss.net_thb.sum())}
        for frac in (.001,.01,.05,.1)
    }
path = res.equity.equity.to_numpy()
peaks = np.maximum.accumulate(np.r_[100000.,path])[1:]
trough = int(np.argmax(peaks-path))
peak = int(np.argmax(path[:trough+1]))
dd_t = t.loc[(t.t_exit>=mins[peak]) & (t.t_exit<=mins[trough])]
report['worst_drawdown'] = {'peak_utc':str(np.datetime64(int(mins[peak]),'m')),
 'trough_utc':str(np.datetime64(int(mins[trough]),'m')), 'peak':float(path[peak]),
 'trough':float(path[trough]), 'closed_by_rule':{r:summary(g) for r,g in dd_t.groupby('rule')}}
t.to_csv(HERE / 'baseline_2010_2016.private.csv', index=False)
(HERE / 'BASELINE_DIAGNOSTIC.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
print(json.dumps({k:report[k] for k in ('summary','by_rule','by_rule_reason','worst_drawdown','loss_concentration')},indent=2))
