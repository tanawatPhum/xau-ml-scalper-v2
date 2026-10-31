"""Post-outcome descriptions requested by reviewer; no candidate/lock modifications."""
from run import *

def describe():
    lock=json.loads((OUT/'LOCK.json').read_text(encoding='utf-8'));verify_sources(lock['sources'])
    v.d.study.verify_hashes(lock['training_data_hashes'])
    result={}
    for name,years,phase in [('TRAINING',list(range(2010,2017)),'training'),('VALIDATION',[2017,2018,2019],'validation')]:
        doc=json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'))
        if name=='VALIDATION':v.d.study.verify_hashes(doc['data_hashes'])
        z=np.load(OUT/(name+'.private.npz'));mins=z['mins'];t=z['trades'];e=z['equity_change'];abe=z['ab_equity']-100000.
        c=load(years,phase);ab,_=baseline(c,name=='TRAINING');np.testing.assert_array_equal(c['mins'],mins)
        np.testing.assert_array_equal(ab.equity.equity.to_numpy()-100000.,abe)
        ei=t[:,1].astype(np.int64);xi=t[:,2].astype(np.int64)
        ny=pd.to_datetime(mins[ei],unit='m',utc=True).tz_convert('America/New_York')
        winter=np.array([x.utcoffset().total_seconds()==-18000 for x in ny]);over=ab.equity.gross_oz.to_numpy()[ei]>0
        seasons={}
        for label,mask in [('winter_UTC_minus5',winter),('summer_UTC_minus4',~winter)]:
            seasons[label]=dict(trades=int(mask.sum()),net=float(t[mask,5].sum()),overlap_count=int(over[mask].sum()),
                overlap=float(over[mask].mean()) if mask.any() else None,median_hold_minutes=float(np.median(mins[xi[mask]]-mins[ei[mask]])) if mask.any() else None)
        annual={};yy=pd.to_datetime(mins,unit='m',utc=True).year.to_numpy();previousC=previousAB=0.
        for y in np.unique(yy):
            a=np.flatnonzero(yy==y);end=int(a[-1]);annual[str(y)]=dict(C=float(e[end]-previousC),AB=float(abe[end]-previousAB),ABC=float(e[end]+abe[end]-previousC-previousAB))
            previousC=float(e[end]);previousAB=float(abe[end])
        lot05={}
        for label,path in [('C',e),('AB',abe),('ABC',abe+e)]:
            dd,ddpct=old.drawdown(5*path)
            lot05[label]=dict(net=float(5*path[-1]),dd=dd,dd_pct=ddpct,lowest=float(min(100000.,(100000.+5*path).min())))
        result[name]=dict(seasons=seasons,annual=annual,lot05=lot05)
        if name=='VALIDATION':v.d.study.verify_hashes(doc['data_hashes'])
    verify_sources(lock['sources']);v.d.study.verify_hashes(lock['training_data_hashes'])
    write(OUT/'DESCRIPTIVE.json',dict(post_outcome=True,selection_impact='none',results=result,script_sha256=sha(__file__)))
    print(json.dumps(result,indent=2))
if __name__=='__main__':describe()
