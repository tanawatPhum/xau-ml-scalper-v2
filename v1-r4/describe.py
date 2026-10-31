"""v1-r4 descriptive follow-up after the design lock came out NOT_CONFIRMED (no candidate met all four limits).
Fixed lots only: a fixed lot L is an exact linear scaling of v1-r2 at 0.1 lot, whose 2017-22 path is already known,
so nothing here reads or selects any of the Z1-Z4 rules on 2017+.  python -B v1-r4/describe.py"""
import json
import math
import sys
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import v1_r4 as v4  # noqa: E402

OUT = v4.OUT
START, SEED = v4.START, v4.SEED
LOTS = (.1, .2, .3, .4, .5)
NY = "America/New_York"


@nb.njit(cache=True)
def boot_thb(dp, n_paths, block, seed, x, cap):
    """Stationary bootstrap of daily THB P&L (fixed lot, no compounding). Returns per-path capital needed for max DD <= x,
    per-path max DD% at capital cap, and per-path lowest equity at cap."""
    np.random.seed(seed)
    n = len(dp)
    need = np.empty(n_paths)
    ddc = np.empty(n_paths)
    low = np.empty(n_paths)
    for q in range(n_paths):
        idx = np.random.randint(n)
        p, mx, nd, dd, lo = 0., 0., 0., 0., 0.
        for t in range(n):
            if t > 0:
                if np.random.random() < 1. / block:
                    idx = np.random.randint(n)
                else:
                    idx = (idx + 1) % n
            p += dp[idx]
            if p > mx:
                mx = p
            v = (mx - p) / x - mx
            if v > nd:
                nd = v
            z = (mx - p) / (cap + mx)
            if z > dd:
                dd = z
            if p < lo:
                lo = p
        need[q], ddc[q], low[q] = nd, dd, cap + lo
    return need, ddc, low


def up(v):
    return int(math.ceil(v / 1000.) * 1000)


def ny_day(mins):
    return (pd.to_datetime(np.asarray(mins) * 60, unit="s", utc=True).tz_convert(NY) + pd.Timedelta(hours=6)).date


def fixed_table(c, t01, eq01):
    e01 = v4.daily_equity(c, eq01)
    d01 = np.diff(e01)
    loss01 = (-t01.net_thb).to_numpy()
    pe01 = (t01.eq_at_entry - START).to_numpy()
    rows = []
    for L in LOTS:
        s = L / .1
        eq = START + (eq01 - START) * s
        dd, ddp = v4.drawdown(eq)
        dstart = START + (e01[:-1] - START) * s
        need_b, ddc, low_b = boot_thb(d01 * s, 2000, 5.0, SEED, .30, START)
        p = np.r_[0., eq01 - START] * s
        mx = np.maximum.accumulate(p)
        cap_hist = ((mx - p) / .20 - mx).max()
        cap_worst_hist = (loss01 * s / .06 - pe01 * s).max()
        cap_worst_day1 = loss01.max() * s / .06
        rows.append(dict(
            lot=L, net=float(eq[-1] - START), dd=dd, dd_pct=ddp, lowest=float(eq.min()),
            worst_trade=float(-loss01.max() * s), worst_trade_pct=float((loss01 * s / (START + pe01 * s)).max() * 100),
            worst_day=float((d01 * s).min()), worst_day_pct=float((-(d01 * s) / dstart).max() * 100),
            boot_thb_dd50=float(np.percentile(ddc, 50) * 100), boot_thb_dd95=float(np.percentile(ddc, 95) * 100),
            boot_thb_p_dd_gt_30=float((ddc > .30).mean()), boot_thb_p_low_lt_80k=float((low_b < 80_000).mean()),
            cap_hist_dd20=up(cap_hist), cap_boot95_dd30=up(np.percentile(need_b, 95)),
            cap_worst6_hist=up(cap_worst_hist), cap_worst6_day1=up(cap_worst_day1)))
    return rows


def worst_trades(c, t01, n=12):
    t = t01.copy()
    tu = t.theta_bps / 1e4 * t.entry_mid
    t["theta_usd"] = tu
    t["adverse_usd"] = -t.side * (t.exit_mid - t.entry_mid)
    t["loss_in_theta"] = t.adverse_usd / tu
    t["ny_entry"] = pd.to_datetime(t.t_entry * 60, unit="s", utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d %H:%M")
    t["hold_min"] = t.t_exit - t.t_entry
    t["reason"] = t.reason_code.map({1: "swing", 2: "stop", 3: "data_gap", 4: "scheduled"})
    cols = ["ny_entry", "rule", "side", "theta_usd", "adverse_usd", "loss_in_theta", "reason", "hold_min", "exit_delay_minutes", "net_thb", "eq_at_entry"]
    w = t.nsmallest(n, "net_thb")[cols]
    stops = t[t.reason_code == 2]
    tail = dict(trades=int(len(t)), stops=int(len(stops)), stop_share=float(len(stops) / len(t)),
                stop_mean_loss_theta=float(stops.loss_in_theta.mean()), stop_p90_loss_theta=float(stops.loss_in_theta.quantile(.9)),
                stop_beyond_3theta=int((stops.loss_in_theta > 3).sum()), stop_beyond_4theta=int((stops.loss_in_theta > 4).sum()),
                theta_usd_p50=float(tu.median()), theta_usd_p90=float(tu.quantile(.9)), theta_usd_max=float(tu.max()),
                planned_stop_thb_01_p50=float((2.5 * tu * 100 * v4.FX * .1).median()),
                planned_stop_thb_01_p90=float((2.5 * tu * 100 * v4.FX * .1).quantile(.9)),
                planned_stop_thb_01_max=float((2.5 * tu * 100 * v4.FX * .1).max()))
    by_year = t.groupby(pd.to_datetime(t.t_exit * 60, unit="s").dt.year).agg(
        worst=("net_thb", "min"), theta_usd_med=("theta_usd", "median"), theta_usd_max=("theta_usd", "max"),
        stop_n=("reason_code", lambda r: int((r == 2).sum())))
    return w, tail, by_year


def main():
    v4.read_lock()
    l2 = v4.lock2_info()
    out = {}
    for label, years, phase in (("2010_2016", list(range(2010, 2017)), "design"), ("2010_2019", list(range(2010, 2020)), "evaluate"),
                                ("2010_2022", list(range(2010, 2023)), "extend")):
        c = v4.context(years, phase)
        st = v4.streams(c, l2)
        t01, eq01 = v4.run_sized(c, st, "Z0", dict(lot=.1), l2["base"]["stop_theta"])
        rows = fixed_table(c, t01, eq01)
        w, tail, by_year = worst_trades(c, t01)
        yr = v4.yearly(c, t01, eq01, years)
        out[label] = dict(fixed_lots=rows, tail=tail, worst_by_year={int(k): v for k, v in by_year.to_dict("index").items()}, yearly_01=yr)
        w.to_csv(OUT / f"WORST_TRADES_{label}.private.csv", index=False)
        print("==", label, "net@0.1", round(eq01[-1] - START), "trades", len(t01), flush=True)
        for r in rows:
            print(f"  lot {r['lot']:.1f} net {r['net']:,.0f} dd {r['dd']:,.0f} ({r['dd_pct']:.1f}%) worst {r['worst_trade']:,.0f} ({r['worst_trade_pct']:.1f}%)"
                  f" worstday {r['worst_day']:,.0f} ({r['worst_day_pct']:.1f}%) bootTHB95 {r['boot_thb_dd95']:.1f}% P(dd>30) {r['boot_thb_p_dd_gt_30']:.2f}"
                  f" | cap dd20 {r['cap_hist_dd20']:,} boot30 {r['cap_boot95_dd30']:,} worst6 {r['cap_worst6_hist']:,} worst6@day1 {r['cap_worst6_day1']:,}",
                  flush=True)
        print("  tail", json.dumps({k: round(v, 2) for k, v in tail.items()}), flush=True)
        print(w.to_string(index=False, float_format=lambda x: f"{x:,.2f}"), flush=True)
        print(by_year.to_string(float_format=lambda x: f"{x:,.1f}"), flush=True)
    v4.write_json(OUT / "DESCRIBE_FIXED_LOTS.json", out)


if __name__ == "__main__":
    main()
