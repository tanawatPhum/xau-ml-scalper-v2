"""Probe candidate download sources (owner approved new data downloads, 2026-11-01 00:35 ICT)."""
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read()
            return r.status, b
    except Exception as e:  # noqa: BLE001
        return getattr(e, "code", None) or str(e)[:80], b""


urls = []
for (y, m, d) in [(2010, 1, 5), (2011, 1, 4), (2012, 1, 4), (2012, 7, 3), (2013, 1, 3), (2014, 1, 3)]:
    urls.append(f"https://www.dukascopy.com/datafeed/USA500IDXUSD/{y}/{m - 1:02d}/{d:02d}/BID_candles_min_1.bi5")
urls += [
    "https://alfred.stlouisfed.org/release/downloaddates?rid=50",
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GVZCLS",
    "https://www.bls.gov/bls/news-release/empsit.htm",
    "https://www.bls.gov/bls/news-release/cpi.htm",
    "https://www.federalreserve.gov/monetarypolicy/fomchistorical2015.htm",
]
for u in urls:
    st, b = get(u)
    head = b[:160].decode("utf-8", "replace").replace("\n", " ") if b and not u.endswith(".bi5") else ""
    print(st, len(b), u, "|", head)
    time.sleep(2.0)
