"""Synthetic-only verification. No market files, loaders, or strategy outcomes."""
from types import SimpleNamespace
import unittest
import numpy as np
import pandas as pd
import signals
import trial


def context(date="2015-03-09",direction=1):
    t=pd.date_range(date+" 11:00",date+" 16:10",freq="min",tz="America/New_York")
    mins=t.tz_convert("UTC").asi8//60_000_000_000
    mid=np.full(len(t),1200.);mid[t.hour>=12]+=direction
    day=np.full(len(t),1,np.int64)
    return dict(mins=mins,mid=mid,bid=mid-.1,ask=mid+.1,eff=np.full(len(t),10.),
                calendar=SimpleNamespace(session_day=day,blocked=np.zeros(len(t),bool),deadline=np.full(len(t),mins[-1]+100)))


class Synthetic(unittest.TestCase):
    def test_exact_signal_and_both_directions(self):
        s=signals.candidates()[0]
        for d in (1,-1):
            c=context(direction=d);sg,scale=signals.signals(c,s)
            i=np.flatnonzero(sg);self.assertEqual(len(i),1)
            ny=pd.to_datetime(c["mins"][i[0]],unit="m",utc=True).tz_convert("America/New_York")
            self.assertEqual((ny.hour,ny.minute),(15,29));self.assertEqual(sg[i[0]],d)
            self.assertGreater(scale[i[0]],0)

    def test_dst_same_local_entry(self):
        s=signals.candidates()[0];utc=[]
        for date in ("2015-03-06","2015-03-09","2015-11-02"):
            c=context(date);sg,_=signals.signals(c,s);i=np.flatnonzero(sg)[0]
            utc.append(pd.to_datetime(c["mins"][i],unit="m",utc=True).hour)
        self.assertEqual(utc,[20,19,20])

    def test_missing_anchor_or_window_gap_rejects(self):
        s=signals.candidates()[0]
        for cut in (30,45,60):
            c=context();keep=np.arange(len(c["mins"]))!=cut
            for k in ("mins","mid","bid","ask","eff"):c[k]=c[k][keep]
            c["calendar"].session_day=c["calendar"].session_day[keep]
            self.assertFalse(signals.signals(c,s)[0].any())

    def test_causal_prefix_and_future_changes(self):
        c=context();s=signals.candidates()[0];full=signals.signals(c,s)
        n=271;short={k:val[:n] if isinstance(val,np.ndarray) else val for k,val in c.items()}
        short["calendar"]=SimpleNamespace(session_day=c["calendar"].session_day[:n])
        for a,b in zip(signals.signals(short,s),full):np.testing.assert_array_equal(a,b[:n])
        c["mid"][271:]+=9999
        for a,b in zip(signals.signals(c,s),full):np.testing.assert_array_equal(a[:n],b[:n])

    def test_timed_fill_and_costs(self):
        c=context();s=signals.candidates()[0];sg=signals.signals(c,s)
        r=trial.execute(c,s,sg);t=r[0];self.assertEqual(len(t),1)
        self.assertEqual(c["mins"][int(t[0,1])]-c["mins"][int(t[0,0])],1)
        self.assertEqual(c["mins"][int(t[0,2])]-c["mins"][int(t[0,1])],30)
        self.assertAlmostEqual(t[0,5],-.168*337.7,places=7)
        ex=trial.execute(c,s,sg,"example")
        self.assertAlmostEqual(ex[0][0,5],-(.168+.04+.02)*337.7,places=7)
        self.assertEqual(r[3],0)

    def test_union_and_simultaneous_overlap(self):
        # 20oz still counts once; zero means same-minute baseline exit already done.
        self.assertEqual(trial.overlap_count([0,10,20,0],np.array([1,2,3])),2)

    def test_night_partial_retrace_original_direction(self):
        s=signals.candidates()[1]
        for direction in (1,-1):
            t=pd.date_range("2015-03-09 21:00","2015-03-09 23:10",freq="min",tz="Asia/Shanghai")
            mins=t.tz_convert("UTC").asi8//60_000_000_000
            mid=np.r_[np.linspace(1200,1200+2*direction,31),np.linspace(1200+2*direction,1200+direction,31)[1:],np.full(70,1200+direction)]
            n=len(t);c=dict(mins=mins,mid=mid,bid=mid-.1,ask=mid+.1,eff=np.full(n,10.),calendar=SimpleNamespace(session_day=np.ones(n),blocked=np.zeros(n,bool),deadline=np.full(n,mins[-1]+100)))
            sg=signals.signals(c,s);ix=np.flatnonzero(sg[0]);self.assertEqual(ix.tolist(),[60]);self.assertEqual(sg[0][60],direction)
            r=trial.execute(c,s,sg);self.assertEqual(r[0][0,1],61);self.assertEqual(r[0][0,2],120)
            for value in (1200-2*direction,1200+3*direction,1200+2*direction):
                c["mid"][60]=value
                self.assertFalse(signals.signals(c,s)[0].any())

    def test_year_guard_before_loading(self):
        for years,phase in (([2020],"evaluate"),([2017],"design"),([2017,2018,2019,2020],"evaluate")):
            with self.assertRaises(ValueError):trial.permitted(years,phase)


if __name__=="__main__":unittest.main()
