"""Descriptive, 2010-16 only: per-year THB of the slower-scale fade cells (the near misses). 2017-19 not read."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = pd.read_pickle(ROOT / "out" / "C_TRADES.private.pkl")
D = D[(D["yr"] <= 2016) & D["cell"].str.startswith(("CS_", "v1_"))]
print(D.pivot_table(index="yr", columns="cell", values="net_thb", aggfunc="sum").round(0).to_string())
print(D.pivot_table(index="yr", columns="cell", values="net_thb", aggfunc="size").to_string())
