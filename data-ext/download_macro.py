"""Download macro data for v1-r3 (owner approval 2026-11-01 00:35 ICT). Everything is truncated at 2022-12-31.

Outputs (data-ext/macro/):
  GVZ_daily_2009_2022.csv          CBOE gold ETF volatility index (close), source cdn.cboe.com
  FOMC_statements_2010_2022.csv    FOMC statement date + release time (ET) from federalreserve.gov pages
  BLS_NFP_2010_2022.csv            Employment Situation release dates (08:30 ET), Wayback copy of the BLS archive page
  BLS_CPI_2010_2022.csv            CPI release dates (08:30 ET), same method
  BEA_GDP_2010_2022.csv            GDP release dates (08:30 ET), bea.gov GDP news-release listing
  SOURCES.json                     URLs, fetch times, row counts, sha256, cross-checks
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = Path(__file__).resolve().parent / "macro"
RAW = OUT / "raw"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
LAST = "2022-12-31"
SRC = {}


def fetch(url, name=None, waits=(0, 10, 30, 60, 120)):
    for w in waits:
        if w:
            time.sleep(w)
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                b = r.read()
            if name:
                (RAW / name).write_bytes(b)
            SRC[url] = dict(fetched_utc=datetime.now(timezone.utc).isoformat(), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
            return b.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            print("retry", url, getattr(e, "code", str(e)[:60]), flush=True)
    raise RuntimeError(f"failed {url}")


def gvz():
    t = fetch("https://cdn.cboe.com/api/global/us_indices/daily_prices/GVZ_History.csv", "GVZ_History.csv")
    df = pd.read_csv(pd.io.common.StringIO(t))
    df["date"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y")
    df = df[df.date <= LAST][["date", "GVZ"]]
    df.to_csv(OUT / "GVZ_daily_2009_2022.csv", index=False, date_format="%Y-%m-%d")
    return dict(rows=len(df), first=str(df.date.min().date()), last=str(df.date.max().date()))


def fomc():
    links = {}
    pages = [f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{y}.htm" for y in range(2010, 2021)]
    pages.append("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm")
    for p in pages:
        t = fetch(p, p.rsplit("/", 1)[1])
        for href, d in re.findall(r'href="([^"]*monetary/?(\d{8})a\.htm)"', t):
            if "20100101" <= d <= "20221231":
                links[d] = href if href.startswith("http") else "https://www.federalreserve.gov" + href
        time.sleep(1.0)
    rows = []
    for d, u in sorted(links.items()):
        t = fetch(u)
        title = re.search(r"<title>(.*?)</title>", t, re.S)
        title = re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
        m = re.search(r"For release at\s+(\d{1,2}):(\d{2})\s*([ap])\.?m\.?\s*(EST|EDT|ET)?", t, re.I)
        tm = f"{int(m.group(1)) % 12 + (12 if m.group(3).lower() == 'p' else 0):02d}:{m.group(2)}" if m else ""
        rows.append(dict(date=f"{d[:4]}-{d[4:6]}-{d[6:]}", time_et=tm, title=title, url=u))
        time.sleep(0.7)
    df = pd.DataFrame(rows)
    stm = df[df.title.str.contains("statement", case=False) & ~df.title.str.contains("minutes", case=False)]
    df.to_csv(OUT / "FOMC_monetary_pressreleases_2010_2022.csv", index=False)
    stm.to_csv(OUT / "FOMC_statements_2010_2022.csv", index=False)
    return dict(press_releases=len(df), statements=len(stm), missing_time=int((stm.time_et == "").sum()))


WEBFETCH_NFP = """2010-01-08 2010-02-05 2010-03-05 2010-04-02 2010-05-07 2010-06-04 2010-07-02 2010-08-06 2010-09-03 2010-10-08 2010-11-05 2010-12-03
2011-01-07 2011-02-04 2011-03-04 2011-04-01 2011-05-06 2011-06-03 2011-07-08 2011-08-05 2011-09-02 2011-10-07 2011-11-04 2011-12-02
2012-01-06 2012-02-03 2012-03-09 2012-04-06 2012-05-04 2012-06-01 2012-07-06 2012-08-03 2012-09-07 2012-10-05 2012-11-02 2012-12-07
2013-01-04 2013-02-01 2013-03-08 2013-04-05 2013-05-03 2013-06-07 2013-07-05 2013-08-02 2013-09-06 2013-10-22 2013-11-08 2013-12-06
2014-01-10 2014-02-07 2014-03-07 2014-04-04 2014-05-02 2014-06-06 2014-07-03 2014-08-01 2014-09-05 2014-10-03 2014-11-07 2014-12-05
2015-01-09 2015-02-06 2015-03-06 2015-04-03 2015-05-08 2015-06-05 2015-07-02 2015-08-07 2015-09-04 2015-10-02 2015-11-06 2015-12-04
2016-01-08 2016-02-05 2016-03-04 2016-04-01 2016-05-06 2016-06-03 2016-07-08 2016-08-05 2016-09-02 2016-10-07 2016-11-04 2016-12-02
2017-01-06 2017-02-03 2017-03-10 2017-04-07 2017-05-05 2017-06-02 2017-07-07 2017-08-04 2017-09-01 2017-10-06 2017-11-03 2017-12-08
2018-01-05 2018-02-02 2018-03-09 2018-04-06 2018-05-04 2018-06-01 2018-07-06 2018-08-03 2018-09-07 2018-10-05 2018-11-02 2018-12-07
2019-01-04 2019-02-01 2019-03-08 2019-04-05 2019-05-03 2019-06-07 2019-07-05 2019-08-02 2019-09-06 2019-10-04 2019-11-01 2019-12-06
2020-01-10 2020-02-07 2020-03-06 2020-04-03 2020-05-08 2020-06-05 2020-07-02 2020-08-07 2020-09-04 2020-10-02 2020-11-06 2020-12-04
2021-01-08 2021-02-05 2021-03-05 2021-04-02 2021-05-07 2021-06-04 2021-07-02 2021-08-06 2021-09-03 2021-10-08 2021-11-05 2021-12-03
2022-01-07 2022-02-04 2022-03-04 2022-04-01 2022-05-06 2022-06-03 2022-07-08 2022-08-05 2022-09-02 2022-10-07 2022-11-04 2022-12-02""".split()
WEBFETCH_CPI = """2010-01-15 2010-02-19 2010-03-18 2010-04-14 2010-05-19 2010-06-17 2010-07-16 2010-08-13 2010-09-17 2010-10-15 2010-11-17 2010-12-15
2011-01-14 2011-02-17 2011-03-17 2011-04-15 2011-05-13 2011-06-15 2011-07-15 2011-08-18 2011-09-15 2011-10-19 2011-11-16 2011-12-16
2012-01-19 2012-02-17 2012-03-16 2012-04-13 2012-05-15 2012-06-14 2012-07-17 2012-08-15 2012-09-14 2012-10-16 2012-11-15 2012-12-14
2013-01-16 2013-02-21 2013-03-15 2013-04-16 2013-05-16 2013-06-18 2013-07-16 2013-08-15 2013-09-17 2013-10-30 2013-11-20 2013-12-17
2014-01-16 2014-02-20 2014-03-18 2014-04-15 2014-05-15 2014-06-17 2014-07-22 2014-08-19 2014-09-17 2014-10-22 2014-11-20 2014-12-17
2015-01-16 2015-02-26 2015-03-24 2015-04-17 2015-05-22 2015-06-18 2015-07-17 2015-08-19 2015-09-16 2015-10-15 2015-11-17 2015-12-15
2016-01-20 2016-02-19 2016-03-16 2016-04-14 2016-05-17 2016-06-16 2016-07-15 2016-08-16 2016-09-16 2016-10-18 2016-11-17 2016-12-15
2017-01-18 2017-02-15 2017-03-15 2017-04-14 2017-05-12 2017-06-14 2017-07-14 2017-08-11 2017-09-14 2017-10-13 2017-11-15 2017-12-13
2018-01-12 2018-02-14 2018-03-13 2018-04-11 2018-05-10 2018-06-12 2018-07-12 2018-08-10 2018-09-13 2018-10-11 2018-11-14 2018-12-12
2019-01-11 2019-02-13 2019-03-12 2019-04-10 2019-05-10 2019-06-12 2019-07-11 2019-08-13 2019-09-12 2019-10-10 2019-11-13 2019-12-11
2020-01-14 2020-02-13 2020-03-11 2020-04-10 2020-05-12 2020-06-10 2020-07-14 2020-08-12 2020-09-11 2020-10-13 2020-11-12 2020-12-10
2021-01-13 2021-02-10 2021-03-10 2021-04-13 2021-05-12 2021-06-10 2021-07-13 2021-08-11 2021-09-14 2021-10-13 2021-11-10 2021-12-10
2022-01-12 2022-02-10 2022-03-10 2022-04-12 2022-05-11 2022-06-10 2022-07-13 2022-08-10 2022-09-13 2022-10-13 2022-11-10 2022-12-13""".split()


def bls(kind, page, prefix, webfetch):
    t = fetch(f"https://web.archive.org/web/2023id_/https://www.bls.gov/bls/news-release/{page}", f"wayback_{page}",
              waits=(0, 30, 60, 90, 120, 180))
    ds = sorted({f"{s[4:]}-{s[:2]}-{s[2:4]}" for s in re.findall(prefix + r"_(\d{8})", t)})
    ds = [x for x in ds if "2010-01-01" <= x <= LAST]
    pd.DataFrame(dict(date=ds, time_et="08:30")).to_csv(OUT / f"BLS_{kind}_2010_2022.csv", index=False)
    return dict(rows=len(ds), only_wayback=sorted(set(ds) - set(webfetch)), only_webfetch=sorted(set(webfetch) - set(ds)))


MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"


def gdp():
    rows = []
    for page in range(0, 60):
        t = fetch(f"https://www.bea.gov/taxonomy/term/451?page={page}", f"bea_451_p{page}.html")
        text = re.sub(r"<[^>]+>", "\n", t)
        text = re.sub(r"[ \t]+", " ", text)
        lines = [x.strip() for x in text.split("\n") if x.strip()]
        found = 0
        for i, ln in enumerate(lines):
            if "Gross Domestic Product" in ln and "State" not in ln and "County" not in ln and "Industry" not in ln and "Territor" not in ln:
                ctx = " ".join(lines[max(0, i - 4): i + 5])
                m = re.search(rf"({MONTHS}) (\d{{1,2}}), (\d{{4}})", ctx)
                if m:
                    rows.append(dict(date=pd.to_datetime(f"{m.group(1)} {m.group(2)} {m.group(3)}").strftime("%Y-%m-%d"), title=ln))
                    found += 1
        years = [int(r["date"][:4]) for r in rows]
        print("bea page", page, "found", found, "min year", min(years) if years else None, flush=True)
        if years and min(years) < 2010:
            break
        time.sleep(1.0)
    df = pd.DataFrame(rows).drop_duplicates()
    df = df[(df.date >= "2010-01-01") & (df.date <= LAST)].sort_values("date")
    df["time_et"] = "08:30"
    df.to_csv(OUT / "BEA_GDP_2010_2022.csv", index=False)
    return dict(rows=len(df), per_year=df.date.str[:4].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, fn in (("gvz", gvz), ("fomc", fomc), ("nfp", lambda: bls("NFP", "empsit.htm", "empsit", WEBFETCH_NFP)),
                     ("cpi", lambda: bls("CPI", "cpi.htm", "cpi", WEBFETCH_CPI)), ("gdp", gdp)):
        try:
            report[name] = fn()
        except Exception as e:  # noqa: BLE001
            report[name] = dict(error=str(e))
        print(name, json.dumps(report[name])[:600], flush=True)
    (OUT / "SOURCES.json").write_text(json.dumps(dict(report=report, sources=SRC, approved="owner 2026-11-01 00:35 ICT",
                                                      truncated_at=LAST), indent=1))
    print("MACRO DONE", flush=True)
