# v1-r1 — daily-close revision

Public version: `v1-r1`; selected parameter set: D058. The former name v1-rx
is retained only in historical artifacts and compatibility paths. Current
entrypoint: `../v1_r1.py`. Next development uses v1-r2, then v1-r3, and so on.

Owner-authorized extension: [2010–2022 at0.5lot per rule](RESULTS_2010_2022_LOT05.md).
It uses the original locked D058 and calendar code without retuning; fresh replay
and provenance are under `out/extension_2010_2022_lot05/`. Run with
`python -B v1-r1/daily/extend_2022.py --allow-2020-2022` in a fresh output setup.
2023+ remains closed. Prior design/evaluation outputs are preserved.

This is the revised RX requested after the overnight-baseline mismatch.
See RESULTS.md for the completed experiment when available; DESIGN.md records
the pre-selection calendar/search rules. Original parent results remain historical.

## Execution
NY16:55 scheduled liquidation,16:58 market close,18:01 reopen (Sunday18:05),
historical DST. Weekends are closed. Conservative deterministic holiday session
blackouts forbid new entries but allow emergency exits on observed tradable
quotes. This is NOT a complete historical Exness holiday-calendar reconstruction.

Only quotes within the regular configured market window are used. The strategy
cannot fill at a price that is missing. A missed cutoff fills on the first later
observed tradable quote and appears in explicit late/cross-close diagnostics.
Unscheduled outages cannot be closed before they become known. No next-gap
backfill and no forced end-of-data liquidation are used.

## Run
From D:/xau-ml-scalper-claude, using D:/xau-ml-scalper/.venv/Scripts/python.exe:

```text
python -B v1-r1/daily/run_study.py check
python -B v1-r1/daily/run_study.py design
python -B v1-r1/daily/run_study.py evaluate
python -B v1-r1/daily/verify_daily.py
python -B v1-r1/daily/report_daily.py
```

Design/evaluate refuse to overwrite their lock or evaluation directory. All
source/data/calendar hashes must match. Reproduction requires a new isolated
output directory in a fresh copy, not deletion of the completed original lock.

The selected deployable research parameters are in out/LOCK.json:selected.
Use run_study.run(context, selected.rules, selected.stop_theta); run_study.load
enforces the permitted year scope and applies the same calendar to all variants.
The old parent study.py and balanced.py reproduce the historical overnight
experiment only; they are not the current daily-close entrypoint.

Tests: daily/tests plus ../tests and ../../swing-causal-execution/tests.
No live broker connection or real order submission is implemented here.
