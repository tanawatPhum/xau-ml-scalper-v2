"""Download Dukascopy USA500IDXUSD BID 1-minute candles, 2011-10-01 .. 2022-12-31 (owner approval 2026-11-01 00:35 ICT).

Resumable and polite: sequential requests, backoff on 429/503/timeouts. Raw .bi5 payloads are kept byte-for-byte.
2023+ is never requested (protected period). Outputs are third-party price data: keep local (private).
Usage: python -B -u download_us500.py            (download)
       python -B -u download_us500.py build      (decode to yearly npz)
"""
import hashlib
import json
import lzma
import struct
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent / "us500"
NATIVE = ROOT / "native"
INV = ROOT / "inventory.jsonl"
START, END = date(2011, 10, 1), date(2022, 12, 31)
assert END < date(2023, 1, 1)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
URL = "https://www.dukascopy.com/datafeed/USA500IDXUSD/{y}/{m0:02d}/{d:02d}/BID_candles_min_1.bi5"
POINT = 1000.0


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except Exception as e:  # noqa: BLE001
        return getattr(e, "code", None) or "error", b""


def decode(raw):
    if not raw:
        return np.empty((0, 6))
    data = lzma.decompress(raw)
    n = len(data) // 24
    arr = np.array(struct.unpack(">" + "5if" * n, data[: n * 24]), dtype=float).reshape(n, 6)
    arr[:, 1:5] /= POINT
    return arr  # t_sec, open, close, low, high, volume


def done_days():
    out = {}
    if INV.exists():
        for line in INV.read_text().splitlines():
            r = json.loads(line)
            if r["status"] in (200, 404):
                out[r["day"]] = r
    return out


def one(day):
    key = day.isoformat()
    url = URL.format(y=day.year, m0=day.month - 1, d=day.day)
    status, raw, attempts = None, b"", 0
    for wait in (0, 5, 15, 45, 120, 300):
        if wait:
            time.sleep(wait)
        attempts += 1
        status, raw = fetch(url)
        if status in (200, 404):
            break
    rec = dict(day=key, status=status, attempts=attempts, bytes=len(raw), url=url)
    if status == 200:
        p = NATIVE / f"{day.year}" / f"{day.month:02d}" / f"{day.day:02d}.bi5"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        a = decode(raw)
        rec.update(sha256=hashlib.sha256(raw).hexdigest(), rows=int(len(a)), vol_minutes=int((a[:, 5] > 0).sum()))
    time.sleep(0.2)
    return rec


def download(workers=6):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock
    NATIVE.mkdir(parents=True, exist_ok=True)
    have = done_days()
    days, day = [], START
    while day <= END:
        if day.weekday() != 5 and day.isoformat() not in have:  # Saturday: no session
            days.append(day)
        day += timedelta(days=1)
    lock, n = Lock(), 0
    with INV.open("a") as inv, ThreadPoolExecutor(max_workers=workers) as ex:
        for rec in ex.map(one, days):
            with lock:
                inv.write(json.dumps(rec) + "\n")
                inv.flush()
                n += 1
                if n % 100 == 0:
                    print(time.strftime("%H:%M:%S"), "done through", rec["day"], "requests", n, "of", len(days), flush=True)
    print("DOWNLOAD FINISHED", flush=True)


def build():
    have = done_days()
    for y in range(START.year, END.year + 1):
        mins, close, vol = [], [], []
        for key, r in sorted(have.items()):
            if not key.startswith(str(y)) or r["status"] != 200 or not r.get("vol_minutes"):
                continue
            d0 = date.fromisoformat(key)
            a = decode((NATIVE / f"{d0.year}" / f"{d0.month:02d}" / f"{d0.day:02d}.bi5").read_bytes())
            a = a[a[:, 5] > 0]  # keep minutes with real ticks only
            base = int((np.datetime64(key, "m") - np.datetime64("1970-01-01T00:00", "m")).astype(np.int64))
            mins.append(base + (a[:, 0] // 60).astype(np.int64))
            close.append(a[:, 2])
            vol.append(a[:, 5])
        if mins:
            np.savez_compressed(ROOT / f"US500_M1_BID_{y}.private.npz", mins=np.concatenate(mins), close=np.concatenate(close),
                                volume=np.concatenate(vol))
            print("built", y, sum(len(m) for m in mins), flush=True)


if __name__ == "__main__":
    build() if len(sys.argv) > 1 and sys.argv[1] == "build" else download()
