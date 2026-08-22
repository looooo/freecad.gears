"""Rigid-body transformations in symbolic and numeric form."""

import sympy as sym
import numpy as np

def symbolic_transformation(angle, axis, translation=np.array([0., 0., 0.])):
    """Build a 4x4 homogeneous transform matrix using sympy.

    Uses the Euler-Rodrigues formula for 3D rotation. See
    https://en.wikipedia.org/wiki/SO(4)#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations

    Args:
        angle (float): Rotation angle [rad].
        axis (sequence): Rotation axis vector (length 3).
        translation (numpy.ndarray): Translation vector (length 3).

    Returns:
        sympy.Matrix: 4x4 homogeneous transformation matrix.
    """
    assert len(axis) == 3
    a = sym.cos(angle / 2)
    axis_normalized = axis / sym.sqrt(axis.dot(axis))
    (b, c, d) = -axis_normalized * sym.sin(angle / 2)
    mat = sym.Matrix(
        [
            [
                a**2 + b**2 - c**2 - d**2,
                2 * (b * c - a * d),
                2 * (b * d + a * c),
                translation[0],
            ],
            [
                2 * (b * c + a * d),
                a**2 + c**2 - b**2 - d**2,
                2 * (c * d - a * b),
                translation[1],
            ],
            [
                2 * (b * d - a * c),
                2 * (c * d + a * b),
                a**2 + d**2 - b**2 - c**2,
                translation[2],
            ],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    return sym.simplify(mat)

def numeric_transformation(angle, axis, translation=np.array([0., 0., 0.])):
    """Build a 4x4 homogeneous transform matrix as a numpy array.

    Uses the Euler-Rodrigues formula for 3D rotation. See
    https://en.wikipedia.org/wiki/SO(4)#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations

    Args:
        angle (float): Rotation angle [rad].
        axis (sequence): Rotation axis vector (length 3).
        translation (numpy.ndarray): Translation vector (length 3).

    Returns:
        numpy.ndarray: 4x4 homogeneous transformation matrix.
    """
    assert len(axis) == 3
    a = np.cos(angle / 2)
    axis_normalized = axis / np.sqrt(axis.dot(axis))
    (b, c, d) = -axis_normalized * np.sin(angle / 2)
    mat = np.array(
        [
            [
                a**2 + b**2 - c**2 - d**2,
                2 * (b * c - a * d),
                2 * (b * d + a * c),
                translation[0],
            ],
            [
                2 * (b * c + a * d),
                a**2 + c**2 - b**2 - d**2,
                2 * (c * d - a * b),
                translation[1],
            ],
            [
                2 * (b * d - a * c),
                2 * (c * d + a * b),
                a**2 + d**2 - b**2 - c**2,
                translation[2],
            ],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    return mat
