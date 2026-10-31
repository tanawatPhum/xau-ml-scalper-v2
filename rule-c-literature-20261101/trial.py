"""Bounded literature pilots; no promotion, no access to post-2019 quotes."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"out"
os.environ["NUMBA_CACHE_DIR"]=str(ROOT/"numba_cache")
sys.path.insert(0,str(ROOT.parent/"v1-r2"))
sys.path.insert(0,str(ROOT.parent/"rule-c-research-20261101"))
import v1_r2 as v
from replay import replay
import signals as hypothesis


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+"\n",encoding="utf-8")
def source_hashes():
    paths=[ROOT/p for p in ("PLAN.md","signals.py","trial.py","test_synthetic.py")]
    paths += [ROOT.parent/"rule-c-research-20261101"/"replay.py",v.ROOT/"v1_r2.py",v.ROOT/"PLAN.md",v.OUT/"LOCK.json",v.OUT/"LOCK.sha256"]
    paths += list(v.d.sources())
    return {str(Path(p).resolve()):sha(p) for p in paths}


def guards():
    lock,ov=v.read_lock();base=v.r1_lock()["selected"]
    assert sha(v.ROOT/"v1_r2.py")==lock["code_sha256"]
    assert sha(v.ROOT/"PLAN.md")==lock["plan_sha256"]
    assert sha(v.d.OUT/"LOCK.json")==lock["r1_lock_sha256"]
    return base,ov


def permitted(years,phase):
    expected=list(range(2010,2017)) if phase=="design" else [2017,2018,2019]
    if years!=expected:raise ValueError("only exact design2010–2016 or frozen validation2017–2019")


def load(years,phase):
    permitted(years,phase);base,ov=guards()
    c=v.add_session(v.d.load(years,"design" if phase=="design" else "evaluate"))
    cfg=v.d.engine.Config()
    ab=v.run(c,base["rules"],ov,base["stop_theta"],cfg)
    if phase=="design":
        locked=v.read_lock()[0]["training_metrics"];actual=v.d.metrics(ab)
        for k in ("net","dd","trades","recent","open_positions"):
            assert abs(actual[k]-locked[k])<1e-6,(k,actual[k],locked[k])
    return c,ab


def execute(c,s,sg,cost="fixed",stop=None):
    half=(c["ask"]-c["bid"])/2 if cost=="historical" else np.full(len(c["mins"]),.084)
    fee,slip=(.01,.02) if cost=="example" else (0.,0.)
    return replay(c["mins"],c["mid"],half,*sg,c["calendar"].blocked,c["calendar"].deadline,
                  s["hold"],s["stop"] if stop is None else stop,s["tp"],10.,33.77,fee,slip)


def drawdown(e,start=100000.):
    eq=start+e;peak=np.maximum.accumulate(np.r_[start,eq])[1:];delta=peak-eq
    return float(delta.max()),float((delta/peak).max()*100)


def daily(c,e):
    day=c["mins"]//1440;end=np.r_[np.flatnonzero(day[1:]!=day[:-1]),len(day)-1]
    return np.diff(np.r_[0.,e[end]])


def overlap_count(ab_exposure,entry_indices):
    # Baseline gross exposure is the union, after same-minute exits/entries.
    return int((np.asarray(ab_exposure)[entry_indices]>0).sum())


def metrics(c,ab,result):
    t,e,x,opened=result;n=len(t);ei=t[:,1].astype(np.int64);xi=t[:,2].astype(np.int64)
    wins=float(t[t[:,5]>0,5].sum());loss=float(-t[t[:,5]<0,5].sum())
    count=overlap_count(ab.equity.gross_oz.to_numpy(),ei)
    dy=daily(c,e);std=dy.std(ddof=1)
    cut=int(np.searchsorted(c["mins"],int(np.datetime64("2014-01-01","m").astype(int))))
    recent=float(e[-1]-(e[cut-1] if cut else 0.))
    combined=ab.equity.equity.to_numpy()-100000.+e
    gap=np.r_[0,np.cumsum(np.diff(c["mins"])>30)]
    m=dict(net=float(e[-1]),closed_net=float(t[:,5].sum()),gross_wins=wins,gross_losses=loss,
           profit_factor=wins/loss if loss else None,trades=n,overlap_count=count,
           overlap=count/n if n else None,dd=drawdown(e)[0],dd_pct=drawdown(e)[1],
           lowest=float(min(100000.,(100000.+e).min())),net_2014_2016=recent,
           daily_t=float(dy.mean()/std*np.sqrt(len(dy))) if std else 0.,
           market_close_crossings=int((c["mins"][xi]>=c["calendar"].market_close[ei]).sum()),
           session_crossings=int((c["calendar"].session_day[xi]!=c["calendar"].session_day[ei]).sum()),
           late_cutoff_exits=int((c["mins"][xi]>c["calendar"].deadline[ei]).sum()),
           trades_spanning_data_gap=int((gap[xi]>gap[ei]).sum()),open_positions=int(opened!=0),
           combined_net=float(combined[-1]),combined_dd=drawdown(combined)[0],combined_dd_pct=drawdown(combined)[1],
           combined_lowest=float(min(100000.,(100000.+combined).min())),
           lot05=dict(net=float(5*e[-1]),dd=drawdown(5*e)[0],dd_pct=drawdown(5*e)[1],
                      lowest=float(min(100000.,(100000.+5*e).min())),
                      combined_net=float(5*combined[-1]),combined_dd=drawdown(5*combined)[0],
                      combined_dd_pct=drawdown(5*combined)[1],combined_lowest=float(min(100000.,(100000.+5*combined).min()))))
    if not opened:np.testing.assert_allclose(m["net"],m["closed_net"],atol=1e-6,rtol=1e-12)
    return m


def eligibility(m,train=True):
    tests=dict(net_positive=m["net"]>0,profit_factor_above_one=m["gross_wins"]>m["gross_losses"],
               natural_overlap=m["overlap"] is not None and m["overlap"]<=.30,
               minimum_trades=m["trades"]>=(50 if train else 20),
               recent_positive=(not train or m["net_2014_2016"]>0),
               example_cost_positive=m["example_net"]>0,
               no_close_crossings=m["market_close_crossings"]==0,no_session_crossings=m["session_crossings"]==0,
               no_terminal_position=m["open_positions"]==0)
    return dict(eligible=bool(all(tests.values())),checks=tests,failed=[k for k,val in tests.items() if not val])


def annual(c,result):
    t,e,_,_=result;out={};prev=0.
    year=pd.to_datetime(c["mins"],unit="m",utc=True).year.to_numpy()
    for y in np.unique(year):
        ix=np.flatnonzero(year==y);a=e[ix];p=np.maximum.accumulate(np.r_[prev,a])[1:]
        exit_year=year[t[:,2].astype(np.int64)]
        out[str(y)]=dict(net=float(a[-1]-prev),end_equity=float(100000.+a[-1]),dd=float((p-a).max()),trades=int((exit_year==y).sum()))
        prev=float(a[-1])
    return out


def night_regimes(c,result):
    """Descriptive only: before/after actual SHFE night-session introduction."""
    t=result[0]
    entry_dates=pd.to_datetime(c["mins"][t[:,1].astype(np.int64)],unit="m",utc=True).tz_convert("Asia/Shanghai")
    post=np.asarray(entry_dates>=pd.Timestamp("2013-07-05",tz="Asia/Shanghai"))
    return {name:dict(trades=int(mask.sum()),closed_net=float(t[mask,5].sum()))
            for name,mask in (("pre_2013_07_05_placebo",~post),("from_2013_07_05",post))}


def prefix_check(c,s,sg,r):
    # Prefix ends with a real open trade, exercising terminal non-liquidation.
    choices=np.flatnonzero(r[2]>0)
    if not len(choices):return dict(status="NO_OPEN_TRADE_AVAILABLE")
    n=int(choices[min(10,len(choices)-1)])+1
    cp=v.add_session(v.d.context(c["mins"][:n],c["bid"][:n],c["ask"][:n]))
    sp=hypothesis.signals(cp,s)
    for a,b in zip(sp,sg):np.testing.assert_array_equal(a,b[:n])
    rp=execute(cp,s,sp)
    np.testing.assert_array_equal(rp[1],r[1][:n])
    np.testing.assert_array_equal(rp[0],r[0][r[0][:,2]<n])
    return dict(status="PASS",quotes=n,open_at_cut=int(rp[3]!=0))


def study_rows(c,ab,specs,train):
    rows=[]
    for s in specs:
        sg=hypothesis.signals(c,s);r=execute(c,s,sg);m=metrics(c,ab,r)
        m["example_net"]=float(execute(c,s,sg,"example")[1][-1])
        m["historical_net"]=float(execute(c,s,sg,"historical")[1][-1])
        m.update(eligibility(m,train))
        stop=execute(c,s,sg,stop=3.);sensitivity=metrics(c,ab,stop)
        sensitivity["example_net"]=float(execute(c,s,sg,"example",stop=3.)[1][-1])
        sensitivity["historical_net"]=float(execute(c,s,sg,"historical",stop=3.)[1][-1])
        sensitivity.update(eligibility(sensitivity,train))
        prefix=prefix_check(c,s,sg,r)
        period="training" if train else "validation"
        np.savez_compressed(OUT/(s["id"]+"_"+period+".private.npz"),trades=r[0],equity_change=r[1],mins=c["mins"])
        row=dict(spec=s,metrics=m,yearly=annual(c,r),stop3_sensitivity=dict(metrics=sensitivity,yearly=annual(c,stop)),prefix_check=prefix)
        if s["family"]=="Ma_night_reversal_momentum":
            row["night_regimes_descriptive"]=night_regimes(c,r)
            row["stop3_sensitivity"]["night_regimes_descriptive"]=night_regimes(c,stop)
        rows.append(row);print(period,s["id"],json.dumps(m),flush=True)
    return rows


def design():
    OUT.mkdir(exist_ok=True)
    if (OUT/"LOCK.json").exists():raise FileExistsError("already locked; no retuning")
    if "FINAL FROZEN PROTOCOL" not in (ROOT/"PLAN.md").read_text(encoding="utf-8"):
        raise ValueError("paper hypotheses and protocol not finalized")
    before=source_hashes();data=v.d.data_hashes(list(range(2010,2017)));guards()
    write(OUT/"RUN_INPUTS.json",dict(sources=before,data_hashes=data))
    specs=hypothesis.candidates();assert 1<=len(specs)<=2
    write(OUT/"CANDIDATES.json",specs)
    c,ab=load(list(range(2010,2017)),"design");rows=study_rows(c,ab,specs,True)
    assert source_hashes()==before;v.d.study.verify_hashes(data)
    selected=[r["spec"] for r in rows if r["metrics"]["eligible"]]
    write(OUT/"TRAINING.json",dict(rows=rows,ab_metrics=v.d.metrics(ab),years_read=list(range(2010,2017))))
    lock=dict(locked_utc=datetime.now(timezone.utc).isoformat(),sources=before,selected=selected,
              all_primary_specs=specs,training_data_hashes=data,baseline_lock_sha256=sha(v.OUT/"LOCK.json"),
              sensitivity_policy="fixed3vol stop reported; never replacement selection",market_years_read=list(range(2010,2017)))
    write(OUT/"LOCK.json",lock);(OUT/"LOCK.sha256").write_text(sha(OUT/"LOCK.json"),encoding="ascii")
    print("LOCKED",json.dumps(selected),flush=True)


def evaluate():
    lock=json.loads((OUT/"LOCK.json").read_text(encoding="utf-8"))
    assert sha(OUT/"LOCK.json")== (OUT/"LOCK.sha256").read_text().strip()
    assert source_hashes()==lock["sources"];guards();v.d.study.verify_hashes(lock["training_data_hashes"])
    if (OUT/"VALIDATION.json").exists():raise FileExistsError("already evaluated")
    if not lock["selected"]:
        write(OUT/"VALIDATION.json",dict(status="NO_TRAINING_CANDIDATE",rows=[],years_read=[]));return
    data=v.d.data_hashes([2017,2018,2019]);c,ab=load([2017,2018,2019],"evaluate")
    rows=study_rows(c,ab,lock["selected"],False)
    assert source_hashes()==lock["sources"];v.d.study.verify_hashes(data)
    write(OUT/"VALIDATION.json",dict(status="EXPLORATORY_PASS" if any(r["metrics"]["eligible"] for r in rows) else "NOT_CONFIRMED",
                                   rows=rows,ab_metrics=v.d.metrics(ab),data_hashes=data,years_read=[2017,2018,2019]))


if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("phase",choices=["design","evaluate"])
    a=ap.parse_args();{"design":design,"evaluate":evaluate}[a.phase]()
