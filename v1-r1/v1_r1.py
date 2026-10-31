"""v1-r1: locked daily-close strategy D058; no live orders."""
import json
from pathlib import Path
import sys

VERSION='v1-r1'
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'daily'))
import run_study as daily


def parameters():
    lock=daily.study.read_lock(daily.OUT/'LOCK.json')
    daily.study.verify_hashes(lock['source_hashes'])
    if daily.study.sha(daily.OUT/'CALENDAR.json')!=lock['calendar_hash']:
        raise ValueError('daily calendar changed')
    return lock['selected']


def simulate(mins,bid,ask,config=None):
    """Apply v1-r1's frozen parameters and daily calendar to supplied quotes."""
    selected=parameters()
    c=daily.context(mins,bid,ask)
    return daily.run(c,selected['rules'],selected['stop_theta'],config)


if __name__=='__main__':
    print('Version:',VERSION)
    print(json.dumps(parameters(),indent=2))
    print('2010-2022 report:',ROOT/'daily/RESULTS_2010_2022_LOT05.md')
