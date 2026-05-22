"""Pure-logic tests for interaction physics helpers (no browser, no fakes)."""

from __future__ import annotations

import math
import random

import pytest

from pydoll.interactions.utils import (
    CubicBezier,
    bezier_2d,
    fitts_duration,
    minimum_jerk,
    random_control_points,
)


def test_cubic_bezier_maps_endpoints_to_zero_and_one():
    curve = CubicBezier(0.25, 0.1, 0.25, 1.0)
    assert curve.solve(0.0) == pytest.approx(0.0)
    assert curve.solve(1.0) == pytest.approx(1.0)


def test_cubic_bezier_is_monotonic_within_unit_interval():
    curve = CubicBezier(0.42, 0.0, 0.58, 1.0)
    samples = [curve.solve(x / 10) for x in range(11)]
    assert samples == sorted(samples)
    assert all(0.0 <= value <= 1.0 for value in samples)


def test_minimum_jerk_endpoints_and_midpoint():
    assert minimum_jerk(0.0) == pytest.approx(0.0)
    assert minimum_jerk(1.0) == pytest.approx(1.0)
    assert minimum_jerk(0.5) == pytest.approx(0.5)


def test_minimum_jerk_is_monotonic():
    samples = [minimum_jerk(t / 20) for t in range(21)]
    assert samples == sorted(samples)


def test_bezier_2d_returns_endpoints():
    p0, p1, p2, p3 = (0.0, 0.0), (10.0, 20.0), (30.0, 40.0), (100.0, 0.0)
    assert bezier_2d(0.0, p0, p1, p2, p3) == pytest.approx(p0)
    assert bezier_2d(1.0, p0, p1, p2, p3) == pytest.approx(p3)


def test_bezier_2d_midpoint_of_evenly_spaced_line():
    p0, p1, p2, p3 = (0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0)
    assert bezier_2d(0.5, p0, p1, p2, p3) == pytest.approx((1.5, 1.5))


def test_fitts_duration_floor_for_nonpositive_distance():
    assert fitts_duration(0.0, 10.0, a=0.1, b=0.2) == 0.1
    assert fitts_duration(-5.0, 10.0, a=0.1, b=0.2) == 0.1


def test_fitts_duration_grows_with_distance():
    near = fitts_duration(10.0, 10.0, a=0.1, b=0.2)
    far = fitts_duration(1000.0, 10.0, a=0.1, b=0.2)
    assert near == pytest.approx(0.1 + 0.2 * math.log2(2))
    assert far > near


def test_random_control_points_short_distance_returns_endpoints():
    start, end = (0.0, 0.0), (0.5, 0.5)
    assert random_control_points(start, end, 0.1, 0.3, 0.5, 100.0) == (start, end)


def test_random_control_points_returns_two_finite_points():
    random.seed(7)
    cp1, cp2 = random_control_points((0.0, 0.0), (100.0, 0.0), 0.1, 0.3, 0.5, 100.0)
    for point in (cp1, cp2):
        assert len(point) == 2
        assert all(math.isfinite(coord) for coord in point)
