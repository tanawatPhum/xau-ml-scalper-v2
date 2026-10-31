"""FOMC metadata audit only: no market data imports, reads, or strategy code."""
from __future__ import annotations
import csv
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html import unescape
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "data-ext"
MACRO = SOURCE / "macro"
NY = ZoneInfo("America/New_York")
CSV_NAMES = ("FOMC_statements_2010_2022.csv", "FOMC_monetary_pressreleases_2010_2022.csv")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def text(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def archive_context():
    found = {}
    for year in range(2010, 2020):
        p = MACRO / "raw" / f"fomchistorical{year}.htm"
        content = p.read_text(encoding="utf-8", errors="replace")
        sections = re.split(r"<h5[^>]*>", content)[1:]
        for section in sections:
            heading = text(section.split("</h5>")[0])
            for href, date in re.findall(r'href="([^"]*monetary/?(\d{8})a\.htm)"', section):
                key = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                found[key] = {"archive_heading": heading,
                              "archive_url": f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm",
                              "archive_local_sha256": sha(p)}
    return found


def snapshot():
    paths = [MACRO / n for n in CSV_NAMES]
    paths += [SOURCE / n for n in ("download_macro.py", "fix_fomc_times.py")]
    paths += [MACRO / "raw" / f"fomchistorical{y}.htm" for y in range(2010, 2020)]
    return {str(p.resolve()): sha(p) for p in paths}


def main():
    before = snapshot()
    out = ROOT / "INPUTS.json"
    if out.exists():
        assert json.loads(out.read_text())["source_hashes"] == before, "Source inputs changed"
    else:
        out.write_text(json.dumps({"created_utc": datetime.now(timezone.utc).isoformat(),
                                   "source_hashes": before,
                                   "scope": "FOMC metadata only; rows <=2019; no price data"}, indent=2)+"\n")
    context = archive_context()
    both = []
    full_counts = {}
    for name in CSV_NAMES:
        with (MACRO / name).open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ["date", "time_et", "title", "url"]
            all_rows = list(reader)  # Announcement metadata only, expressly permitted.
        full_counts[name] = len(all_rows)
        both.append([r for r in all_rows if "2010-01-01" <= r["date"] <= "2019-12-31"])
    rows = both[0]
    assert rows == both[1], "The <=2019 slices differ"
    assert len({r['date'] for r in rows}) == len(rows), "Duplicate dates"
    assert len({r['url'] for r in rows}) == len(rows), "Duplicate URLs"
    for r in rows:
        assert r['url'].startswith("https://www.federalreserve.gov/")
        r.update(context.get(r['date'], {}))
        if r['date'] == '2010-05-09':
            kind = 'conference_call_liquidity_swap_statement'
        elif r['date'] == '2019-10-11':
            kind = 'notation_vote_implementation_statement'
        else:
            assert 'Meeting' in r.get('archive_heading', ''), r
            kind = 'regular_meeting_policy_statement'
        r['event_type'] = kind
        r['period'] = 'design' if r['date'] < '2017-01-01' else 'validation'
        r['declared_release_at_utc'] = ''
        r['actual_available_at_utc'] = ''
        r['availability_basis'] = 'missing_release_minute'
        r['zone'] = 'America/New_York'
        r['utc_offset'] = ''
        if r['time_et']:
            dt = datetime.fromisoformat(r['date'] + 'T' + r['time_et']).replace(tzinfo=NY)
            r['declared_release_at_utc'] = dt.astimezone(timezone.utc).isoformat()
            r['utc_offset'] = dt.strftime('%z')
            r['expected_timezone_abbreviation'] = dt.tzname()
            r['availability_basis'] = 'local_csv_time_pending_official_header_verification'
        r['news_coverage'] = 'known_fomc_subset_only'
        r['actual_dissemination_latency_known'] = False
        r['canonical_url'] = 'https://www.federalreserve.gov/newsevents/pressreleases/monetary'+r['date'].replace('-','')+'a.htm'
    (ROOT / 'metadata_rows.json').write_text(json.dumps(rows, indent=2)+"\n", encoding='utf-8')
    summary = dict(rows=len(rows), full_metadata_counts=full_counts,
                   missing_times=sum(not r['time_et'] for r in rows),
                   explicit_times=sum(bool(r['time_et']) for r in rows),
                   by_year=dict(Counter(r['date'][:4] for r in rows)),
                   types=dict(Counter(r['event_type'] for r in rows)),
                   explicit_by_period=dict(Counter(r['period'] for r in rows if r['time_et'])),
                   regular_explicit_by_period=dict(Counter(r['period'] for r in rows if r['time_et'] and r['event_type']=='regular_meeting_policy_statement')),
                   duplicate_dates=0, duplicate_urls=0, identical_source_slices=True,
                   input_hashes_unchanged=snapshot()==before)
    (ROOT/'METADATA_COUNTS.json').write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
