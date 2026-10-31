"""Build swing events (real), sign-flip null summaries and the synthetic self-test."""

import json

import numpy as np

from swing import CACHE, OUT, THETA_BPS, THETA_USD, YEARS, load_series, ny_clock, process, signflip

NDRAW = 5


def summarize(ev, yr):
    v = ev["code"] >= 0
    out = {}
    for c in range(8):
        m = v & (ev["code"] == c)
        out[c] = dict(n=int(m.sum()), r1=float(ev["r1"][m].sum()), r3=float(ev["r3"][m].sum()),
                      r1sq=float((ev["r1"][m] ** 2).sum()), r3sq=float((ev["r3"][m] ** 2).sum()))
    out["all_n"] = int(len(ev["code"]))
    out["yr"] = yr
    return out


def main():
    rng = np.random.default_rng(20261031)
    # synthetic self-test: Gaussian random walk on the 2017 calendar
    y, mins, blk = load_series(2017)
    sd = float(np.std(np.diff(y)[blk[1:] == blk[:-1]]))
    same = np.r_[False, blk[1:] == blk[:-1]]
    steps = np.where(same, rng.normal(0, sd, len(y)), 0.0)
    cs = np.cumsum(steps)
    first = np.r_[0, np.flatnonzero(np.diff(blk)) + 1]
    ysyn = 5000 + cs - cs[first[blk]]
    synth = {}
    for tu, th in zip(THETA_USD, THETA_BPS, strict=True):
        ev = process(ysyn, mins, blk, th)
        synth[tu] = summarize(ev, 2017)
        print("synthetic theta $", tu, "events", len(ev["code"]), flush=True)
    with open(OUT / "SYNTH.json", "w", encoding="utf-8") as f:
        json.dump(synth, f, indent=1)

    nulls = {tu: [] for tu in THETA_USD}
    for tu, th in zip(THETA_USD, THETA_BPS, strict=True):
        parts = []
        for yr in YEARS:
            y, mins, blk = load_series(yr)
            ev = process(y, mins, blk, th)
            ev["yr"] = np.full(len(ev["code"]), yr)
            ev["day"] = ev["mins"] // 1440
            ev["nyh"], ev["nymin"] = ny_clock(ev["mins"])
            parts.append(ev)
            for _ in range(NDRAW):
                evn = process(signflip(y, blk, rng), mins, blk, th)
                nulls[tu].append(summarize(evn, yr))
        out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
        np.savez_compressed(CACHE / f"EVENTS_theta{tu}.private.npz", **out)
        print(f"theta ${tu} ({th:.3f} bps): events {len(out['code'])}, with pattern "
              f"{int((out['code'] >= 0).sum())}", flush=True)
    with open(OUT / "NULL_SIGNFLIP.json", "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in nulls.items()}, f)


if __name__ == "__main__":
    main()
