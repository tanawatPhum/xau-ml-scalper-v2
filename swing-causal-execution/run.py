"""Local causal replay: 2010-2019 by default; explicit opt-in through 2022, never 2023+."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine import Config, RULES, simulate, validate_prices

ROOT = Path(__file__).resolve().parent
DEFAULT_CACHE = ROOT.parent/'microstructure-edge-map'/'cache'


def validate_years(years, *, allow_2020_2022=False):
    years = tuple(years)
    last = 2022 if allow_2020_2022 else 2019
    if (not years or any(not isinstance(y, (int, np.integer)) or not 2010 <= y <= last for y in years)
            or tuple(sorted(set(years))) != years):
        raise ValueError(f'only unique increasing years 2010-{last} are permitted; '
                         '2020-2022 requires explicit opt-in; 2023+ is always closed')
    return years


def load_prices(cache, years, *, allow_2020_2022=False):
    years = validate_years(years, allow_2020_2022=allow_2020_2022)  # Before file access.
    pieces = []
    for yr in years:
        with np.load(Path(cache)/f'M1_{yr}.private.npz', allow_pickle=False) as z:
            rawbase = np.asarray(z['base'])
            base = int(rawbase)
            bid, ask = np.asarray(z['bid'], float), np.asarray(z['ask'], float)
        start = int(np.datetime64(f'{yr}-01-01T00:00', 'm').astype(np.int64))
        end = int(np.datetime64(f'{yr+1}-01-01T00:00', 'm').astype(np.int64))
        if (rawbase.ndim != 0 or base != start or float(rawbase) != base or bid.ndim != 1
                or ask.shape != bid.shape or len(bid) > end-start):
            raise ValueError(f'cache {yr} has invalid base or minute-grid shape')
        present = ~np.isnan(bid) & ~np.isnan(ask)
        pos = np.flatnonzero(present)
        pieces.append(validate_prices(base+pos, bid[present], ask[present]))
    return validate_prices(*(np.concatenate([p[i] for p in pieces]) for i in range(3)))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def yearly_report(result, years, start):
    rows = {}
    previous = previous_balance = start
    for yr in years:
        lo = int(np.datetime64(f'{yr}-01-01', 'm').astype(np.int64))
        hi = int(np.datetime64(f'{yr+1}-01-01', 'm').astype(np.int64))
        path = result.equity.loc[(result.equity.t_minute >= lo) & (result.equity.t_minute < hi)]
        trades = result.trades.loc[(result.trades.t_exit >= lo) & (result.trades.t_exit < hi)]
        e = path.equity.to_numpy()
        peak = np.maximum.accumulate(np.r_[previous, e])[1:]
        end = float(e[-1]) if len(e) else previous
        end_balance = float(path.balance.iloc[-1]) if len(path) else previous_balance
        rows[str(yr)] = dict(closed_trades=len(trades), realized_net_thb=end_balance-previous_balance,
                            closed_trade_net_thb=float(trades.net_thb.sum()),
                            start_equity_thb=previous, end_equity_thb=end, equity_change_thb=end-previous,
                            max_equity_drawdown_thb=float(np.max(peak-e)) if len(e) else 0.)
        previous = end
        previous_balance = end_balance
    return rows


def run_audit(years, config, output, cache=DEFAULT_CACHE, *, allow_2020_2022=False):
    years = validate_years(years, allow_2020_2022=allow_2020_2022)
    output, cache = Path(output), Path(cache)
    if output.exists():
        raise FileExistsError(f'output already exists; choose a fresh directory: {output}')
    sources = [ROOT/'engine.py', ROOT/'run.py']+[cache/f'M1_{y}.private.npz' for y in years]
    before = {str(p.resolve()): sha256(p) for p in sources}
    mins, bid, ask = load_prices(cache, years, allow_2020_2022=allow_2020_2022)
    result = simulate(mins, bid, ask, config=config)
    if before != {str(p.resolve()): sha256(p) for p in sources}:
        raise RuntimeError('source changed during replay; result not saved')
    import numba
    report = dict(kind='engineering_correction_not_holdout_exam', years=list(years),
                  allow_2020_2022=bool(allow_2020_2022),
                  created_utc=datetime.now(timezone.utc).isoformat(), config=asdict(config), rules=RULES,
                  summary=result.summary, diagnostics=result.diagnostics,
                  yearly=yearly_report(result, years, config.start),
                  by_rule={r:dict(trades=len(g),net_thb=float(g.net_thb.sum()),
                                 win_rate=float((g.net_thb > 0).mean())) for r,g in result.trades.groupby('rule')},
                  exit_reasons=result.trades.exit_reason.value_counts().to_dict(),
                  source_hashes=before, versions=dict(numpy=np.__version__,pandas=pd.__version__,numba=numba.__version__),
                  assumptions=[
                      'Signal filter fixed at confirmation close; fill at exact next minute close.',
                      'Close-based stop submits an exit for the next observed quote; not an intrabar stop.',
                      'Data-gap liquidation occurs after the gap; no retrospective last-bar fill.',
                      'exit_delay_minutes is stop/swing-reason request latency only; forced gap/scheduled exits report zero.',
                      'No assumed broker session calendar; UTC cutoff disabled unless supplied.',
                      'Commission/slippage are user assumptions; zero does not prove zero execution cost.',
                      'Liquidation equity includes estimated exit costs; EOF positions remain open.',
                      'Realized net is cash balance change including paid entry commissions on open positions.',
                      'Gross/spread/slippage/commission cost totals refer to closed trades; commission_paid includes open entries.',
                      'No margin liquidation, funding/swap, variable FX or intraminute risk simulation.',
                      'Daily cutoff in UTC does not adjust for DST, holidays or a broker-specific calendar.',
                      'Signals/parameters unchanged except causal dollar filter and adjacent-minute volatility.',
                      'Volatility/swing state is continuous across year boundaries; no artificial annual reset.',
                  ])
    output.mkdir(parents=True, exist_ok=False)
    result.trades.to_csv(output/'TRADES.private.csv', index=False)
    result.open_positions.to_json(output/'OPEN_POSITIONS.private.json',orient='records',indent=2)
    np.savez_compressed(output/'EQUITY.private.npz', **{c:result.equity[c].to_numpy() for c in result.equity})
    (output/'REPORT.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--years', nargs='+', type=int, default=list(range(2010,2020)))
    parser.add_argument('--allow-2020-2022', action='store_true',
                        help='explicitly permit the owner-authorized correction audit through 2022; never 2023+')
    parser.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--output', type=Path, required=True, help='must be a NEW directory')
    parser.add_argument('--cost-mode', choices=['fixed','historical'], default='fixed')
    parser.add_argument('--spread', type=float, default=.168, help='fixed round-trip USD/oz')
    parser.add_argument('--commission', type=float, default=0., help='USD/oz per side')
    parser.add_argument('--slippage', type=float, default=0., help='adverse USD/oz per fill')
    parser.add_argument('--flat-utc', help='optional HH:MM daily cutoff; no entries until next UTC day')
    args=parser.parse_args(argv)
    cutoff=None
    if args.flat_utc:
        try:
            hour,minute=map(int,args.flat_utc.split(':'))
            if not 0 <= hour < 24 or not 0 <= minute < 60:
                raise ValueError
            cutoff=60*hour+minute
        except ValueError:
            parser.error('--flat-utc must be HH:MM UTC')
    config=Config(cost_mode=args.cost_mode,spread=args.spread,commission=args.commission,
                  slippage=args.slippage,flat_minute_utc=cutoff)
    report=run_audit(args.years,config,args.output,args.cache,allow_2020_2022=args.allow_2020_2022)
    print(json.dumps(report['summary'],indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
