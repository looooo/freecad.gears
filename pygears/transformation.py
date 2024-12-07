import sympy as sym
import numpy as np

def symbolic_transformation(angle, axis, translation=np.array([0., 0., 0.])):
    """
        see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations
        sympy enabled transformation
        angle: angle of rotation
        axis: the axis of the rotation
        translation: translation of transformation
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
    """
        see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations
        angle: angle of rotation
        axis: the axis of the rotation
        translation: translation of transformation
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