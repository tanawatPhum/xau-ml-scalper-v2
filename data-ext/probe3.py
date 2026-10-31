"""Probe 3: BEA GDP vintage page content; Wayback BLS archive pages with backoff; one US500 day decoded."""
import lzma
import re
import struct
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


st, b = get("https://apps.bea.gov/histdata/histChildLevels.cfm?HMI=7")
t = re.sub(r"<[^>]+>", " ", b.decode("utf-8", "replace"))
t = re.sub(r"\s+", " ", t)
print("BEA", st, t[:1500], flush=True)

for u in ["https://web.archive.org/web/2023id_/https://www.bls.gov/bls/news-release/empsit.htm"]:
    for attempt in range(4):
        st, b = get(u)
        print("WAYBACK", attempt, st, len(b), flush=True)
        if st == 200:
            s = b.decode("utf-8", "replace")
            names = re.findall(r"empsit_(\d{8})", s)
            print("empsit dates found", len(names), names[:5], names[-5:], flush=True)
            break
        time.sleep(30 * (attempt + 1))


def decode(raw, point):
    data = lzma.decompress(raw)
    rows = [struct.unpack(">5if", data[i:i + 24]) for i in range(0, len(data), 24)]
    return [(r[0], r[1] / point, r[2] / point, r[3] / point, r[4] / point, r[5]) for r in rows]


for day in ("2011/09/03", "2012/00/04", "2012/06/03", "2015/00/06"):
    st, b = get(f"https://www.dukascopy.com/datafeed/USA500IDXUSD/{day}/BID_candles_min_1.bi5")
    if st == 200 and b:
        rows = decode(b, 1000)
        vol = sum(1 for r in rows if r[5] > 0)
        moves = sum(1 for r in rows if r[3] != r[4])
        print("US500", day, "rows", len(rows), "vol>0", vol, "hi!=lo", moves, "first", rows[0], "mid", rows[len(rows) // 2], flush=True)
    else:
        print("US500", day, st, flush=True)
    time.sleep(1.5)
