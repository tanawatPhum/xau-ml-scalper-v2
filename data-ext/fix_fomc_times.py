"""Re-parse FOMC statement pages whose release time was not found (HTML entities / tags around the time)."""
import html
import re
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = Path(__file__).resolve().parent / "macro"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def text_of(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        t = r.read().decode("utf-8", "replace")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t).replace("\xa0", " "))


df = pd.read_csv(OUT / "FOMC_statements_2010_2022.csv", dtype=str).fillna("")
for i, r in df[df.time_et == ""].iterrows():
    t = text_of(r.url)
    m = re.search(r"For (?:release|use) at\s+(\d{1,2}):(\d{2})\s*([ap])\.?\s*m\.?", t, re.I)
    if m:
        h = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "p" else 0)
        df.loc[i, "time_et"] = f"{h:02d}:{m.group(2)}"
    k = t.find("elease")
    print(r.date, df.loc[i, "time_et"] or "MISSING", "|", t[max(0, k - 80): k + 120] if not m else "", flush=True)
    time.sleep(0.7)
df.to_csv(OUT / "FOMC_statements_2010_2022.csv", index=False)
print("remaining missing", int((df.time_et == "").sum()))
