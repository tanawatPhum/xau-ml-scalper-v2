"""Timestamp-only NY session calendar; never infer a closure from future quotes.

Holiday exclusions are a conservative strategy policy, not an Exness historical
holiday archive. Dates are computable without seeing any market observations.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache

from dateutil.easter import easter
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

NY='America/New_York'
FLAT=16*60+55
CLOSE=16*60+58
REOPEN=18*60+1


@dataclass(frozen=True)
class Schedule:
    mins:np.ndarray
    available:np.ndarray
    blocked:np.ndarray
    deadline:np.ndarray
    market_close:np.ndarray
    session_day:np.ndarray
    holiday:np.ndarray


@lru_cache(maxsize=64)
def blackout_dates(first,last):
    dates=set(USFederalHolidayCalendar().holidays(f'{first}-01-01',f'{last}-12-31').date)
    for y in range(first,last+1):
        dates.add(easter(y)-timedelta(days=2))
        thanksgiving=date(y,11,1)
        thanksgiving+=timedelta(days=(3-thanksgiving.weekday())%7+21)
        dates.add(thanksgiving+timedelta(days=1))
        dates.add(date(y,7,3))
        observed=date(y,7,4)
        if observed.weekday()==5:observed-=timedelta(days=1)
        elif observed.weekday()==6:observed+=timedelta(days=1)
        before=observed-timedelta(days=1)
        while before.weekday()>=5:before-=timedelta(days=1)
        dates.add(before)
        for d in range(24,32):dates.add(date(y,12,d))
        dates.update((date(y,1,1),date(y,1,2)))
    return tuple(sorted(dates))


def schedule(mins):
    m=np.asarray(mins)
    if m.ndim!=1 or not np.isfinite(m).all() or np.any(m!=np.floor(m)):
        raise ValueError('calendar needs finite integer minute timestamps')
    m=m.astype(np.int64)
    if not len(m):
        b=np.empty(0,bool)
        return Schedule(m,b,b.copy(),m.copy(),m.copy(),m.copy(),b.copy())
    ny=pd.to_datetime(m,unit='m',utc=True).tz_convert(NY)
    mod=(ny.hour*60+ny.minute).to_numpy();dow=ny.dayofweek.to_numpy()
    days=ny.tz_localize(None).normalize()+pd.to_timedelta((mod>=REOPEN).astype(int),unit='D')
    first=int(days.year.min());last=int(days.year.max())
    holiday=np.asarray(days.isin(pd.to_datetime(blackout_dates(first,last))))
    regular=(days.dayofweek.to_numpy()<5)&((mod<CLOSE)|(mod>=REOPEN))
    regular&=~((dow==6)&(mod<18*60+5))
    # Blackouts forbid new risk but never suppress an observed emergency exit.
    available=regular
    blocked=~available|holiday|((mod>=FLAT)&(mod<REOPEN))
    deadline=(days+pd.Timedelta(minutes=FLAT)).tz_localize(NY).tz_convert('UTC').as_unit('ns').asi8//60_000_000_000
    market_close=(days+pd.Timedelta(minutes=CLOSE)).tz_localize(NY).tz_convert('UTC').as_unit('ns').asi8//60_000_000_000
    session_day=days.to_numpy(dtype='datetime64[D]').astype(np.int64)
    return Schedule(m,available,blocked,deadline,market_close,session_day,holiday)


def manifest(first=2010,last=2019):
    return dict(timezone=NY,flat_ny='16:55',close_ny='16:58',reopen_ny='18:01',sunday_reopen_ny='18:05',
        policy='Conservative deterministic session blackouts; not a verified historical Exness holiday calendar',
        blackout_session_dates=[x.isoformat() for x in blackout_dates(first,last)],
        sources=['https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours',
                 'https://www.cmegroup.com/education/files/metals-prod_guide_2019.pdf'])
