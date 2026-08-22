# -*- coding: utf-8 -*-
"""Unit tests for spherical involute bevel teeth in pygears.bevel_tooth."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pygears.bevel_tooth import BevelTooth


def _stack(segments):
    return np.vstack([np.atleast_2d(segment) for segment in segments])


def _segments_connected(segments, atol=1e-9):
    for previous, current in zip(segments, segments[1:]):
        previous = np.atleast_2d(previous)
        current = np.atleast_2d(current)
        if np.linalg.norm(previous[-1] - current[0]) > atol:
            return False
    return True


def test_constructor_sets_angular_backlash_and_limits():
    tooth = BevelTooth(z=21, module=0.25, backlash=0.0)
    assert tooth.z == 21
    assert tooth.module == pytest.approx(0.25)
    assert tooth.angular_backlash == pytest.approx(0.0)
    assert np.isfinite(tooth.involute_start)
    assert np.isfinite(tooth.involute_end)
    assert tooth.involute_start < tooth.involute_end
    assert tooth.add_foot is True


def test_involute_functions_are_consistent_with_get_radius():
    tooth = BevelTooth()
    sample = 0.5 * (tooth.involute_start + tooth.involute_end)
    fx, fy, fz = (
        tooth.involute_function_x(),
        tooth.involute_function_y(),
        tooth.involute_function_z(),
    )
    radius = tooth.get_radius(sample)
    assert radius == pytest.approx(np.hypot(fx(sample), fy(sample)))
    assert np.isfinite(fz(sample))


def test_involute_start_radius_matches_function():
    tooth = BevelTooth()
    assert tooth.involute_start_radius == pytest.approx(
        tooth.get_radius(tooth.involute_start)
    )


@pytest.mark.parametrize("num", [6, 10, 15])
def test_points_are_3d_connected_and_projected_to_z_one(num):
    tooth = BevelTooth()
    segments = tooth.points(num=num)
    assert _segments_connected(segments)
    points = _stack(segments)
    assert points.shape[1] == 3
    assert np.all(np.isfinite(points))
    # conical projection onto the plane z = 1
    assert_allclose(points[:, 2], 1.0)
    if tooth.add_foot:
        assert len(segments) == 5
    else:
        assert len(segments) == 3


def test_backlash_rotates_projected_involute():
    plain = BevelTooth(backlash=0.0)
    with_backlash = BevelTooth(backlash=0.05)
    assert with_backlash.angular_backlash == pytest.approx(
        0.05 / (with_backlash.z * with_backlash.module / 2)
    )
    p0 = plain.involute_points(num=8)[0]
    p1 = with_backlash.involute_points(num=8)[0]
    delta = np.arctan2(p1[1], p1[0]) - np.arctan2(p0[1], p0[0])
    assert delta == pytest.approx(-with_backlash.angular_backlash / 2, rel=1e-6, abs=1e-8)


def test_root_radius_on_projected_plane():
    tooth = BevelTooth()
    projected_root = tooth.r_f / tooth.z_f
    points = np.asarray(tooth.involute_points(num=12))
    radii = np.linalg.norm(points[:, :2], axis=1)
    assert radii.min() == pytest.approx(projected_root, rel=1e-8)


def test_flanks_are_mirrored_across_the_yz_plane():
    tooth = BevelTooth()
    segments = tooth.points(num=10)
    if tooth.add_foot:
        left, right = segments[1], segments[3]
    else:
        left, right = segments[0], segments[2]
    mirrored = left * np.array([-1.0, 1.0, 1.0])
    assert_allclose(mirrored, right[::-1], atol=1e-10)


def test_update_rebuilds_derived_quantities():
    tooth = BevelTooth(z=21)
    original_end = tooth.involute_end
    tooth.z = 33
    tooth._update()
    assert tooth.z == 33
    assert tooth.involute_end != pytest.approx(original_end)
    assert np.isfinite(tooth.involute_end)


@pytest.mark.parametrize("z", [12, 21, 40])
def test_tooth_count_changes_pitch_partition(z):
    tooth = BevelTooth(z=z)
    points = _stack(tooth.points(num=8))
    assert points.shape[0] > 0
    # angular width of one tooth stays below 2π/z after centering
    angles = np.arctan2(points[:, 1], points[:, 0])
    assert np.ptp(angles) < 2 * np.pi / z + 1e-6
