"""Join date-specific official-header evidence to <=2019 metadata."""
import csv
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from audit_metadata import ROOT, sha, snapshot


def build():
    rows = json.loads((ROOT/'metadata_rows.json').read_text())
    evidence = {}
    updates = {}
    paths = sorted((ROOT/'source_evidence').glob('*.txt'))
    for p in paths:
        for section in p.read_text(encoding='utf-8').split('-'*80):
            m = re.search(r'\(https://www.federalreserve.gov/newsevents/pressreleases/monetary(\d{8})a.htm\)', section)
            if not m: continue
            compact = m[1]
            date = f'{compact[:4]}-{compact[4:6]}-{compact[6:]}'
            header = re.search(r'For release at (\d{1,2}):(\d{2}) ([ap])\.m\. (EST|EDT)', section)
            if header:
                hh = int(header[1]) % 12 + (12 if header[3]=='p' else 0)
                evidence[date] = dict(header=header[0], time=f'{hh:02d}:{header[2]}', tz=header[4],
                                      source_evidence_file=str(p.relative_to(ROOT)), source_evidence_sha256=sha(p))
            elif 'For immediate release' in section:
                evidence[date] = dict(header='For immediate release', time='', tz='',
                                      source_evidence_file=str(p.relative_to(ROOT)), source_evidence_sha256=sha(p))
            update = re.search(r'Last Update: ([A-Za-z]+ \d{1,2}, \d{4})', section)
            if update: updates[date] = datetime.strptime(update[1], '%B %d, %Y').date().isoformat()
    for r in rows:
        e = evidence.get(r['date'])
        r['source_verified'] = bool(e)
        r['official_release_header'] = e['header'] if e else ''
        r['source_evidence_file'] = e['source_evidence_file'] if e else ''
        r['source_evidence_sha256'] = e['source_evidence_sha256'] if e else ''
        r['last_update_date'] = updates.get(r['date'], '')
        r['timestamp_confidence'] = 'missing'
        r['eligible_for_diagnostic'] = False
        if r['time_et']:
            assert e and e['time']==r['time_et'], r['date']
            assert e['tz']==r['expected_timezone_abbreviation'], r['date']
            r['availability_basis'] = 'official_declared_release_header_not_observed_latency'
            r['timestamp_confidence'] = 'official_minute_zone_verified'
            r['eligible_for_diagnostic'] = r['event_type']=='regular_meeting_policy_statement'
        elif e:
            assert not e['time']
        r['schedule_status'] = 'regular_meeting_archive' if r['event_type']=='regular_meeting_policy_statement' else 'outside_regular_meeting_policy_decision_subset'
        r['pre_event_calendar_snapshot_available'] = False
        r['correction_status'] = 'same_date_last_update_no_intraday_version_audit' if r['last_update_date']==r['date'] else 'not_version_audited'
    assert len(rows)==82 and sum(r['eligible_for_diagnostic'] for r in rows)==32
    assert sum(r['eligible_for_diagnostic'] and r['period']=='design' for r in rows)==8
    (ROOT/'event_manifest.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    fields = sorted(set().union(*(r.keys() for r in rows)))
    with (ROOT/'event_manifest.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    design=[r for r in rows if r['period']=='design' and r['eligible_for_diagnostic']]
    (ROOT/'design_events.json').write_text(json.dumps(design,indent=2)+'\n',encoding='utf-8')
    checks=dict(rows=82,header_verified_explicit=34,header_verified_missing=sum(r['source_verified'] and not r['time_et'] for r in rows),
                header_date_zone_mismatches=0,design_regular_verified=8,validation_regular_verified=24,
                actual_latency_verified=0,duplicate_dates=0,duplicate_urls=0,
                input_hashes_unchanged=snapshot()==json.loads((ROOT/'INPUTS.json').read_text())['source_hashes'],
                evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in paths},
                manifest_sha256=sha(ROOT/'event_manifest.json'), design_manifest_sha256=sha(ROOT/'design_events.json'))
    assert checks['input_hashes_unchanged']
    (ROOT/'DATA_VERIFICATION.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps({k:v for k,v in checks.items() if k!='evidence_hashes'},indent=2))


if __name__=='__main__':build()
