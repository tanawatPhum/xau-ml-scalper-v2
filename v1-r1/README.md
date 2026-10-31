# v1-r1

Current public version: **v1-r1**, formerly v1-rx; internal strategy ID D058.
Next developments use **v1-r2, v1-r3, …**; see [version policy](../VERSIONING.md).
Canonical entrypoint: `v1_r1.py`; version metadata: `VERSION.json`.

Latest requested size/period report: [v1-r1,2010–2022 at0.5lot per rule](daily/RESULTS_2010_2022_LOT05.md).
Frozen parameters; no new tuning on2020–2022.

**Current revision:** [v1-r1 daily-close results](daily/RESULTS.md), with
`v1_r1.py` as the current parameter-loading/simulation entrypoint.
Selected D058 closes before the configured market close in all2,802 observed
2010-2019 trades; source/calendar/selection are frozen under `daily/out/`.
See [daily README](daily/README.md) for execution and reproduction.
`current_rx.py` and the `v1-rx/` directory alias support older references.

**Historical experiment below:** the original parent runs used the older
overnight-capable v1 and remain preserved. See [baseline review](BASELINE_STATUS.md).

Research fork of Swing v1, using the unchanged corrected causal execution engine.
Owner-authorized design outcomes:2010-2016. Evaluation scope:2010-2019 only.
This directory does not replace the frozen v1 or enable live trading.

- [Historical overnight results](RESULTS.md): earlier comparison, not the current daily-close report.
- [Protocol and disclosed amendment](PLAN.md).
- `strategy.py`: causal signal/entry filters; all confirmation events remain available for exits.
- `baseline_engine.py`: byte-identical snapshot of `../swing-causal-execution/engine.py`.
- `study.py`: original bounded search, lock and evaluation.
- `balanced.py`: secondary selection from the existing training table, removing only the self-imposed trade-count floor; separately locked and evaluated.
- `out/LOCK.json`: immutable original fallback P01, which failed original training gates.
- `out/balanced/LOCK.json`: separate balanced P20 selection and provenance.
- `research/CAUSAL_CHECKS.json`: actual-price prefix invariance checks; no future-dependent signals.

## Assumptions

100,000THB start;0.1lot =10oz PER RULE; FX33.77THB/USD; fixed spread0.168USD/oz.
Two rules may overlap, so maximum aggregate exposure is0.2lot. No compounding.
Orders decided at a closed minute fill one minute later; a missing entry minute
cancels entry. Close-triggered stops fill at the next observed quote. Gaps reset
signals and positions exit only after the gap becomes observable. Equity marks
open positions to the executable liquidation side and includes estimated costs.
There is no margin/stop-out, swap, financing or intrabar stop model.

Historical bid/ask and a hypothetical extra commission/slippage scenario are
reported separately. A hypothetical0.5lot PER RULE scales money P/L by5, but
percentage drawdown must be recomputed from the scaled equity path.

## Reproduce

The completed outputs are protected against accidental overwrites. Use a fresh
copy with a fresh `out/` directory for a full reproduction; do not remove the
original locks. The cache path must continue to refer to the same local inputs.
Source and data hashes are verified before and after computation. Locked source
paths are absolute, so an existing lock cannot silently certify changed code.

```powershell
& 'D:\xau-ml-scalper\.venv\Scripts\python.exe' -B v1-r1/study.py design
& 'D:\xau-ml-scalper\.venv\Scripts\python.exe' -B v1-r1/study.py evaluate
& 'D:\xau-ml-scalper\.venv\Scripts\python.exe' -B v1-r1/balanced.py lock
& 'D:\xau-ml-scalper\.venv\Scripts\python.exe' -B v1-r1/balanced.py evaluate
& 'D:\xau-ml-scalper\.venv\Scripts\python.exe' -B -m pytest v1-r1/tests swing-causal-execution/tests -q -p no:cacheprovider --basetemp 'D:\xau-ml-scalper-claude\v1-r1\.test-temp-new'
```

The secondary experiment is explicitly exploratory: its selection gate was
amended after the training search, and2017-2019 was seen in earlier project work.
No2020+ price files are accessed by these runners. Price-derived trade/equity
artifacts remain local under `*.private.*` names.
