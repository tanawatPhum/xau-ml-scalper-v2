"""One bounded training-only follow-up; original research and versions unchanged."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
import research_study as s
original_signals=s.signals
original_reclaim=s.reclaim.candidates
original_structure=s.structure.candidates
def flipped(c,spec):
    a,b=original_signals(c,spec)
    return -a,b
def renamed(fn):
    return [{**x,'id':'opposite_'+x['id']} for x in fn()]
def sources():
    files=[PARENT/x for x in ('PLAN.md','replay.py','reclaim.py','structure.py','research_study.py','out/LOCK.json')]
    files += [HERE/'PLAN.md',HERE/'opposite.py']
    return {str(p):s.sha(p) for p in files}
if __name__=='__main__':
    s.ROOT=HERE;s.OUT=HERE/'out';s.sources=sources;s.signals=flipped
    s.reclaim.candidates=lambda:renamed(original_reclaim)
    s.structure.candidates=lambda:renamed(original_structure)
    {'design':s.design,'evaluate':s.evaluate}[sys.argv[1]]()
