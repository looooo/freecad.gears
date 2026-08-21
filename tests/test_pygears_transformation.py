# -*- coding: utf-8 -*-
"""Unit tests for Euler-Rodrigues homogeneous transforms in pygears.transformation."""

import numpy as np
import pytest
import sympy as sym
from numpy.testing import assert_allclose

from pygears.transformation import numeric_transformation, symbolic_transformation


def _apply(matrix, point):
    homogeneous = np.append(np.asarray(point, dtype=float), 1.0)
    return (matrix @ homogeneous)[:3]


def test_numeric_identity_for_zero_angle():
    matrix = numeric_transformation(0.0, np.array([0.0, 0.0, 1.0]))
    assert_allclose(matrix, np.eye(4), atol=1e-12)


def test_numeric_translation_is_last_column():
    translation = np.array([1.5, -2.0, 4.0])
    matrix = numeric_transformation(0.0, np.array([1.0, 0.0, 0.0]), translation)
    point = _apply(matrix, [0.0, 0.0, 0.0])
    assert_allclose(point, translation)


def test_numeric_rotation_around_z():
    matrix = numeric_transformation(np.pi / 2, np.array([0.0, 0.0, 1.0]))
    # column-vector convention of this Rodrigues layout maps +x towards -y
    assert_allclose(_apply(matrix, [1.0, 0.0, 0.0]), [0.0, -1.0, 0.0], atol=1e-12)
    assert_allclose(_apply(matrix, [0.0, 0.0, 3.0]), [0.0, 0.0, 3.0], atol=1e-12)


def test_numeric_rotation_around_x_keeps_axis_points_fixed():
    matrix = numeric_transformation(0.8, np.array([2.0, 0.0, 0.0]), np.zeros(3))
    assert_allclose(_apply(matrix, [5.0, 0.0, 0.0]), [5.0, 0.0, 0.0], atol=1e-12)


def test_numeric_linear_part_is_orthogonal():
    matrix = numeric_transformation(1.1, np.array([1.0, 2.0, 3.0]))
    rotation = matrix[:3, :3]
    assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-12)
    assert pytest.approx(np.linalg.det(rotation), abs=1e-12) == 1.0


def test_numeric_full_turn_is_identity():
    matrix = numeric_transformation(2 * np.pi, np.array([1.0, 1.0, 0.0]))
    assert_allclose(matrix, np.eye(4), atol=1e-12)


def test_numeric_rejects_non_3d_axis():
    with pytest.raises(AssertionError):
        numeric_transformation(0.1, np.array([1.0, 0.0]))


def test_symbolic_matches_numeric():
    angle = 0.7
    axis = [1.0, 2.0, 3.0]
    translation = np.array([0.5, -1.0, 2.0])
    numeric = numeric_transformation(angle, np.array(axis), translation)
    symbolic = symbolic_transformation(angle, sym.Matrix(axis), translation)
    assert_allclose(np.array(symbolic.tolist(), dtype=float), numeric, atol=1e-12)


def test_symbolic_zero_angle_is_translation():
    translation = np.array([3.0, 0.0, -1.0])
    matrix = symbolic_transformation(0, sym.Matrix([0, 1, 0]), translation)
    numeric = np.array(matrix.tolist(), dtype=float)
    expected = np.eye(4)
    expected[:3, 3] = translation
    assert_allclose(numeric, expected, atol=1e-12)


def test_symbolic_rejects_non_3d_axis():
    with pytest.raises(AssertionError):
        symbolic_transformation(0.1, sym.Matrix([1, 0]))
