"""Build the scheduled-release event table for v1-r3 (data cleaning only; no trade outcomes are used).

- NFP / CPI: BLS archive dates (data-ext/macro/BLS_*.csv if the Wayback download worked, else the BLS archive-page
  lists captured via WebFetch on 2026-11-01, embedded in data-ext/download_macro.py). 08:30 ET.
- GDP: data-ext/macro/BEA_GDP_2010_2022.csv, 08:30 ET.
- FOMC: data-ext/macro/FOMC_statements_2010_2022.csv. Missing 2010-15 times are inferred from gold 1-minute prices
  (design years only): among {12:30, 14:00, 14:15} ET pick the candidate with the largest max |1-min return| in the
  3 minutes after it, relative to that day's 12:00-15:00 ET median |return|.
Output: out/EVENTS_2010_2022.csv (type, date, time_et, utc_minute, source, note).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
EXT = ROOT.parent / "data-ext"
sys.path.insert(0, str(EXT))
sys.path.insert(0, str(ROOT.parent / "v1-r2"))
import download_macro as dm  # noqa: E402  (constants only)
import v1_r2 as r2  # noqa: E402

d = r2.d
OUT = ROOT / "out"
NY = "America/New_York"


GDP_ALFRED = """2010-01-29 2010-02-26 2010-03-26 2010-04-30 2010-06-25 2010-07-30 2010-08-27 2010-09-30 2010-10-29 2010-11-23 2010-12-22
2011-01-28 2011-02-25 2011-03-25 2011-04-28 2011-05-26 2011-06-24 2011-07-29 2011-08-26 2011-09-29 2011-10-27 2011-11-22 2011-12-22
2012-01-27 2012-02-29 2012-03-29 2012-04-27 2012-05-31 2012-06-28 2012-07-27 2012-08-29 2012-09-27 2012-10-26 2012-11-29 2012-12-20
2013-01-30 2013-02-28 2013-03-28 2013-04-26 2013-05-30 2013-06-26 2013-07-31 2013-08-29 2013-09-26 2013-11-07 2013-12-05 2013-12-20
2014-01-30 2014-02-28 2014-03-27 2014-04-30 2014-05-29 2014-06-25 2014-07-30 2014-08-28 2014-09-26 2014-10-30 2014-11-25 2014-12-23
2015-01-30 2015-02-27 2015-03-27 2015-04-29 2015-05-29 2015-06-24 2015-07-30 2015-08-27 2015-09-25 2015-10-29 2015-11-24 2015-12-22
2016-01-29 2016-02-26 2016-03-25 2016-04-28 2016-05-27 2016-06-28 2016-07-29 2016-08-26 2016-09-29 2016-10-28 2016-11-29 2016-12-22
2017-01-27 2017-02-28 2017-03-30 2017-04-28 2017-05-26 2017-06-29 2017-07-28 2017-08-30 2017-09-28 2017-10-27 2017-11-29 2017-12-21
2018-01-26 2018-02-28 2018-03-28 2018-04-27 2018-05-30 2018-06-28 2018-07-27 2018-08-29 2018-09-27 2018-10-26 2018-11-28 2018-12-21
2019-02-28 2019-03-28 2019-04-26 2019-05-30 2019-06-27 2019-07-26 2019-08-29 2019-09-26 2019-10-30 2019-11-27 2019-12-20
2020-01-30 2020-02-27 2020-03-26 2020-04-29 2020-05-28 2020-06-25 2020-07-30 2020-08-27 2020-09-30 2020-10-29 2020-11-25 2020-12-22
2021-01-28 2021-02-25 2021-03-25 2021-04-29 2021-05-27 2021-06-24 2021-07-29 2021-08-26 2021-09-30 2021-10-28 2021-11-24 2021-12-22
2022-01-27 2022-02-24 2022-03-30 2022-04-28 2022-05-26 2022-06-29 2022-07-28 2022-08-25 2022-09-29 2022-10-27 2022-11-30 2022-12-22"""


PRESSER_2011_12 = {"2011-04-27", "2011-06-22", "2011-11-02", "2012-01-25", "2012-04-25", "2012-06-20", "2012-09-13", "2012-12-12"}


def utc_minute(date, hhmm):
    ts = pd.Timestamp(f"{date} {hhmm}").tz_localize(NY).tz_convert("UTC")
    return int(ts.value // 60_000_000_000)


def bls(kind, webfetch):
    p = EXT / "macro" / f"BLS_{kind}_2010_2022.csv"
    if p.exists():
        return pd.read_csv(p).date.tolist(), "BLS archive page via Wayback (data-ext/macro)"
    return list(webfetch), "BLS archive page captured via WebFetch 2026-11-01"


def main():
    rows = []
    for kind, wf in (("NFP", dm.WEBFETCH_NFP), ("CPI", dm.WEBFETCH_CPI)):
        dates, src = bls(kind, wf)
        rows += [dict(type=kind, date=x, time_et="08:30", source=src, note="") for x in dates]
    # bea.gov listing parsed only 2017+; use ALFRED GDP vintage dates (= BEA release dates), captured via WebFetch
    gdp = sorted(set(GDP_ALFRED.split()) | {"2010-05-27"})
    rows += [dict(type="GDP", date=x, time_et="08:30", source="ALFRED GDP vintage dates via WebFetch 2026-11-01",
                  note="added: Q1-2010 second estimate" if x == "2010-05-27" else "") for x in gdp]
    fomc = pd.read_csv(EXT / "macro" / "FOMC_statements_2010_2022.csv", dtype=str).fillna("")
    miss = fomc[fomc.time_et == ""]
    c = d.load(list(range(2010, 2016)), "design")
    mins, y = c["mins"], c["y"]
    for _, r in fomc.iterrows():
        if r.time_et:
            rows.append(dict(type="FOMC", date=r.date, time_et=r.time_et, source="federalreserve.gov statement page", note=r.title[:80]))
            continue
        lo, hi = utc_minute(r.date, "12:00"), utc_minute(r.date, "15:00")
        a, b = np.searchsorted(mins, lo), np.searchsorted(mins, hi)
        seg_m, seg_r = mins[a:b][1:], np.abs(np.diff(y[a:b]))
        med = float(np.median(seg_r)) if len(seg_r) else np.nan
        best, score = None, -1.0
        for cand in ("12:30", "14:00", "14:15"):
            t0 = utc_minute(r.date, cand)
            sel = (seg_m >= t0) & (seg_m <= t0 + 2)
            s = float(seg_r[sel].max() / med) if sel.any() and med > 0 else -1.0
            if s > score:
                best, score = cand, s
        rule = "12:30" if r.date in PRESSER_2011_12 else ("14:15" if r.date < "2013-03-01" else "14:00")
        rows.append(dict(type="FOMC", date=r.date, time_et=rule, source="Fed schedule practice (12:30 presser days 2011-12; 14:15 to Jan-2013; 14:00 after)",
                         note=f"spike check {best} ({score:.1f}x median){' AGREES' if best == rule else ' differs'}"))
    ev = pd.DataFrame(rows)
    ev["utc_minute"] = [utc_minute(a, b) for a, b in zip(ev.date, ev.time_et)]
    ev = ev[ev.date <= "2022-12-31"].sort_values("utc_minute").reset_index(drop=True)
    OUT.mkdir(exist_ok=True)
    ev.to_csv(OUT / "EVENTS_2010_2022.csv", index=False)
    print(ev.groupby("type").size().to_dict(), flush=True)
    print(ev[ev.source.str.startswith("inferred")][["date", "time_et", "note"]].to_string(), flush=True)
    print("missing inferred:", len(miss), flush=True)


if __name__ == "__main__":
    main()
