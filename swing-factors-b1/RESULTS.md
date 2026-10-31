# Swing factors, batch 1: results (2026-10-31)

Plan `PLAN.md` (before outcomes). Code `code/build.py`, `code/analysis.py`. Output `out/REPORT.txt`,
`out/REPORT.json`. Data 2010-2019; 2020-2022 sealed; 2023+ closed. Today's $ per oz.

## Base check
| Base | 2010-16 n / O1 net / O1+O2 / stop | 2017-19 n / O1 net / O1+O2 / stop |
|---|---|---|
| k 1 large leg fade | 8735 / +0.232 / -0.038 / 6.8% | 3411 / +0.157 / +0.199 / 6.6% |
| k 1.5 large leg fade | 4623 / +0.439 / +0.164 / 7.2% | 1791 / +0.583 / +0.509 / 6.5% |
- O1 reproduces swing-adaptive-bounce (stop 3 theta) exactly.
- Letting TP run one more swing (O1+O2) is worse on average in 2010-16 for both bases.

## Verdict: no factor passes (0 of 32 tests); shuffle null 0 false passes in 20 draws
Closest (same direction in both periods, below the bar; hypotheses only):
- Session, k 1: Asia entries lose in both periods (O1 -0.049 / -0.054), London +0.552 / +0.286,
  NY +0.274 / +0.251 (London vs Asia t +2.8 / +1.5). k 1.5: London best, late worst (t +1.9 / +2.6).
- Stop risk (O3, reported only) is ~2.5x higher when sigma60 is low relative to sigma1440
  (low tercile 10.0% / 10.9% at k 1, 10.4% / 12.0% at k 1.5; high tercile 3.9-4.9%), in both
  bases and both periods: a stop set from the 60-minute scale is too tight when the hour is
  quieter than the day. NY entries have the lowest stop rates (1.3-4.2%).
- Extension (O2): no factor is consistent; e.g. k 1.5 small legs favour extension in both periods
  (O1+O2 +0.812 / +0.887) but the test fails validation (t +3.1 / +0.5).

## Reading
- Price-only features of the swing itself (leg size, speeds, range position, k 3 trend, structure)
  do not reliably separate good from bad entries, nor tell when TP should run.
- Two leads for the next pre-registered step: (1) session (avoid Asia at k 1); (2) set the stop
  (and possibly theta) from max(sigma60, sigma1440) so it is not too tight in quiet hours.
- New information is still missing: tick volume and spread (batch 2).
