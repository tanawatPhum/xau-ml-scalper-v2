"""Where are the market breaks in the data? Gaps > 30 minutes, start/end in New York local time (DST-aware), 2010-2022."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "swing-causal-execution"))
from run import DEFAULT_CACHE, load_prices  # noqa: E402

mins, bid, ask = load_prices(DEFAULT_CACHE, list(range(2010, 2023)), allow_2020_2022=True)
g = np.flatnonzero(np.diff(mins) > 30)
last = pd.to_datetime(mins[g] * 60, unit="s", utc=True).tz_convert("America/New_York")
nxt = pd.to_datetime(mins[g + 1] * 60, unit="s", utc=True).tz_convert("America/New_York")
G = pd.DataFrame(dict(last_ny=last, next_ny=nxt, minutes=(mins[g + 1] - mins[g])))
G["last_hhmm"] = G["last_ny"].dt.strftime("%H:%M")
G["next_hhmm"] = G["next_ny"].dt.strftime("%H:%M")
G["kind"] = np.where(G["minutes"] > 1440, "weekend/holiday", "daily")
print("gaps:", len(G))
print("last quote before the gap (NY time), top 10:")
print(G["last_hhmm"].value_counts().head(10).to_string())
print("first quote after the gap (NY time), top 10:")
print(G["next_hhmm"].value_counts().head(10).to_string())
odd = G[~G["last_hhmm"].isin(["16:59", "16:58", "16:57"])]
print(f"\ngaps NOT starting at about 17:00 NY: {len(odd)}")
print(odd.assign(last=odd.last_ny.dt.strftime("%Y-%m-%d %a %H:%M"), next=odd.next_ny.dt.strftime("%Y-%m-%d %a %H:%M"))[
    ["last", "next", "minutes"]].to_string(index=False))
G.to_csv(Path(__file__).resolve().parent / "out" / "GAPS.csv", index=False)
