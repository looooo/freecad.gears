# -*- coding: utf-8 -*-
# ***************************************************************************
# *                                                                         *
# * This program is free software: you can redistribute it and/or modify    *
# * it under the terms of the GNU General Public License as published by    *
# * the Free Software Foundation, either version 3 of the License, or       *
# * (at your option) any later version.                                     *
# *                                                                         *
# * This program is distributed in the hope that it will be useful,         *
# * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           *
# * GNU General Public License for more details.                            *
# *                                                                         *
# * You should have received a copy of the GNU General Public License       *
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.   *
# *                                                                         *
# ***************************************************************************

"""Pure geometric helpers for 2D/3D point transformations and curve trimming."""

from numpy import sin, cos, dot, array, ndarray, vstack, transpose, sqrt
from numpy.linalg import solve, norm


def reflection(angle):
    """A 2D reflection across a line through the origin.

    Args:
        angle (float): Angle of the mirror line [rad].

    Returns:
        function(points): Callable that reflects an array of 2D points.
    """
    mat = array([[cos(2 * angle), -sin(2 * angle)], [-sin(2 * angle), -cos(2 * angle)]])

    def _func(x):
        # we do not use matrix-multiplication here because this is meant to work
        # on an array of points
        return dot(x, mat)

    return _func


def reflection3D(angle):
    """A 3D reflection across a plane containing the z-axis.

    Args:
        angle (float): Angle of the mirror line in the xy-plane [rad].

    Returns:
        function(points): Callable that reflects an array of 3D points.
    """
    mat = array(
        [
            [cos(2 * angle), -sin(2 * angle), 0.0],
            [-sin(2 * angle), -cos(2 * angle), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )

    def _func(points):
        return dot(points, mat)

    return _func


def rotation(angle, center=None):
    """A 2D rotation transformation.

    Args:
        angle (float): Rotation angle [rad].
        center (sequence, optional): Center of rotation ``[x, y]``. Defaults
            to the origin.

    Returns:
        function(points): Callable that rotates an array of 2D points.
    """
    center = center or [0.0, 0.0]
    mat = array([[cos(angle), sin(angle)], [-sin(angle), cos(angle)]])
    center = array(center)
    vec = center - dot(center, mat)
    trans = translation(vec)

    def _func(points):
        return trans(dot(points, mat))

    return _func


def rotation3D(angle):
    """A 3D rotation about the z-axis.

    Args:
        angle (float): Rotation angle [rad] in the xy-plane.

    Returns:
        function(points): Callable that rotates an array of 3D points.
    """
    mat = array(
        [[cos(angle), sin(angle), 0.0], [-sin(angle), cos(angle), 0.0], [0.0, 0.0, 1.0]]
    )

    def _func(points):
        return dot(points, mat)

    return _func


def translation(vector):
    """A 2D translation transformation.

    Args:
        vector (sequence): Translation offset ``[dx, dy]``.

    Returns:
        function(points): Callable that translates an array of 2D points.
    """
    def _trans(point):
        return [point[0] + vector[0], point[1] + vector[1]]

    def _func(points):
        return array(list(map(_trans, points)))

    return _func


def trim(p1, p2, p3, p4):
    """Find the intersection point of two 2D line segments.

    Args:
        p1, p2: Endpoints of the first segment.
        p3, p4: Endpoints of the second segment.

    Returns:
        numpy.ndarray: Intersection point, an endpoint, or ``False`` if the
            segments do not intersect within their bounds.
    """
    a1 = array(p1)
    a2 = array(p2)
    a3 = array(p3)
    a4 = array(p4)
    if all(a1 == a2) or all(a3 == a4):
        if all(a1 == a3):
            return a1
        return False
    if all(a1 == a3):
        if all(a2 == a4):
            return (a1 + a2) / 2
        return a1
    if all(a1 == a4):
        if all(a2 == a3):
            return (a1 + a2) / 2
        return a1
    if all(a2 == a3) or all(a2 == a4):
        return p2
    try:
        g, h = solve(transpose([-a2 + a1, a4 - a3]), a1 - a3)
    except Exception as e:
        print(e)
        return False
    if 0.0 < g < 1.0 and 0.0 < h < 1.0:
        return a1 + g * (a2 - a1)
    return False


def trimfunc(l1, l2):
    """Trim two polylines at their first intersection.

    Args:
        l1 (sequence): First polyline as a sequence of 2D points.
        l2 (sequence): Second polyline as a sequence of 2D points.

    Returns:
        list or bool: ``[trimmed_l1, trimmed_l2]`` with both polylines ending
        at the intersection, or ``False`` if no intersection is found.
    """
    ik = 0
    i0 = array(l1[0])
    for i in array(l1[1:]):
        jk = 0
        j0 = array(l2[0])
        for j in array(l2[1:]):
            s = trim(j0, j, i0, i)
            if isinstance(s, ndarray):
                if ik == 0:
                    l1 = [l1[0]]
                else:
                    l1 = l1[:ik]
                if jk == 0:
                    l2 = [l2[0]]
                else:
                    l2 = l2[jk::-1]
                return [vstack([l1, [s]]), vstack([[s], l2])]
            j0 = j
            jk += 1
        i0 = i
        ik += 1
    return False


def diff_norm(vector_1, vector_2):
    """Return the Euclidean distance between two 2D points.

    Args:
        vector_1 (array or list): First point.
        vector_2 (array or list): Second point.

    Returns:
        float: Distance between the two points.
    """
    return norm(array(vector_2) - array(vector_1))


def nearestpts(involute, undercut):
    """Join involute and undercut polylines at their closest approach.

    Selects the pair of points with minimum distance where the involute point
    is farther from the origin than the undercut point.

    Args:
        involute (sequence): Involute flank polyline.
        undercut (sequence): Undercut polyline.

    Returns:
        list: ``[merged_undercut_to_involute, involute_from_joint]`` as stacked
            point arrays.
    """
    ik = 0
    iout = 0
    jout = 0
    outmin = 1000.0
    for i in array(involute[1:]):
        jk = 0
        for j in array(undercut[1:]):
            l = diff_norm(i, j)
            if l < outmin:
                re = diff_norm(i, [0, 0])
                ru = diff_norm(j, [0, 0])
                if re > ru:
                    outmin = l
                    iout, jout = [ik, jk]
            jk += 1
        ik += 1
    return [vstack([undercut[:jout], involute[iout]]), involute[iout:]]


def intersection_line_circle(point_1, point_2, radius):
    """Return where a ray from ``point_1`` toward ``point_2`` meets a circle.

    The circle is centered at the origin with the given radius.

    Args:
        point_1: Ray origin (2D).
        point_2: Point defining the ray direction (2D).
        radius (float): Circle radius.

    Returns:
        numpy.ndarray: Intersection point on the circle.
    """
    diff = point_2 - point_1
    diff /= norm(diff)
    p_half = diff.dot(point_1)
    q = point_1.dot(point_1) - radius ** 2
    t = -p_half + sqrt(p_half ** 2 - q)
    return point_1 + diff * t


def arc_from_points_and_center(point_1, point_2, center):
    """Return three collinear arc sample points between two endpoints.

    Args:
        point_1 (numpy.ndarray): Arc start point (2D).
        point_2 (numpy.ndarray): Arc end point (2D).
        center (numpy.ndarray): Arc center (2D).

    Returns:
        tuple: ``(point_1, point_12, point_2)`` where ``point_12`` lies on the
            arc midway between the endpoints.
    """
    r = (norm(point_1 - center) + norm(point_2 - center)) / 2
    p_12l = (point_1 + point_2) / 2
    v = p_12l - center
    v /= norm(v)
    p_12 = center + v * r
    return (point_1, p_12, point_2)
