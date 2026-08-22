# -*- coding: utf-8 -*-
"""Unit tests for pygears.computation (Newton root finder and gear centre distance)."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pygears.computation import compute_shifted_gears, find_root, minimize


def _inv(angle):
    return np.tan(angle) - angle


def test_minimize_quadratic():
    result = minimize(lambda x: (x - 2.0) ** 2, 0.0)
    assert result.x[0] == pytest.approx(2.0, abs=1e-6)
    assert result.fun == pytest.approx(0.0, abs=1e-10)


def test_minimize_timing_gear_distances_match_scipy():
    pitch = 5.0
    teeth = 15
    u = 0.6
    tooth_height = 1.2
    alpha = np.deg2rad(40.0)
    backlash = 0.0

    r_p = pitch * teeth / 2.0 / np.pi
    gamma_0 = pitch / r_p
    gamma_1 = gamma_0 / 4.0
    p_A = np.array([np.cos(-gamma_1), np.sin(-gamma_1)]) * (
        r_p - u - tooth_height / 2
    )
    direction = np.array(
        [np.cos(alpha / 2 - gamma_1), np.sin(alpha / 2 - gamma_1)]
    )

    def line(s):
        return p_A + direction * s

    def dist_p1(s):
        return (np.linalg.norm(line(s)) - (r_p - u - tooth_height)) ** 2

    def dist_p2(s):
        return (np.linalg.norm(line(s)) - (r_p - u)) ** 2

    s1 = minimize(dist_p1, 0.0).x[0]
    s2 = minimize(dist_p2, 0.0).x[0]
    assert dist_p1(s1) == pytest.approx(0.0, abs=1e-10)
    assert dist_p2(s2) == pytest.approx(0.0, abs=1e-10)
    assert s1 == pytest.approx(-0.64103017, abs=1e-5)
    assert s2 == pytest.approx(0.63628363, abs=1e-5)


def test_find_root_lantern_gear_phi_min():
    m = 1.0
    teeth = 15
    r_r = 1.0
    r_0 = m * teeth / 2
    r_max = r_0 + r_r
    phi_max = (r_r + np.sqrt(r_max**2 - r_0**2)) / r_0
    x0 = (phi_max + r_r / r_0 * 4) / 5

    def find_phi_min(phi_min):
        return r_0 * (
            phi_min**2 * r_0
            - 2 * phi_min * r_0 * np.sin(phi_min)
            - 2 * phi_min * r_r
            - 2 * r_0 * np.cos(phi_min)
            + 2 * r_0
            + 2 * r_r * np.sin(phi_min)
        )

    def d_find_phi_min(phi_min):
        return 2 * r_0 * (1 - np.cos(phi_min)) * (phi_min * r_0 - r_r)

    phi_min = find_root(x0, find_phi_min, d_find_phi_min)
    assert find_phi_min(phi_min) == pytest.approx(0.0, abs=1e-8)
    assert phi_min == pytest.approx(0.17780902310246768, abs=1e-5)


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
