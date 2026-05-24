"""Unit tests for the CubicBezier easing used by humanized interactions.

solve_curve_x must invert sample_curve_x (find the parameter t for a given x) so
the humanized movement/scroll timing maps real time onto the easing curve. These
assert the mathematical contract — round-trip accuracy and endpoint clamping —
without any browser.
"""

from __future__ import annotations

import pytest

from pydoll.interactions.utils import CubicBezier

# A typical ease-in-out control polygon.
_CURVE = CubicBezier(0.42, 0.0, 0.58, 1.0)


@pytest.mark.parametrize('x', [0.0, 0.2, 0.5, 0.75, 1.0])
def test_solve_curve_x_round_trips_through_sample(x):
    t = _CURVE.solve_curve_x(x)
    assert abs(_CURVE.sample_curve_x(t) - x) < 1e-3


def test_sample_curve_y_endpoints():
    assert _CURVE.sample_curve_y(0.0) == 0.0
    assert abs(_CURVE.sample_curve_y(1.0) - 1.0) < 1e-9
