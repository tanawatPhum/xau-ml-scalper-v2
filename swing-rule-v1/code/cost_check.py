"""Owner question 13:49: is the spread right? Independent re-check for rule A (k 1 V2), 2017-2019.
1) cost constant; 2) every trade recomputed from BID/ASK closes the way a broker fills
(sell at bid, buy at ask), with the owner's spread instead of Dukascopy's; 3) one worked trade;
4) do trades cross the daily break (rollover / swap)?"""
import numpy as np

import variants as V

P = 4083.276
print(f"\nCOST_BPS {V.COST_BPS:.4f} bps = ${V.COST_BPS * V.U:.4f} per oz per round trip "
      f"= ${V.COST_BPS * V.U * 10:.2f} per 0.1 lot")

tot_g, tot_n, tot_b, cnt, blockend = 0.0, 0.0, 0.0, 0, 0
gaps_per_day = []
example = None
for yr in (2017, 2018, 2019):
    y, mins, blk = V.data[yr]
    s60 = V.sigma60(y, blk)
    sl = V.sigma_long(y, blk)
    seff = np.where(np.isfinite(sl), np.fmax(s60, sl), s60)
    T = 1.0 * seff
    idx, d, ext, exi, th = V.zigzag_x(y, blk, T)
    n = len(y)
    eb = blk[idx]
    same_prev = np.r_[False, eb[1:] == eb[:-1]]
    B = np.full(len(idx), np.nan)
    B[1:] = d[1:] * (ext[:-1] - ext[1:])
    last_of_blk = np.r_[np.flatnonzero(np.diff(blk)), n - 1]
    same_next = np.r_[eb[1:] == eb[:-1], False]
    exit_i = np.where(same_next, np.r_[idx[1:], -1], last_of_blk[eb])
    ent = np.minimum(idx + 1, n - 1)
    ok = (blk[ent] == eb) & same_prev & (B / th >= 2.5)
    ex = np.minimum(exit_i + 1, n - 1)
    ex = np.where(blk[ex] == eb, ex, exit_i)
    ok &= ex > ent
    sgn = -d.astype(np.float64)
    out_i, stopped = V.apply_stop(y, ent[ok], ex[ok], sgn[ok], 3.0 * T[idx][ok])
    e, sg = ent[ok], sgn[ok]
    mid_gross_usd = sg * (y[out_i] - y[e]) * V.U          # study method, today's $
    net_study = mid_gross_usd - 0.168
    # broker-style fill on the actual mid prices of that day, owner's spread 0.168 at today's price
    mid = np.exp(y / 1e4)                                   # actual historical mid price
    half = 0.084 * mid / P                                  # owner's half-spread scaled to that price
    fill_in = np.where(sg < 0, mid[e] - half[e], mid[e] + half[e])          # sell at bid / buy at ask
    fill_out = np.where(sg < 0, mid[out_i] + half[out_i], mid[out_i] - half[out_i])
    broker_usd_hist = sg * (fill_out - fill_in)             # in that day's dollars
    broker_usd_today = broker_usd_hist * P / mid[e]          # same move expressed at today's price
    tot_g += mid_gross_usd.sum()
    tot_n += net_study.sum()
    tot_b += broker_usd_today.sum()
    cnt += len(e)
    blockend += int(np.sum(~same_next[ok] & (stopped == 0)))
    if example is None:
        k = int(np.argmax(np.abs(net_study) > 0))
        example = (yr, mins[e[k]], sg[k], mid[e[k]], mid[out_i[k]], fill_in[k], fill_out[k],
                   broker_usd_hist[k], broker_usd_today[k], net_study[k])
    t = (mins.astype(np.int64) * 60).astype("datetime64[s]")
    gap = np.diff(mins) > 30
    days = np.unique(t.astype("datetime64[D]"))
    gaps_per_day.append(gap.sum() / len(days))

print(f"rule A 2017-19 trades {cnt}: mean gross ${tot_g / cnt:+.4f}, study net ${tot_n / cnt:+.4f} "
      f"(difference ${(tot_n - tot_g) / cnt:+.4f} per trade), broker-style bid/ask net ${tot_b / cnt:+.4f}")
yr, m0, sg, me, mx, fi, fo, bh, bt, ns = example
print(f"example trade {np.datetime64(int(m0) * 60, 's')} side {'SELL' if sg < 0 else 'BUY'}: mid in {me:.3f} out {mx:.3f}; "
      f"fill in {fi:.3f} out {fo:.3f}; P&L that day ${bh:+.3f}/oz = ${bt:+.3f}/oz at today's price; study net ${ns:+.3f}")
print(f"trades closed by the block end (daily break / weekend) without a stop: {blockend} ({100 * blockend / cnt:.1f}%)")
print(f"gaps > 30 min per calendar day in the data: {np.round(gaps_per_day, 2)} (daily break splits blocks -> "
      f"no position is held through the break)")
