"""Post-lock reporting and independent accounting; does not change selection."""
from __future__ import annotations
from datetime import datetime,timezone
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import trial

ROOT=Path(__file__).resolve().parent;OUT=ROOT/"out"
train=json.loads((OUT/"TRAINING.json").read_text(encoding="utf-8"))
lock=json.loads((OUT/"LOCK.json").read_text(encoding="utf-8"))
validation=json.loads((OUT/"VALIDATION.json").read_text(encoding="utf-8"))
assert trial.sha(OUT/"LOCK.json")== (OUT/"LOCK.sha256").read_text().strip()
assert trial.source_hashes()==lock["sources"]
trial.v.d.study.verify_hashes(lock["training_data_hashes"])
assert not lock["selected"] and validation["years_read"]==[]
c,ab=trial.load(list(range(2010,2017)),"design")
# Reconstruct the baseline union from trade intervals, independently of gross_oz.
change=np.zeros(len(c["mins"])+1,np.int64)
ae=np.searchsorted(c["mins"],ab.trades.t_entry.to_numpy(np.int64))
ax=np.searchsorted(c["mins"],ab.trades.t_exit.to_numpy(np.int64))
np.add.at(change,ae,1);np.add.at(change,ax,-1)
active=np.cumsum(change[:-1])
np.testing.assert_array_equal(active*10,ab.equity.gross_oz.to_numpy())
rows=[];checks=[]
for row in train["rows"]:
    s=row["spec"]
    with np.load(OUT/(s["id"]+"_training.private.npz"),allow_pickle=False) as z:
        t=z["trades"];e=z["equity_change"];mins=z["mins"]
    np.testing.assert_array_equal(mins,c["mins"])
    ei=t[:,1].astype(np.int64);xi=t[:,2].astype(np.int64);si=t[:,0].astype(np.int64)
    np.testing.assert_array_equal(mins[ei]-mins[si],np.ones(len(t),np.int64))
    np.testing.assert_array_equal(mins[xi]-mins[ei],np.full(len(t),s["hold"],np.int64))
    gross=t[:,3]*(c["mid"][xi]-c["mid"][ei])*337.7
    np.testing.assert_allclose(t[:,5],gross-.168*337.7,rtol=0,atol=1e-6)
    overlap=int((active[ei]>0).sum());assert overlap==row["metrics"]["overlap_count"]
    np.testing.assert_allclose(sum(y["net"] for y in row["yearly"].values()),e[-1],atol=1e-6)
    np.testing.assert_allclose(t[:,5].sum(),e[-1],atol=1e-6)
    half=(c["ask"]-c["bid"])/2
    historical=gross-(half[ei]+half[xi])*337.7
    np.testing.assert_allclose(historical.sum(),row["metrics"]["historical_net"],atol=1e-6)
    checks.append(dict(id=s["id"],trade_cost_arithmetic=True,entry_and_timed_exit_exact=True,
                       overlap_count_reconstructed_from_ab_intervals=overlap,annual_and_closed_net_reconcile=True))
    if s["family"]=="Ma_night_reversal_momentum":
        # This post-lock descriptive subset does not amend all-years eligibility.
        cutoff=int(pd.Timestamp("2013-07-05",tz="Asia/Shanghai").tz_convert("UTC").value//60_000_000_000)
        j=int(np.searchsorted(c["mins"],cutoff))
        mask=mins[ei]>=cutoff;pt=t[mask].copy();pt[:,0:3]-=j
        pe=e[j:]-(e[j-1] if j else 0.)
        cp={k:(val[j:] if isinstance(val,np.ndarray) and val.shape==(len(mins),) else val) for k,val in c.items()}
        cp["calendar"]=trial.v.d.schedule(cp["mins"])
        abe=ab.equity.iloc[j:].copy();abe["equity"]-=float(ab.equity.equity.iloc[j-1])-100000.
        pm=trial.metrics(cp,SimpleNamespace(equity=abe),(pt,pe,np.zeros(len(pe)),0))
        pm["example_net"]=float(t[mask,5].sum()-.06*337.7*mask.sum())
        pm["historical_net"]=float(historical[mask].sum())
        sg=trial.hypothesis.signals(c,s);sr=trial.execute(c,s,sg,stop=3.)
        st=sr[0];sm=mins[st[:,1].astype(np.int64)]>=cutoff
        spe=sr[1][j:]-sr[1][j-1];spt=st[sm].copy();spt[:,:3]-=j
        spm=trial.metrics(cp,SimpleNamespace(equity=abe),(spt,spe,np.zeros(len(pe)),0))
        spm["example_net"]=float(st[sm,5].sum()-.06*337.7*sm.sum())
        sei=st[sm,1].astype(np.int64);sxi=st[sm,2].astype(np.int64)
        spm["historical_net"]=float((st[sm,3]*(c["mid"][sxi]-c["mid"][sei])*337.7-(half[sei]+half[sxi])*337.7).sum())
        rows.append(dict(id=s["id"],scope="2013-07-05 to2016-12-31 descriptive only",metrics=pm,stop3_sensitivity=spm))
trial.write(OUT/"NIGHT_POSTLAUNCH_DESCRIPTIVE.json",dict(rows=rows,selection_unchanged=True))
assert trial.source_hashes()==lock["sources"];trial.v.d.study.verify_hashes(lock["training_data_hashes"])
verification=dict(verified_utc=datetime.now(timezone.utc).isoformat(),source_hashes_unchanged=True,
                  training_data_hashes_unchanged=True,baseline_reproduced_exactly=True,
                  synthetic_tests=dict(count=8,status="PASS",entry_point="test_synthetic.py"),
                  actual_prefix_checks=[r["prefix_check"] for r in train["rows"]],
                  independent_accounting_checks=checks,validation_years_read=[],post2019_price_files_read=[],
                  locked_selection=[],new_version_promoted=False)
trial.write(ROOT/"VERIFICATION.json",verification)

fmt=lambda x:f"{x:,.2f}"
lines=["# Literature-to-Rule-C pilots: NOT_CONFIRMED","",
       "Both paper-derived primary transfers failed2010–2016 training after costs. The two fixed3volatility stop sensitivities also failed. No2017–2019 validation prices were opened, and no2020+ prices were opened. A/B and version records remain unchanged.","",
       "The final protocol, two primaries and two nonselectable stop sensitivities were written before outcomes. At0.1lot(10oz), FX33.77, spread.168USD/oz, fresh100,000THB. Example costs additionally charge commission.01 and adverse slippage.02USD/oz/side. Historical quotes use both entry/exit BID/ASK spreads.","",
       "| Cell | Fixed netTHB | Example netTHB | Historical netTHB | PF | Trades | Natural overlap |2014–2016netTHB | EquityDDTHB |",
       "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
for row in train["rows"]:
    for label,m in ((row["spec"]["id"],row["metrics"]),(row["spec"]["id"]+" +stop3 sensitivity",row["stop3_sensitivity"]["metrics"])):
        lines.append(f"|{label}|{fmt(m['net'])}|{fmt(m['example_net'])}|{fmt(m['historical_net'])}|{m['profit_factor']:.3f}|{m['trades']}|{m['overlap_count']}/{m['trades']}={100*m['overlap']:.2f}%|{fmt(m['net_2014_2016'])}|{fmt(m['dd'])}|")
lines += ["","All four cells pass the overlap<=30%, minimum50trades, and calendar/terminal-position checks; all fail net>0, PF>1, positive2014–2016 and positive example-cost net. Market-close crossings, session crossings, late-cutoff exits, >30minute gap-spanning trades and terminal positions are all zero for these C cells. No A/B position veto was used. Simultaneous entries count, A/B exits on that minute do not, and A+B holding counts once.","",
          "## Exact adaptations and evidence limits","",
          "Xu,Bouri,Saeed&Wen(2020), DOI[10.1016/j.resourpol.2020.101830](https://doi.org/10.1016/j.resourpol.2020.101830): GLD11:30–12:00NY direction predicts15:30–16:00NY. Local adaptation signals15:29, fills15:30, exits16:00. Original regressionR²=.49%,OOSR²=.26%; reported sign-timing t=1.23 is weak. Mean-return units were not independently verified and are omitted. This ETF finding is not an after-cost XAUUSD claim.","",
          "Ma,Bouri,Xu&Zhou(2025), DOI[10.1016/j.gfj.2025.101084](https://doi.org/10.1016/j.gfj.2025.101084): metadata/publisher preview describes SHFE gold/silver night-session reversal followed by momentum. Full text was unavailable. Our Shanghai21:00–21:30 impulse,21:30–22:00 opposite partial retracement,22:01entry/23:00exit is a mechanism transfer, not a paper replication. Direction follows the original impulse; no optimized magnitude threshold or target.","",
          "The frozen Night eligibility used all2010–2016, even though the pre2013-07-05 period predates the SHFE night session and belongs only to a placebo regime. This is an explicit protocol limitation. It was noticed after outcomes had finished, so the failed protocol was preserved without amendment/reselection. Prelaunch observations are not evidence for a night-market mechanism; the postlaunch subset below is descriptive only.","",
          "| Night subset | Trades | Fixed netTHB | Example netTHB | Historical netTHB | Natural overlap | EquityDDTHB |",
          "|---|---:|---:|---:|---:|---:|---:|"]
for label,m in (("Primary from2013-07-05",rows[0]["metrics"]),("Stop3 sensitivity from2013-07-05",rows[0]["stop3_sensitivity"])):
    lines.append(f"|{label}|{m['trades']}|{fmt(m['net'])}|{fmt(m['example_net'])}|{fmt(m['historical_net'])}|{m['overlap_count']}/{m['trades']}={100*m['overlap']:.2f}%|{fmt(m['dd'])}|")
lines += ["",f"Prelaunch placebo: primary219trades net{fmt(train['rows'][1]['night_regimes_descriptive']['pre_2013_07_05_placebo']['closed_net'])}THB; fixed-stop sensitivity219trades net{fmt(train['rows'][1]['stop3_sensitivity']['night_regimes_descriptive']['pre_2013_07_05_placebo']['closed_net'])}THB. Neither regime is used to rescue selection.","",
          "## Portfolio effect and0.5lot scaling","",
          f"Locked A/B baseline: net{fmt(train['ab_metrics']['net'])}THB, equityDD{fmt(train['ab_metrics']['dd'])}THB,2,737trades. It reproduces the r2 lock exactly.","",
          "| Primary | A/B+C net0.1lotTHB | A/B+C DD0.1lotTHB | C net0.5lotTHB | C DD0.5lotTHB | C lowest equity0.5lotTHB |",
          "|---|---:|---:|---:|---:|---:|"]
for r in train["rows"]:
    m=r["metrics"];f=m["lot05"]
    lines.append(f"|{r['spec']['id']}|{fmt(m['combined_net'])}|{fmt(m['combined_dd'])}|{fmt(f['net'])}|{fmt(f['dd'])}|{fmt(f['lowest'])}|")
lines += ["","Both additions lower A/B net and increase absolute equityDD.0.5lot uses fixed5×dollar exposure, recomputes DD% against100k, and is not executable C-only capital history once equity is nonpositive. The model has no margin call, stop-out, funding or size-dependent impact.","",
          "## Annual fixed-spread net at0.1lot","",
          "| Year | Xu primaryTHB | Xu stop3THB | Night primaryTHB | Night stop3THB |",
          "|---|---:|---:|---:|---:|"]
for y in map(str,range(2010,2017)):
    a,b=train["rows"]
    lines.append(f"|{y}|{fmt(a['yearly'][y]['net'])}|{fmt(a['stop3_sensitivity']['yearly'][y]['net'])}|{fmt(b['yearly'][y]['net'])}|{fmt(b['stop3_sensitivity']['yearly'][y]['net'])}|")
lines += ["","## Verification and scope","",
          "Eight synthetic checks pass: two-sided signal direction, DST clocks, missing anchor/window rejection, signal-prefix invariance, next-minute fills/timed exits/cost arithmetic, A/B union and forbidden-year checks. Both real-data prefix checks ended with an open position and reproduced the full historical prefix without terminal forced liquidation. An independent trade-interval reconstruction matches baseline gross exposure and both overlap counts; closed/net/yearly sums and fixed/historical fill costs reconcile. Source and2010–2016data hashes remain unchanged.","",
          "Sources: `PLAN.md`, `signals.py`, `trial.py`, `test_synthetic.py`; frozen outputs `out/TRAINING.json`, `out/LOCK.json`+SHA, `out/VALIDATION.json`; postlaunch-only descriptive accounting `out/NIGHT_POSTLAUNCH_DESCRIPTIVE.json`; checks `VERIFICATION.json`. The all-years failed selection is empty; validation status isNO_TRAINING_CANDIDATE.","",
          "The previous48structural trials and earlier clock fades make this a continuation of a large research search.2017–2019 is reused exploratory validation, not a virgin holdout. Old requested narrative summaries include2017–2022aggregates; those were inspected only for prior-test inventory, with no2020+ quote/result arrays opened by this pilot. No further recipe, opposite-direction rescue, parameter tuning or version promotion follows these failures.",""]
(ROOT/"RESULTS.md").write_text("\n".join(lines),encoding="utf-8")
print(json.dumps(dict(status="NOT_CONFIRMED",training_cells=4,postlaunch=rows,verification=verification),indent=2))
