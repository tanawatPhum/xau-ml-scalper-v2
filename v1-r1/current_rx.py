"""Compatibility entrypoint for the former v1-rx name; delegates to v1-r1."""
import json
from v1_r1 import ROOT,VERSION,parameters,simulate


if __name__=='__main__':
    print('Version:',VERSION)
    print(json.dumps(parameters(),indent=2))
    print('2010-2022 report:',ROOT/'daily/RESULTS_2010_2022_LOT05.md')
