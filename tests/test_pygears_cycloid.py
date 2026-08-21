# -*- coding: utf-8 -*-
"""Unit tests for cycloid tooth geometry in pygears.cycloid_tooth."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pygears.cycloid_tooth import CycloidTooth


def _stack(segments):
    return np.vstack([np.atleast_2d(segment) for segment in segments])


def _segments_connected(segments, atol=1e-10):
    for previous, current in zip(segments, segments[1:]):
        previous = np.atleast_2d(previous)
        current = np.atleast_2d(current)
        if np.linalg.norm(previous[-1] - current[0]) > atol:
            return False
    return True


def _is_symmetric_about_x(points, atol=1e-8):
    mirrored = points * np.array([1.0, -1.0])
    for point in mirrored:
        if np.min(np.linalg.norm(points - point, axis=1)) > atol:
            return False
    return True


def test_default_gear_factors():
    tooth = CycloidTooth()
    assert tooth.d == pytest.approx(tooth.num_teeth * tooth.m)
    assert tooth.d1 == pytest.approx(tooth.num_teeth_1 * tooth.m)
    assert tooth.d2 == pytest.approx(tooth.num_teeth_2 * tooth.m)
    assert tooth.da == pytest.approx(tooth.d + 2 * (1 + tooth.head) * tooth.m)
    assert tooth.di == pytest.approx(tooth.d - 2 * (1 + tooth.clearance) * tooth.m)
    assert tooth.phipart == pytest.approx(2 * np.pi / tooth.num_teeth)
    assert tooth.phi == pytest.approx(tooth.m * np.pi)
    assert tooth.angular_backlash == pytest.approx(0.0)


def test_epi_and_hypocycloid_start_on_pitch_circle():
    tooth = CycloidTooth()
    assert tooth.epicycloid_x()(0.0) == pytest.approx(tooth.d / 2)
    assert tooth.epicycloid_y()(0.0) == pytest.approx(0.0)
    assert tooth.hypocycloid_x()(0.0) == pytest.approx(tooth.d / 2)
    assert tooth.hypocycloid_y()(0.0) == pytest.approx(0.0)


def test_outer_end_reaches_addendum_circle():
    tooth = CycloidTooth()
    t_end = tooth.outer_end()
    radius = np.hypot(tooth.epicycloid_x()(t_end), tooth.epicycloid_y()(t_end))
    assert radius == pytest.approx(tooth.da / 2)


def test_inner_end_reaches_dedendum_circle():
    tooth = CycloidTooth()
    t_end = tooth.inner_end()
    radius = np.hypot(tooth.hypocycloid_x()(t_end), tooth.hypocycloid_y()(t_end))
    assert radius == pytest.approx(tooth.di / 2)


@pytest.mark.parametrize("num", [5, 10, 16])
def test_points_are_connected_symmetric_and_in_annulus(num):
    tooth = CycloidTooth()
    segments = tooth.points(num=num)
    assert len(segments) == 3
    assert _segments_connected(segments)
    points = _stack(segments)
    assert points.shape[1] == 2
    assert np.all(np.isfinite(points))
    assert _is_symmetric_about_x(points)
    radii = np.linalg.norm(points, axis=1)
    assert radii.min() == pytest.approx(tooth.di / 2, rel=1e-9)
    assert radii.max() == pytest.approx(tooth.da / 2, rel=1e-9)
    # inner and outer samples share the pitch point, so one vertex is dropped
    assert segments[0].shape[0] == (num - 2) + num
    assert segments[2].shape[0] == segments[0].shape[0]


def test_head_and_clearance_change_tip_and_root():
    base = CycloidTooth(head=0.0, clearance=0.25)
    modified = CycloidTooth(head=0.2, clearance=0.5)
    assert modified.da == pytest.approx(base.da + 0.4 * base.m)
    assert modified.di == pytest.approx(base.di - 0.5 * base.m)


def test_backlash_rotates_the_tooth():
    plain = CycloidTooth(backlash=0.0)
    with_backlash = CycloidTooth(backlash=0.4)
    assert with_backlash.angular_backlash == pytest.approx(0.4 / (with_backlash.d / 2))
    p0 = plain.points(num=8)[0][0]
    p1 = with_backlash.points(num=8)[0][0]
    delta = np.arctan2(p1[1], p1[0]) - np.arctan2(p0[1], p0[0])
    assert delta == pytest.approx(with_backlash.angular_backlash / 2, rel=1e-8)


def test_update_recomputes_from_current_attributes():
    tooth = CycloidTooth()
    tooth.num_teeth = 20
    tooth.m = 2.0
    tooth.head = 0.1
    tooth._update()
    assert tooth.d == pytest.approx(40.0)
    assert tooth.da == pytest.approx(40.0 + 2 * 1.1 * 2.0)


def test_rolling_circle_diameters_scale_with_module():
    tooth = CycloidTooth(num_teeth_1=3, num_teeth_2=7, m=4)
    assert tooth.d1 == pytest.approx(12.0)
    assert tooth.d2 == pytest.approx(28.0)
    points = _stack(tooth.points(num=6))
    assert_allclose(np.linalg.norm(points, axis=1).max(), tooth.da / 2, rtol=1e-9)
