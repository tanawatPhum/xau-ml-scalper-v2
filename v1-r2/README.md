# v1-r2

The current revision after v1-r1. It is v1-r1 (D058) with per-session formulas for rules A and B.
- Plan: [PLAN.md](PLAN.md). Results (Thai): [RESULTS.md](RESULTS.md).
- Entrypoint: `v1_r2.py`. Locked parameters: `out/LOCK.json` (+ `.sha256`).
- v1-r1's code, calendar and lock are imported read-only and are not modified.

## Run
From D:\xau-ml-scalper-claude, using D:\xau-ml-scalper\.venv\Scripts\python.exe:

```text
python -B v1-r2/v1_r2.py check      # reproduces v1-r1 signals and 2010-16 metrics exactly
python -B v1-r2/v1_r2.py design     # refuses if out/LOCK.json exists
python -B v1-r2/v1_r2.py evaluate   # 2010-19 and 2017-19, three cost cases; refuses if done
python -B v1-r2/v1_r2.py extend     # 2010-22 descriptive (owner-authorized years), 0.1 lot
python -B v1-r2/summary.py
python -B v1-r2/diff_stats.py       # day-clustered t of the daily difference vs v1-r1; per rule x session
```

## Notes
- No live orders.
- 2023+ is never read.
- 2017-19 validation is reused (seen in earlier work); 2020-22 is descriptive.
