import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def minute(*times):
    return pd.to_datetime(list(times),utc=True).as_unit('ns').asi8//60_000_000_000


@pytest.mark.parametrize('date,utc',['2010-02-02,21'.split(','),'2010-06-02,20'.split(',')])
def test_close_cutoff_tracks_ny_dst(date,utc):
    from calendar_rules import schedule
    m=minute(f'{date} {utc}:54',f'{date} {utc}:55',f'{date} {utc}:57',f'{date} {utc}:58')
    s=schedule(m)
    assert s.available.tolist()==[True,True,True,False]
    assert s.blocked.tolist()==[False,True,True,True]
    assert np.all(s.deadline==m[1])


def test_weekend_and_sunday_reopen():
    from calendar_rules import schedule
    m=minute('2010-06-04 20:57','2010-06-04 22:01','2010-06-05 15:00',
             '2010-06-06 22:04','2010-06-06 22:05')
    assert schedule(m).available.tolist()==[True,False,False,False,True]


def test_holiday_blackout_begins_previous_evening():
    from calendar_rules import schedule
    m=minute('2010-01-14 23:01','2010-01-17 23:05','2010-01-18 15:00','2010-01-18 23:01')
    s=schedule(m)
    assert s.holiday.tolist()==[False,True,True,False]
    # A strategy holiday blackout forbids entry, not emergency exits on quotes.
    assert s.available.tolist()==[True,True,True,True]
    assert s.blocked.tolist()==[False,True,True,False]


def test_good_friday_and_year_end_blackouts():
    from calendar_rules import schedule
    m=minute('2010-04-02 15:00','2010-12-24 15:00','2011-01-02 15:00')
    assert schedule(m).holiday.all()


def test_calendar_never_changes_past_for_future_gap_or_eof():
    from calendar_rules import schedule
    base=int(minute('2010-02-02 15:00')[0])
    a=base+np.arange(15);b=base+np.r_[np.arange(10),np.arange(60,66)]
    for field in ('available','blocked','deadline','market_close','session_day','holiday'):
        x=getattr(schedule(a),field)
        np.testing.assert_array_equal(x[:10],getattr(schedule(a[:10]),field))
        np.testing.assert_array_equal(x[:10],getattr(schedule(b),field)[:10])
    assert not schedule(a).blocked.any()


def test_bad_time_values_are_rejected():
    from calendar_rules import schedule
    with pytest.raises(ValueError):schedule(np.array([1.5]))
