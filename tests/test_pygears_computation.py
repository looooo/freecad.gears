# -*- coding: utf-8 -*-
"""Unit tests for pygears.computation (Newton root finder and gear centre distance)."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pygears.computation import compute_shifted_gears, find_root


def _inv(angle):
    return np.tan(angle) - angle


def test_find_root_quadratic():
    root = find_root(1.0, lambda x: x**2 - 2.0, lambda x: 2.0 * x)
    assert root == pytest.approx(np.sqrt(2.0), rel=1e-8)


def test_find_root_already_at_solution():
    assert find_root(3.0, lambda x: 0.0, lambda x: 1.0) == pytest.approx(3.0)


def test_find_root_zero_derivative_returns_none():
    assert find_root(1.0, lambda x: 1.0, lambda x: 0.0) is None


def test_find_root_max_iter_returns_none():
    # f never reaches epsilon because the iterate is damped and we stop early
    assert (
        find_root(1.0, lambda x: 1.0, lambda x: 1.0, epsilon=1e-20, max_iter=3) is None
    )


def test_unshifted_gears_keep_standard_centre_distance():
    module = 2.5
    alpha = np.deg2rad(20.0)
    teeth_1, teeth_2 = 20, 40
    distance, alpha_w = compute_shifted_gears(
        module, alpha, teeth_1, teeth_2, 0.0, 0.0
    )
    assert distance == pytest.approx(module * (teeth_1 + teeth_2) / 2.0)
    assert alpha_w == pytest.approx(alpha, abs=1e-10)


def test_equal_and_opposite_shifts_cancel():
    module = 1.0
    alpha = np.deg2rad(20.0)
    distance, alpha_w = compute_shifted_gears(module, alpha, 20, 40, 0.3, -0.3)
    assert distance == pytest.approx(module * (20 + 40) / 2.0)
    assert alpha_w == pytest.approx(alpha, abs=1e-10)


def test_positive_shifts_increase_centre_distance_and_working_angle():
    module = 1.0
    alpha = np.deg2rad(20.0)
    distance, alpha_w = compute_shifted_gears(module, alpha, 20, 40, 0.5, 0.5)
    assert distance > module * (20 + 40) / 2.0
    assert alpha_w > alpha
    # ISO involute relation: inv(αw) = inv(α) + 2 tan(α) (x1+x2)/(z1+z2)
    expected_inv = _inv(alpha) + 2 * np.tan(alpha) * (0.5 + 0.5) / (20 + 40)
    assert _inv(alpha_w) == pytest.approx(expected_inv, rel=1e-8)
    assert distance == pytest.approx(
        module * (20 + 40) / 2.0 * np.cos(alpha) / np.cos(alpha_w), rel=1e-8
    )


@pytest.mark.parametrize(
    "module,teeth_1,teeth_2,shift_1,shift_2",
    [
        (1.0, 12, 12, 0.0, 0.0),
        (3.0, 15, 45, 0.2, 0.1),
        (2.0, 25, 30, -0.1, 0.4),
    ],
)
def test_shifted_gears_satisfy_involute_and_cosine_laws(
    module, teeth_1, teeth_2, shift_1, shift_2
):
    alpha = np.deg2rad(20.0)
    distance, alpha_w = compute_shifted_gears(
        module, alpha, teeth_1, teeth_2, shift_1, shift_2
    )
    expected_inv = _inv(alpha) + 2 * np.tan(alpha) * (shift_1 + shift_2) / (
        teeth_1 + teeth_2
    )
    assert_allclose(_inv(alpha_w), expected_inv, rtol=1e-7, atol=1e-10)
    expected_distance = (
        module * (teeth_1 + teeth_2) / 2.0 * np.cos(alpha) / np.cos(alpha_w)
    )
    assert distance == pytest.approx(expected_distance, rel=1e-8)
    assert np.isfinite(distance) and np.isfinite(alpha_w)
