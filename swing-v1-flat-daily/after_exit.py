"""Owner 22:17: are the losers really the wrong direction, or stopped out and then price went our way anyway?
Exness version (EX). For every losing trade, follow the price AFTER the exit until the next daily cutoff (16:55 NY):
 - back to entry: price returns to the entry price (break-even before spread)
 - reaches a win: price goes 1 theta in the trade's favour from the entry (a typical winner's size)
 - further against: price goes 1 more theta against the trade beyond the exit price before returning to entry
Also the no-stop counterfactual for stopped trades: hold to the rule's next swing exit or the daily cutoff."""
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "swing-causal-execution"))
import engine as E  # noqa: E402
from run import DEFAULT_CACHE, load_prices  # noqa: E402

mins, bid, ask = load_prices(DEFAULT_CACHE, list(range(2010, 2023)), allow_2020_2022=True)
mid = (bid + ask) / 2
ny = pd.to_datetime(mins * 60, unit="s", utc=True).tz_convert("America/New_York")
mod = (ny.hour * 60 + ny.minute).to_numpy()
blocked = (mod >= 16 * 60 + 55) & (mod < 18 * 60 + 1)
gap_next = np.r_[np.diff(mins) > 30, True]
nxt_gap = pd.Series(np.where(gap_next, mins, np.nan)).bfill().to_numpy()
blocked |= (nxt_gap - mins) <= 4
cut_idx = np.where(blocked, np.arange(len(mins)), len(mins) - 1)
cut_idx = np.minimum.accumulate(cut_idx[::-1])[::-1]  # next blocked index at or after i
events = E.make_signals(mins, bid, ask)
ev_idx = {r: np.asarray(e[:, 0], np.int64) for r, e in events.items()}

T = pd.read_csv(HERE / "out" / "TRADES_EX.private.csv")
T["ie"] = np.searchsorted(mins, T.t_entry.to_numpy())
T["ix"] = np.searchsorted(mins, T.t_exit.to_numpy())
T["theta_usd"] = T.theta_bps * T.entry_mid / 1e4
L = T[T.net_thb <= 0].copy()


@nb.njit(cache=True)
def follow(mid, ie, ix, side, entry, th, cut):
    n = len(ie)
    back = np.zeros(n, np.int8)
    win = np.zeros(n, np.int8)
    further = np.zeros(n, np.int8)
    first_back = np.zeros(n, np.int8)
    for k in range(n):
        x = ix[k]
        lvl_exit = side[k] * (mid[x] - entry[k])
        done_far = False
        for t in range(x + 1, cut[x] + 1):
            m = side[k] * (mid[t] - entry[k])
            if not done_far and m <= lvl_exit - th[k]:
                further[k] = 1
                done_far = True
            if m >= 0 and back[k] == 0:
                back[k] = 1
                if not done_far:
                    first_back[k] = 1
            if m >= th[k]:
                win[k] = 1
                break
    return back, win, further, first_back


back, win, further, first_back = follow(mid, L.ix.to_numpy(), L.ie.to_numpy() * 0 + L.ix.to_numpy(), L.side.to_numpy().astype(float),
                                        L.entry_mid.to_numpy(), L.theta_usd.to_numpy(), cut_idx) if False else \
    follow(mid, L.ie.to_numpy(), L.ix.to_numpy(), L.side.to_numpy().astype(float), L.entry_mid.to_numpy(), L.theta_usd.to_numpy(), cut_idx)
L["back"], L["win_after"], L["further"], L["back_first"] = back, win, further, first_back

# no-stop counterfactual for stopped losers: exit at the minute after the rule's next swing, or at the daily cutoff
S = L[L.exit_reason == "stop"].copy()
cf = []
for r, g in S.groupby("rule"):
    e = ev_idx[r]
    for i, (ie, s, em) in zip(g.index, g[["ie", "side", "entry_mid"]].to_numpy()):
        ie = int(ie)
        j = np.searchsorted(e, ie, side="right")
        sw = e[j] + 1 if j < len(e) else len(mid) - 1
        x = min(sw, cut_idx[ie])
        cf.append((i, s * (mid[x] - em) - 0.168))
cf = pd.Series(dict(cf))
S["cf_net_thb"] = cf.reindex(S.index) * 10 * 33.77

pd.set_option("display.width", 250)
print(f"losers {len(L)}; after the exit, until the next daily cutoff (16:55 NY):")
for name, g in [("all losers", L)] + [(k, v) for k, v in L.groupby("exit_reason")]:
    print(f"  {name:10s} n {len(g):5d} | back to entry {g.back.mean():5.1%} | reaches a 1-theta win {g.win_after.mean():5.1%} | "
          f"goes 1 more theta against first {(g.further == 1).mean() - ((g.further == 1) & (g.back_first == 1)).mean():5.1%} | "
          f"neither {(1 - g.back.clip(0, 1) - ((g.further == 1) & (g.back == 0))).mean():5.1%}")
print("\nstopped losers, no-stop counterfactual (hold to the next swing exit or the daily cutoff):")
print(f"  actual {S.net_thb.sum():,.0f} THB | without the stop {S.cf_net_thb.sum():,.0f} THB | would have ended positive {(S.cf_net_thb > 0).mean():.1%} | "
      f"would have lost more {(S.cf_net_thb < S.net_thb).mean():.1%}")
print(f"  of the stopped trades that lose more without the stop: extra loss {(S.cf_net_thb - S.net_thb)[S.cf_net_thb < S.net_thb].sum():,.0f} THB; "
      f"of those that do better: saved {(S.cf_net_thb - S.net_thb)[S.cf_net_thb >= S.net_thb].sum():,.0f} THB")
print(f"  worst counterfactual trade {S.cf_net_thb.min():,.0f} THB (actual worst {S.net_thb.min():,.0f})")
L[["rule", "exit_reason", "net_thb", "back", "win_after", "further", "back_first"]].to_csv(HERE / "out" / "LOSERS_AFTER_EXIT.private.csv")
