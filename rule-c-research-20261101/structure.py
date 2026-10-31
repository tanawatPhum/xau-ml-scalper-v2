"""Independent, causal structural Rule C research signals.

Run this file directly for synthetic-only checks. No market files are read.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def candidates():
    """Return a fixed, outcome-independent 16-candidate research grid."""
    specs = []
    for family, windows, thresholds, code in (
        ("mean_deviation_reversal", (60, 240), (1.5, 2.5), "mean"),
        ("compression_breakout", (30, 60), (1., 1.5), "compress"),
    ):
        for window in windows:
            for threshold in thresholds:
                for hold in (30, 90):
                    specs.append({
                        "id": f"C_{code}_w{window}_k{threshold:g}_h{hold}",
                        "family": family,
                        "params": {"window": window, "threshold": threshold},
                        "hold": hold,
                        "stop": 1.5,
                        "tp": 1.5,
                    })
    return specs


def signals(c, spec):
    """Return signal directions and entry distance scales, in USD/oz.

    A signal at t uses close[t], a rolling window ending at t-1, and
    volatility[t-1]. The returned execution scale uses volatility[t].
    The 0.5 USD floor also bounds the normalization denominator. Every
    window must lie in one session and contain exact adjacent minutes.
    Scale is zero where there is no signal. Neither A/B nor outcomes are
    inspected; input arrays are never modified.
    """
    mid = np.asarray(c["mid"], dtype=float)
    mins = np.asarray(c["mins"])
    eff = np.asarray(c["eff"], dtype=float)
    session = np.asarray(c["calendar"].session_day)
    n = len(mid)
    if any(a.shape != (n,) for a in (mid, mins, eff, session)):
        raise ValueError("mid, mins, eff and calendar.session_day must be equal-length vectors")
    family = spec["family"]
    if family not in ("mean_deviation_reversal", "compression_breakout"):
        raise ValueError(f"Unknown structural signal family: {family}")
    window = int(spec["params"]["window"])
    threshold = float(spec["params"]["threshold"])
    if window < 1 or not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("window and threshold must be positive")
    side = np.zeros(n, dtype=np.int8)
    scale = np.zeros(n, dtype=float)
    if n == 0:
        return side, scale

    # The count since the latest boundary rejects rolling windows which
    # otherwise would bridge a gap/session boundary. Invalid quotes also
    # interrupt history rather than silently entering a rolling feature.
    valid_mid = np.isfinite(mid) & (mid > 0)
    boundary = np.ones(n, dtype=bool)
    boundary[1:] = ((mins[1:] - mins[:-1] != 1)
                    | (session[1:] != session[:-1])
                    | ~valid_mid[1:] | ~valid_mid[:-1])
    row = np.arange(n)
    age = row - np.maximum.accumulate(np.where(boundary, row, 0))
    current_vol = eff * mid / 10000.
    valid_vol = np.isfinite(current_vol) & (eff >= 0)
    execution_scale = np.maximum(current_vol, .5)
    prior_vol = np.full(n, np.nan)
    prior_vol[1:] = np.where(valid_vol[:-1], execution_scale[:-1], np.nan)
    eligible = (age >= window) & valid_mid & valid_vol & np.isfinite(prior_vol)
    prior_close = pd.Series(mid).shift(1).rolling(window, min_periods=window)

    if family == "mean_deviation_reversal":
        mean = prior_close.mean().to_numpy()
        deviation = (mid - mean) / prior_vol
        deviation[~eligible] = np.nan
        previous = np.full(n, np.nan)
        previous[1:] = deviation[:-1]
        inside = eligible & (np.abs(deviation) <= threshold)
        # Current and previous normalized deviations each use their own
        # strictly prior rolling mean and volatility.
        side[inside & (previous < -threshold)] = 1
        side[inside & (previous > threshold)] = -1
    else:
        high = prior_close.max().to_numpy()
        low = prior_close.min().to_numpy()
        compressed = (high - low) <= threshold * prior_vol
        above = eligible & (mid > high)
        below = eligible & (mid < low)
        was_above = np.zeros(n, dtype=bool)
        was_below = np.zeros(n, dtype=bool)
        was_above[1:] = above[:-1]
        was_below[1:] = below[:-1]
        # Detect the crossing before applying compression: a continuing
        # breakout does not become a fresh event when compression changes.
        side[compressed & above & ~was_above] = 1
        side[compressed & below & ~was_below] = -1

    active = side != 0
    scale[active] = execution_scale[active]
    return side, scale


def _synthetic_checks():
    import unittest
    from types import SimpleNamespace

    def context(mid):
        mid = np.asarray(mid, dtype=float)
        n = len(mid)
        return {
            "mid": mid,
            "mins": np.arange(n, dtype=np.int64),
            "eff": 10000.0 / mid,  # One USD/oz at each row.
            "calendar": SimpleNamespace(session_day=np.zeros(n, dtype=np.int64)),
        }

    def spec(family, window, threshold):
        return {
            "id": "synthetic",
            "family": family,
            "params": {"window": window, "threshold": threshold},
            "hold": 30,
            "stop": 1.5,
            "tp": 1.5,
        }

    class SyntheticChecks(unittest.TestCase):
        def test_candidate_grid(self):
            specs = candidates()
            self.assertEqual(len(specs), 16)
            self.assertEqual(len({s["id"] for s in specs}), 16)
            self.assertEqual(sum(s["family"] == "mean_deviation_reversal" for s in specs), 8)
            self.assertEqual(sum(s["family"] == "compression_breakout" for s in specs), 8)
            self.assertTrue(all(s["hold"] in (30, 90) and s["stop"] == s["tp"] == 1.5 for s in specs))

        def test_mean_reentry_both_sides_and_no_repeat(self):
            for direction in (1, -1):
                c = context([1000.] * 60 + [1000. - direction * 2., 1000. - direction * .2, 1000.])
                side, scale = signals(c, spec("mean_deviation_reversal", 60, 1.5))
                self.assertEqual(np.flatnonzero(side).tolist(), [61])
                self.assertEqual(side[61], direction)
                self.assertAlmostEqual(scale[61], 1.)

        def test_mean_does_not_call_opposite_extension_inside(self):
            c = context([1000.] * 60 + [998., 1002.])
            side, _ = signals(c, spec("mean_deviation_reversal", 60, 1.5))
            self.assertFalse(side.any())

        def test_prior_volatility_for_trigger_current_volatility_for_scale(self):
            c = context([1000.] * 60 + [998., 999.8])
            c["eff"][-1] = 1000.
            side, scale = signals(c, spec("mean_deviation_reversal", 60, 1.5))
            self.assertEqual(side[-1], 1)
            self.assertAlmostEqual(scale[-1], 99.98)
            c = context([1000.] * 60 + [998., 999.1])
            c["eff"][-1] = .01
            side, scale = signals(c, spec("mean_deviation_reversal", 60, 1.5))
            self.assertEqual(side[-1], 1)
            self.assertEqual(scale[-1], .5)

        def test_breakout_first_cross_only_both_sides(self):
            for direction in (1, -1):
                c = context([1000.] * 30 + [1000. + direction * .8, 1000. + direction, 1000. + direction * .9, 1000. + direction * 1.1])
                side, _ = signals(c, spec("compression_breakout", 30, 1.))
                self.assertEqual(np.flatnonzero(side).tolist(), [30, 33])
                self.assertTrue(np.all(side[[30, 33]] == direction))

        def test_wide_range_is_not_compression(self):
            c = context([999., 1001.] * 15 + [1002.])
            c["eff"][-1] = 1000.  # Current volatility must not qualify the range.
            side, _ = signals(c, spec("compression_breakout", 30, 1.5))
            self.assertFalse(side.any())

        def test_gap_and_session_restart_history(self):
            fixtures = [
                (context([1000.] * 60 + [998., 999.8]), spec("mean_deviation_reversal", 60, 1.5), 61),
                (context([1000.] * 30 + [1000.8]), spec("compression_breakout", 30, 1.), 30),
            ]
            for original, s, at in fixtures:
                for reset in ("gap", "session"):
                    c = context(original["mid"])
                    if reset == "gap":
                        c["mins"][at:] += 1
                    else:
                        c["calendar"].session_day[at:] += 1
                    side, _ = signals(c, s)
                    self.assertFalse(side.any(), reset)

        def test_scale_floor_and_input_unchanged(self):
            c = context([1000.] * 30 + [1000.2])
            c["eff"][:] = .01
            before = {k: v.copy() for k, v in c.items() if isinstance(v, np.ndarray)}
            side, scale = signals(c, spec("compression_breakout", 30, 1.))
            self.assertEqual(side[-1], 1)
            self.assertEqual(scale[-1], .5)
            for key, original in before.items():
                np.testing.assert_array_equal(c[key], original)

        def test_all_prefixes_match_full_history(self):
            t = np.arange(650)
            c = context(1000. + 2.2 * np.sin(t / 7.) + .2 * np.cos(t / 29.))
            c["mins"][320:] += 7
            c["calendar"].session_day[500:] = 1
            for s in candidates():
                full_side, full_scale = signals(c, s)
                self.assertEqual(full_side.dtype, np.dtype("int8"))
                self.assertEqual(full_side.shape, (650,))
                for size in (0, 29, 30, 60, 61, 120, 240, 241, 319, 320, 321, 500, 501, 650):
                    prefix = {k: v[:size].copy() if isinstance(v, np.ndarray) else SimpleNamespace(session_day=v.session_day[:size].copy()) for k, v in c.items()}
                    side, scale = signals(prefix, s)
                    np.testing.assert_array_equal(side, full_side[:size])
                    np.testing.assert_array_equal(scale, full_scale[:size])

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    _synthetic_checks()
