"""Render and independently check stored diagnostic accounting; no quote reads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stamp(m):return datetime.fromtimestamp(m*60,timezone.utc).strftime('%Y-%m-%d %H:%M')


def main():
    r=json.loads((OUT/'TRAINING.json').read_text());p=r['primary']['metrics'];s=r['stop3_sensitivity']['metrics']
    pre=json.loads((OUT/'PRE_RUN_LOCK.json').read_text());lock=json.loads((OUT/'LOCK.json').read_text())
    assert sha(OUT/'PRE_RUN_LOCK.json')==(OUT/'PRE_RUN_LOCK.sha256').read_text().strip()
    assert sha(OUT/'LOCK.json')==(OUT/'LOCK.sha256').read_text().strip()
    assert pre['source_hashes']==lock['source_hashes']
    assert all(sha(path)==h for path,h in lock['source_hashes'].items())
    original=json.loads((ROOT/'INPUTS.json').read_text())['source_hashes']
    assert all(sha(path)==h for path,h in original.items())
    assert len(r['event_records'])==8 and len(r['trades'])==5
    assert sum(x['status']=='signal' for x in r['event_records'])==5
    assert len({t['event_utc_minute'] for t in r['trades']})==5
    for t in r['trades']:
        assert t['signal_utc_minute']==t['event_utc_minute']+4
        assert t['entry_utc_minute']==t['event_utc_minute']+5
        assert t['exit_utc_minute']==t['event_utc_minute']+20
        assert t['exit_reason']==1
        assert abs(t['net_thb']-(t['gross_mid_thb']-.168*10*33.77))<1e-7
    assert abs(sum(t['net_thb'] for t in r['trades'])-p['net'])<1e-7
    assert abs(p['example_net']-(p['net']-5*.06*10*33.77))<1e-7
    assert p==s and p['failed']==['minimum_trades']
    val=json.loads((OUT/'VALIDATION.json').read_text());assert val['years_read']==[] and not lock['selected']
    ab=r['ab_metrics']
    lines=['# FOMC declared-release-time diagnostic — 1 November 2026','',
           'The fixed diagnostic is positive on five trades but does not qualify:5 trades are below the prespecified20-trade design minimum. There were only8 eligible events before prices were read. No candidate was selected and no2017–2019 validation prices were read. Actual news delivery latency is unverified; this is a declared-release-time proxy, not validated real-time news-conditioned execution.','',
           'Design prices:2010–2016. Every eligible event is in2016; earlier regular statements lack verified release minutes and were excluded. Five of eight events reached the fixed2-sigma threshold; three did not. No missing-window event was silently treated as no-news.','',
           '| Design result | Primary timed exit | Fixed3-vol stop sensitivity |',
           '|---|---:|---:|',
           f'| Closed trades |{p["trades"]}|{s["trades"]}|',
           f'| Fixed-spread net,0.1lot (THB) |{p["net"]:,.2f}|{s["net"]:,.2f}|',
           f'| Example-cost net (THB) |{p["example_net"]:,.2f}|{s["example_net"]:,.2f}|',
           f'| Historical-spread net (THB) |{p["historical_net"]:,.2f}|{s["historical_net"]:,.2f}|',
           f'| Gross midpoint net (THB) |{p["gross_mid_net"]:,.2f}|{s["gross_mid_net"]:,.2f}|',
           f'| Profit factor on fixed-cost trades |{p["profit_factor"]:.3f}|{s["profit_factor"]:.3f}|',
           f'| C liquidation-equity DD (THB / %) |{p["dd"]:,.2f} / {p["dd_pct"]:.3f}%|{s["dd"]:,.2f} / {s["dd_pct"]:.3f}%|',
           f'| Natural A/B union overlap |{p["overlap_count"]}/{p["trades"]} (0%)|0%|','',
           'The stop sensitivity is identical because no3-scale stop fired. It cannot replace primary selection. All five primary trades entered exactlyE+5 and exitedE+20. Market-close/session crossings, late-cutoff exits, data-gap spans and terminal positions are all zero. The only failed qualification check is minimum_trades; the extra conservative0.5lot solvency check also passes and does not affect rejection.','',
           f'Locked A/B baseline design net is{ab["net"]:,.2f}THB. Adding C gives{p["combined_net"]:,.2f}THB with combined DD{p["combined_dd"]:,.2f}THB ({p["combined_dd_pct"]:.3f}%). This is a historical sum of separately sized rules, not evidence that the new rule is deployable.','',
           f'At fixed0.5lot scaling, C net is{p["lot05"]["net"]:,.2f}THB, C DD{p["lot05"]["dd"]:,.2f}THB ({p["lot05"]["dd_pct"]:.3f}%), and minimum equity{p["lot05"]["lowest"]:,.2f}THB. Scaled combined net is{p["lot05"]["combined_net"]:,.2f}THB with DD{p["lot05"]["combined_dd"]:,.2f}THB ({p["lot05"]["combined_dd_pct"]:.3f}%). Start equity is100,000THB; no compounding, margin, financing or stop-out model.','',
           '| Event date | Jump ratio J | Outcome |','|---|---:|---|']
    for e in r['event_records']:
        lines.append(f'|{stamp(e["event_utc_minute"])[:10]}|{e.get("jump_ratio",0):.3f}|{e["status"]}|')
    lines+=['','| Entry UTC | Exit UTC | Side | Fixed net THB |','|---|---|---|---:|']
    for t in r['trades']:
        lines.append(f'|{stamp(t["entry_utc_minute"])}|{stamp(t["exit_utc_minute"])}|{"Buy" if t["side"]>0 else "Sell"}|{t["net_thb"]:,.2f}|')
    lines+=['','Source evidence and exclusions are in DATA_AUDIT.md and event_manifest.json. PRE_RUN_LOCK freezes protocol, code, event inputs and allowed design-cache hashes before price loading. Synthetic checks cover direction, exact five-minute response, missing quote/entry cancellation, pre-event scale, DST, costs, next-minute fills, stop delay, overlap union and forbidden years. Real-data prefix invariance passed with an open trade at cutoff; locked baseline training metrics reproduced. Original metadata, source and allowed design-cache hashes remained unchanged. No GVZ, US500 or2020+ prices were read.','',
            'No trading specification or execution code was changed after market outcomes.','',
            'Decision: retain as a data-limited research observation only. More trustworthy contemporaneous release timing and substantially more eligible design events would be needed before a fresh, separately prespecified test; do not backfill this frozen trial in response to its positive P/L.']
    report='\n'.join(lines)+'\n'
    report=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',report)
    report=report.replace('qualify:5','qualify: 5').replace('prices:2010','prices: 2010').replace('net,0.1','net, 0.1').replace('exactlyE+5','exactly E+5').replace('exitedE+20','exited E+20').replace('US 500','US500')
    (ROOT/'RESULTS.md').write_text(report,encoding='utf-8')
    verification=dict(status='PASS',frozen_hashes_match=True,source_inputs_unchanged=True,
                      five_trade_timing_costs_checked=True,example_cost_arithmetic_checked=True,
                      only_failed_gate='minimum_trades',validation_price_years_read=[],
                      results_sha256=sha(ROOT/'RESULTS.md'))
    (ROOT/'REPORT_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps(verification,indent=2))


if __name__=='__main__':main()
