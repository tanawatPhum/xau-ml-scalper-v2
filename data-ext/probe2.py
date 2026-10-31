"""Probe 2: archive mirrors for BLS/BEA release dates; Fed calendar; Dukascopy US500 start in 2011."""
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except Exception as e:  # noqa: BLE001
        return getattr(e, "code", None) or str(e)[:80], b""


urls = [
    "https://web.archive.org/web/2023id_/https://www.bls.gov/bls/news-release/empsit.htm",
    "https://web.archive.org/web/2023id_/https://www.bls.gov/bls/news-release/cpi.htm",
    "https://apps.bea.gov/histdata/histChildLevels.cfm?HMI=7",
    "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
]
for u in urls:
    st, b = get(u)
    t = b.decode("utf-8", "replace")
    print(st, len(b), u, "| empsit_ count", t.count("empsit_"), "cpi_ count", t.count("cpi_"), "monetary2 count", t.count("monetary2"))
    time.sleep(2.0)
# Dukascopy US500 start: first trading days of 2011 months (0-based month in URL)
for m in range(1, 13):
    for d in (3, 4, 5):
        u = f"https://www.dukascopy.com/datafeed/USA500IDXUSD/2011/{m - 1:02d}/{d:02d}/BID_candles_min_1.bi5"
        st, b = get(u, 60)
        if st == 200 and len(b) > 0:
            print("US500 first ok in month", m, "day", d, len(b))
            break
        time.sleep(1.0)
    else:
        print("US500 none in 2011 month", m)
    time.sleep(1.0)
