import sys,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
sp=importlib.util.spec_from_file_location('practical_parent',PARENT/'study.py')
p=importlib.util.module_from_spec(sp);sys.modules['practical_parent']=p;sp.loader.exec_module(p)
def candidates():
    return [dict(id=f'long_w{w}_k{k}_h{h}_tp{tp}',family='price_path',params=dict(w=w,k=k,d=1),hold=h,stop=1.,tp=float(tp))
            for w in (15,30,60) for k in (1,2) for h in (180,360) for tp in (2,4)]
def sources():
    files=[HERE/'PLAN.md',HERE/'longer.py',PARENT/'PLAN.md',PARENT/'study.py',PARENT/'out/LOCK.json']
    files += [PARENT.parent/'rule-c-research-20261101'/f for f in ('research_study.py','replay.py')]
    return {str(f):p.s.sha(f) for f in files}
if __name__=='__main__':
    p.tests();s=p.s;s.ROOT=HERE;s.OUT=HERE/'out';s.sources=sources;s.signals=p.signals;s.metrics=p.metrics;s.execute=p.execute;s.eligible=p.eligible
    s.reclaim.candidates=candidates;s.structure.candidates=lambda:[]
    {'design':s.design,'evaluate':s.evaluate}[sys.argv[1]]()
