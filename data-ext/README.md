# data-ext: external data downloaded for v1-r3

The owner approved downloading all new data needed for the v1-r3 experiments (2026-11-01, 00:35 ICT).
Everything is truncated at 2022-12-31; 2023+ is never requested or stored.

| File | Content | Source |
|---|---|---|
| `macro/GVZ_daily_2009_2022.csv` | CBOE Gold ETF Volatility Index, daily close, 2009-09-18 to 2022-12-30 | cdn.cboe.com GVZ_History.csv |
| `macro/FOMC_statements_2010_2022.csv` | 109 FOMC statement dates. Release time (ET) is given for 2016+; earlier pages show no time | federalreserve.gov FOMC calendar and statement pages |
| `../v1-r3/out/EVENTS_2010_2022.csv` | Combined release table: NFP 156, CPI 156, GDP 155 (all 08:30 ET), FOMC 109 | see note below |
| `us500/US500_M1_BID_{year}.private.npz` | Dukascopy USA500IDXUSD BID 1-minute closes, minutes with ticks only. Real data from early 2012; 2013 has a gap | datafeed via www.dukascopy.com |
| `us500/inventory.jsonl`, `us500/native/` | Per-day request log (status, sha256) and the raw .bi5 payloads byte-for-byte | same |

**Notes**
- bls.gov blocks this device (403), and FRED / ALFRED time out.
  - NFP and CPI release dates were taken from the BLS archive pages via WebFetch; Wayback copies were rate-limited.
  - GDP release dates are the ALFRED GDP vintage dates via WebFetch, plus 2010-05-27.
- FOMC times for 2010-15 follow the Fed's schedule practice:
  - 12:30 ET on the 2011-12 press-conference days;
  - 14:15 ET through Jan 2013;
  - 14:00 ET from Mar 2013.
  A check against gold 1-minute spikes is recorded in the events table.
- **US500 build:** the download may still be running for 2017-2022. When `us500_download.log` says `DOWNLOAD FINISHED`, rerun:
  `D:\xau-ml-scalper\.venv\Scripts\python.exe -B -u download_us500.py build`
- **Privacy:** US500 files are third-party price data. Keep them local (`*.private.*`).
