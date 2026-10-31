"""Owner-authorized continuous2010-2022 replay of frozen D058 at0.5lot per rule.

Does not change locked design code, parameters, calendar rules or earlier outputs.
2023+ is rejected before file access. Explicit opt-in is required for2020-2022.
"""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd
import run_study as d


def validate_years(years,allow_2020_2022=False):
    years=tuple(years);last=2022 if allow_2020_2022 else 2019
    if (not years or any(type(y) is not int or not 2010<=y<=last for y in years)
        or tuple(sorted(set(years)))!=years):
        raise ValueError(f'only unique increasing2010-{last}years;2020-2022 requires opt-in;2023+ closed')
    return years


def load_prices(years,cache=d.study.CACHE,allow_2020_2022=False):
    years=validate_years(years,allow_2020_2022)
    parts=[]
    for year in years:
        with np.load(Path(cache)/f'M1_{year}.private.npz',allow_pickle=False) as z:
            raw=z['base'];bid=z['bid'];ask=z['ask']
        lo=int(np.datetime64(f'{year}-01-01','m').astype(int));hi=int(np.datetime64(f'{year+1}-01-01','m').astype(int))
        if raw.ndim!=0 or not np.isfinite(raw) or raw!=np.floor(raw):raise ValueError('invalid minute base')
        if int(raw)!=lo or bid.ndim!=1 or ask.shape!=bid.shape or len(bid)>hi-lo:raise ValueError('invalid year grid')
        ok=~np.isnan(bid)&~np.isnan(ask);ix=np.flatnonzero(ok)
        parts.append(d.engine.validate_prices(lo+ix,bid[ok],ask[ok]))
    return d.engine.validate_prices(*(np.concatenate([p[i] for p in parts]) for i in range(3)))


def main(allow_2020_2022=False):
    years=list(validate_years(list(range(2010,2023)),allow_2020_2022))
    lock=d.study.read_lock(d.OUT/'LOCK.json');d.study.verify_hashes(lock['source_hashes'])
    if d.study.sha(d.OUT/'CALENDAR.json')!=lock['calendar_hash']:raise ValueError('locked calendar changed')
    old= json.loads((d.OUT/'EVALUATION.json').read_text())
    d.study.verify_hashes(old['data_hashes'])
    selected=lock['selected'];cfg=d.engine.Config(oz=50.)
    output=d.OUT/'extension_2010_2022_lot05'
    if output.exists():raise FileExistsError('extension output already exists')
    source={**lock['source_hashes'],str(Path(__file__).resolve()):d.study.sha(__file__)}
    data=d.data_hashes(years)
    output.mkdir()
    request=dict(created_utc=datetime.now(timezone.utc).isoformat(),owner_authorized_2020_2022=True,
        years=years,selected_id=selected['id'],rules=selected['rules'],stop_theta=selected['stop_theta'],
        config=asdict(cfg),lock_sha256=d.study.sha(d.OUT/'LOCK.json'),source_hashes=source,data_hashes=data,
        mode='Frozen parameters; continuous equity; no annual capital reset; no retuning')
    d.study.write_json(output/'REQUEST.json',request)
    calendar=d.manifest(2010,2022)
    original_calendar=json.loads((d.OUT/'CALENDAR.json').read_text())
    assert [x for x in calendar['blackout_session_dates'] if x<'2020-01-01']==original_calendar['blackout_session_dates']
    d.study.write_json(output/'CALENDAR.json',calendar)
    print('AUTHORIZED EXTENSION:2010-2022;D058;0.5lot per rule;no retuning',flush=True)
    c=d.context(*load_prices(years,allow_2020_2022=True))
    r=d.run(c,selected['rules'],selected['stop_theta'],cfg)
    cutoff=int(np.datetime64('2020-01-01','m').astype(int));past=r.equity[r.equity.t_minute<cutoff]
    with np.load(d.OUT/'evaluation/full/fixed/rx/EQUITY.private.npz',allow_pickle=False) as z:
        np.testing.assert_array_equal(past.t_minute.to_numpy(),z['t_minute'])
        for col in ('balance','equity'):
            np.testing.assert_allclose(past[col],100000+5*(z[col]-100000),rtol=1e-12,atol=1e-6)
        for col in ('unrealized','gross_oz','net_oz'):
            np.testing.assert_allclose(past[col],5*z[col],rtol=1e-12,atol=1e-6)
    before_trades=pd.read_csv(d.OUT/'evaluation/full/fixed/rx/TRADES.private.csv')
    continued=r.trades[r.trades.t_exit<cutoff].reset_index(drop=True)
    for col in ('t_signal','t_entry','t_exit','side','rule','exit_reason'):
        np.testing.assert_array_equal(continued[col],before_trades[col])
    np.testing.assert_allclose(continued.net_thb,5*before_trades.net_thb,rtol=1e-12,atol=1e-6)
    sch=d.schedule(r.trades.t_entry.to_numpy(dtype=np.int64))
    crossed=r.trades.t_exit.to_numpy()>=sch.market_close
    assert int(crossed.sum())==r.diagnostics['market_close_crossings']
    assert not sch.blocked.any()
    assert np.isclose(r.trades.net_thb.sum(),r.summary['closed_trade_net_thb'])
    d.study.verify_hashes(source);d.study.verify_hashes(data)
    assert d.study.sha(d.OUT/'LOCK.json')==request['lock_sha256']
    d.save(output/'replay',r,years,cfg)
    report=json.loads((output/'replay/REPORT.json').read_text());previous=cfg.start
    for year in years:
        lo=int(np.datetime64(f'{year}-01-01','m').astype(int));hi=int(np.datetime64(f'{year+1}-01-01','m').astype(int))
        q=r.equity.loc[(r.equity.t_minute>=lo)&(r.equity.t_minute<hi),'equity'].to_numpy()
        peak=np.maximum.accumulate(np.r_[previous,q])[1:]
        report['yearly'][str(year)].update(start_equity=previous,dd_pct=float((100*(peak-q)/peak).max()) if len(q) else 0.)
        previous=float(q[-1]) if len(q) else previous
    assert np.isclose(sum(x['equity_change'] for x in report['yearly'].values()),r.summary['net_equity_thb'],rtol=1e-12,atol=1e-6)
    report.update(provenance=request,completed_utc=datetime.now(timezone.utc).isoformat(),
        checks=dict(past_2010_2019_equity_and_trades_match_scaled_original=True,yearly_reconciles=True,
                    source_data_and_lock_unchanged=True,market_close_crossings_independently_recounted=True),
        extension_net_2020_2022=float(sum(report['yearly'][str(y)]['equity_change'] for y in (2020,2021,2022))))
    d.study.write_json(output/'replay/REPORT.json',report)
    exceptions=r.trades.loc[crossed].copy()
    for col in ('t_entry','t_exit'):
        exceptions[col+'_NY']=pd.to_datetime(exceptions[col],unit='m',utc=True).dt.tz_convert('America/New_York').astype(str)
    exceptions.to_json(output/'CLOSE_EXCEPTIONS.private.json',orient='records',indent=2)
    lines=['# RX D058:2010–2022 ที่0.5lotต่อกฎ','',
        'ใช้กฎและค่าStopที่ล็อกไว้เดิม ไม่มีการจูนจากปี2020–2022 รันต่อเนื่องจากทุน100,000บาทในปี2010 ไม่รีเซ็ตหรือเติมทุนรายปี', '',
        '0.5lot=50ozต่อกฎ สูงสุดรวม1.0lotเมื่อA/Bถือพร้อมกัน; FX33.77; สเปรดคงที่0.168USD/oz; ยังไม่เพิ่มcommission/slippage ไม่ทบล็อตตามกำไร', '',
        '| ปี | กำไรสุทธิบาท | Max DDในปีบาท | Max DDในปี% | เงินปลายปีบาท | ไม้ |',
        '|---|---:|---:|---:|---:|---:|']
    for year,row in report['yearly'].items():
        lines.append(f'| {year} | {row["equity_change"]:+,.0f} | {row["dd"]:,.0f} | {row["dd_pct"]:.2f}% | {row["end_equity"]:,.0f} | {row["trades"]:,} |')
    s=report['summary'];dg=report['diagnostics']
    lines += ['',f'- กำไรรวม: {s["net_equity_thb"]:+,.2f}บาท; เงินปลายปี2022: {s["end_equity_thb"]:,.2f}บาท',
        f'- Max Equity DDตลอดช่วง: {s["max_equity_drawdown_thb"]:,.2f}บาท / {s["max_equity_drawdown_pct"]:.2f}%',
        f'- Equityต่ำสุด: {s["lowest_equity_thb"]:,.2f}บาท; ขาดทุนเมื่อปิดไม้หนักที่สุด: {report["metrics"]["worst"]:,.2f}บาท',
        f'- เฉพาะ2020–2022เพิ่มกำไร: {report["extension_net_2020_2022"]:+,.2f}บาท',
        f'- จำนวนไม้รวม: {s["trades"]:,}; ข้ามเวลาปิดตลาด: {dg["market_close_crossings"]}; ข้ามsession: {dg["session_crossings"]}; ปิดช้ากว่าเป้าหมาย16:55: {dg["late_cutoff_exits"]}; สถานะค้างปลายข้อมูล: {s["open_positions"]}', '',
        'DDรวมขาดทุนลอยตัวระหว่างถือสถานะ ไม่ใช่การขาดทุนต่อไม้ DDรายปีเริ่มจากEquityต้นปีและยอดสูงสุดภายในปีนั้น; DD%ไม่ได้คูณห้าจากรุ่น0.1lot แต่คำนวณใหม่จากEquity', '',
        'ปิดตามเวลาNY16:55 ก่อนเวลาตลาดที่กำหนด16:58 และงดเข้าในวันหยุดตามนโยบายอนุรักษนิยมเดิม ตารางนี้ไม่ใช่ประกาศวันหยุดExnessย้อนหลังที่ยืนยันครบ หากราคาหายใช้ราคาแรกที่ซื้อขายได้จริงและบันทึกข้อยกเว้น ไม่ปิดย้อนหลัง', '',
        'แบบจำลองไม่มีmargin call/stop-out,swap,fundingหรือผลล็อตต่อslippage ตัวเลขจึงไม่ได้ยืนยันว่าทุน100,000บาทรองรับล็อตนี้ในบัญชีจริง', '',
        'ตรวจแล้วว่าผล2010–2019ด้านสัญญาณ/รายการเทรดและEquityตรงกับผลเดิมเมื่อปรับเป็น0.5lot ยอดรายปีกระทบยอดรวมครบ และแฮชกฎ/โค้ด/ข้อมูลก่อนหลังไม่เปลี่ยน', '',
        f'ผลละเอียด: `{output.relative_to(d.ROOT).as_posix()}/replay/REPORT.json`', '']
    (d.ROOT/'RESULTS_2010_2022_LOT05.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(dict(summary=s,diagnostics=dg,yearly=report['yearly'],extension_net_2020_2022=report['extension_net_2020_2022']),indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-2020-2022',action='store_true')
    args=parser.parse_args();main(args.allow_2020_2022)
