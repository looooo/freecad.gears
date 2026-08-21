# -*- coding: utf-8 -*-
"""Unit tests for pygears._functions (2D/3D transforms and geometry helpers)."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pygears import __version__
from pygears._functions import (
    arc_from_points_and_center,
    diff_norm,
    intersection_line_circle,
    nearestpts,
    reflection,
    reflection3D,
    rotation,
    rotation3D,
    translation,
    trim,
    trimfunc,
)


def test_package_version_is_semver_string():
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


# ---------------------------------------------------------------------------
# reflections / rotations / translations
# ---------------------------------------------------------------------------


def test_reflection_over_x_axis():
    reflect = reflection(0.0)
    points = np.array([[1.0, 2.0], [-3.0, 4.0]])
    assert_allclose(reflect(points), np.array([[1.0, -2.0], [-3.0, -4.0]]))


def test_reflection_over_y_axis():
    reflect = reflection(np.pi / 2)
    points = np.array([[1.0, 2.0], [-3.0, 4.0]])
    assert_allclose(reflect(points), np.array([[-1.0, 2.0], [3.0, 4.0]]), atol=1e-12)


def test_reflection_is_involutory():
    points = np.array([[1.5, -0.3], [4.0, 2.2], [0.0, 0.0]])
    reflect = reflection(0.37)
    assert_allclose(reflect(reflect(points)), points, atol=1e-12)


def test_reflection_preserves_distances():
    points = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0]])
    out = reflection(0.2)(points)
    assert_allclose(np.linalg.norm(out[1] - out[0]), 1.0)
    assert_allclose(np.linalg.norm(out[2] - out[0]), 2.0)


def test_reflection3d_mirrors_xy_and_keeps_z():
    points = np.array([[1.0, 2.0, 7.0], [-3.0, 4.0, -1.0]])
    out = reflection3D(0.0)(points)
    assert_allclose(out, np.array([[1.0, -2.0, 7.0], [-3.0, -4.0, -1.0]]))


def test_rotation_identity_and_quarter_turn():
    points = np.array([[1.0, 0.0], [0.0, 1.0]])
    assert_allclose(rotation(0.0)(points), points)
    out = rotation(np.pi / 2)(points)
    assert_allclose(out, np.array([[0.0, 1.0], [-1.0, 0.0]]), atol=1e-12)


def test_rotation_around_center():
    points = np.array([[2.0, 0.0], [3.0, 0.0]])
    out = rotation(np.pi / 2, center=[2.0, 0.0])(points)
    assert_allclose(out, np.array([[2.0, 0.0], [2.0, 1.0]]), atol=1e-12)


def test_rotation_full_turn_is_identity():
    points = np.array([[1.2, -3.4], [0.5, 0.5]])
    assert_allclose(rotation(2 * np.pi)(points), points, atol=1e-12)


def test_rotation3d_rotates_xy_and_keeps_z():
    points = np.array([[1.0, 0.0, 5.0]])
    out = rotation3D(np.pi / 2)(points)
    assert_allclose(out, np.array([[0.0, 1.0, 5.0]]), atol=1e-12)


def test_translation_shifts_all_points():
    points = np.array([[0.0, 0.0], [1.0, 2.0]])
    out = translation([3.0, -4.0])(points)
    assert_allclose(out, np.array([[3.0, -4.0], [4.0, -2.0]]))


# ---------------------------------------------------------------------------
# trim / trimfunc
# ---------------------------------------------------------------------------


def test_trim_crossing_segments():
    point = trim([0.0, 0.0], [1.0, 1.0], [0.0, 1.0], [1.0, 0.0])
    assert_allclose(point, [0.5, 0.5])


def test_trim_non_crossing_parallel_segments():
    assert trim([0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]) is False


def test_trim_shared_end_of_first_segment_is_start_of_second():
    # p2 == p3: the implementation returns the shared vertex rather than False
    point = trim([0.0, 0.0], [1.0, 0.0], [1.0, 0.0], [2.0, 0.0])
    assert_allclose(point, [1.0, 0.0])


def test_trim_shared_start_point():
    point = trim([0.0, 0.0], [1.0, 0.0], [0.0, 0.0], [0.0, 1.0])
    assert_allclose(point, [0.0, 0.0])


def test_trim_identical_endpoints_of_first_segment():
    assert trim([1.0, 1.0], [1.0, 1.0], [0.0, 0.0], [2.0, 2.0]) is False
    assert_allclose(trim([1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [2.0, 2.0]), [1.0, 1.0])


def test_trim_identical_segments_returns_midpoint():
    mid = trim([0.0, 0.0], [2.0, 0.0], [0.0, 0.0], [2.0, 0.0])
    assert_allclose(mid, [1.0, 0.0])


def test_trimfunc_returns_polylines_cut_at_intersection():
    line_1 = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    line_2 = np.array([[0.0, 2.0], [1.0, 1.0], [2.0, 0.0]])
    result = trimfunc(line_1, line_2)
    assert result is not False
    cut_1, cut_2 = result
    assert_allclose(cut_1[-1], [1.0, 1.0])
    assert_allclose(cut_2[0], [1.0, 1.0])


def test_trimfunc_no_intersection():
    line_1 = np.array([[0.0, 0.0], [1.0, 0.0]])
    line_2 = np.array([[0.0, 1.0], [1.0, 1.0]])
    assert trimfunc(line_1, line_2) is False


def test_trimfunc_intersection_on_first_segment_of_second_line():
    # jk == 0 hits a comparison-no-op in trimfunc; second polyline is not truncated.
    line_1 = np.array([[0.0, 0.0], [2.0, 0.0]])
    line_2 = np.array([[1.0, -1.0], [1.0, 1.0]])
    result = trimfunc(line_1, line_2)
    assert result is not False
    cut_1, cut_2 = result
    assert_allclose(cut_1[-1], [1.0, 0.0])
    assert_allclose(cut_2[0], [1.0, 0.0])
    assert cut_2.shape[0] == 1 + line_2.shape[0]


# ---------------------------------------------------------------------------
# distances / nearest points / circle helpers
# ---------------------------------------------------------------------------


def test_diff_norm_euclidean_distance():
    assert diff_norm([0.0, 0.0], [3.0, 4.0]) == pytest.approx(5.0)
    assert diff_norm([1.0, 1.0], [1.0, 1.0]) == pytest.approx(0.0)


def test_nearestpts_stitches_undercut_prefix_to_involute():
    involute = np.array([[3.0, 0.0], [4.0, 0.0], [5.0, 0.0]])
    undercut = np.array([[1.0, 0.0], [2.0, 0.0], [3.9, 0.1]])
    combined, rest = nearestpts(involute, undercut)
    assert combined.shape[1] == 2
    assert rest.ndim == 2
    # rest is a suffix of the involute (indices come from the sliced search)
    assert_allclose(rest[-1], involute[-1])
    assert rest.shape[0] <= involute.shape[0]


def test_intersection_line_circle_lies_on_sphere_and_line():
    point_1 = np.array([2.0, 0.0, 0.0])
    point_2 = np.array([0.0, 0.0, 0.0])
    hit = intersection_line_circle(point_1, point_2, 1.0)
    assert_allclose(np.linalg.norm(hit), 1.0)
    # colinear with the two input points
    direction = point_2 - point_1
    offset = hit - point_1
    assert_allclose(np.cross(direction, offset), 0.0, atol=1e-12)


def test_intersection_line_circle_from_inside_towards_positive_x():
    hit = intersection_line_circle(
        np.array([0.1, 0.0, 0.0]), np.array([2.0, 0.0, 0.0]), 1.0
    )
    assert_allclose(hit, [1.0, 0.0, 0.0])


def test_arc_from_points_and_center_midpoint_on_circle():
    point_1 = np.array([1.0, 0.0])
    point_2 = np.array([0.0, 1.0])
    center = np.array([0.0, 0.0])
    start, mid, end = arc_from_points_and_center(point_1, point_2, center)
    assert_allclose(start, point_1)
    assert_allclose(end, point_2)
    assert_allclose(np.linalg.norm(mid - center), 1.0)
    # minor-arc midpoint of the quarter circle
    assert_allclose(mid, [np.sqrt(2) / 2, np.sqrt(2) / 2])
