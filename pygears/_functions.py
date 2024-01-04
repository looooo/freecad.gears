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

from numpy import sin, cos, dot, array, ndarray, vstack, transpose, sqrt
from numpy.linalg import solve, norm


def reflection(angle):
    """A 2d reflection- / mirror- transformation 

    Args:
        angle (float): the angle of the line which mirrors the points.

    Returns:
        function(points): the function can be used to transform an array of points (2d)
    """
    mat = array([[cos(2 * angle), -sin(2 * angle)], [-sin(2 * angle), -cos(2 * angle)]])

    def _func(x):
        # we do not use matrix-multiplication here because this is meant to work
        # on an array of points
        return dot(x, mat)

    return _func


def reflection3D(angle):
    """A 3d reflection- / mirror- transformation 

    Args:
        angle (float): the angle of the line which mirrors the points. The transformation
        happens in xy-plane.

    Returns:
        function(points): the function can be used to transform an array of points (3d)
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
    """A 2d rotation - transformation 

    Args:
        angle (float): the angle of the rotation.
        center (2d array): 

    Returns:
        function(points): the function can be used to transform an array of points (3d)
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
    """A 3d rotation - transformation 

    Args:
        angle (float): the angle of the line which mirrors the points. The transformation
        happens in xy-plane.

    Returns:
        function(points): the function can be used to transform an array of points (3d)
    """
    mat = array(
        [[cos(angle), sin(angle), 0.0], [-sin(angle), cos(angle), 0.0], [0.0, 0.0, 1.0]]
    )

    def _func(points):
        return dot(points, mat)

    return _func


def translation(vector):
    """A 2d translation - transformation 

    Args:
        angle (float): the angle of the line which mirrors the points. The transformation
        happens in xy-plane.

    Returns:
        function(points): the function can be used to transform an array of points (3d)
    """
    def _trans(point):
        return [point[0] + vector[0], point[1] + vector[1]]

    def _func(points):
        return array(list(map(_trans, points)))

    return _func


def trim(p1, p2, p3, p4):
    """ a trim function, needs to be documented

    Args:
        p1 (array or list of length 2): _description_
        p2 (array or list of length 2): _description_
        p3 (array or list of length 2): _description_
        p4 (array or list of length 2): _description_

    Returns:
        _type_: _description_
    """
    a1 = array(p1)
    a2 = array(p2)
    a3 = array(p3)
    a4 = array(p4)
    if all(a1 == a2) or all(a3 == a4):
        if all(a1 == a3):
            return a1
        else:
            return False
    elif all(a1 == a3):
        if all(a2 == a4):
            return (a1 + a2) / 2
        else:
            return a1
    elif all(a1 == a4):
        if all(a2 == a3):
            return (a1 + a2) / 2
        else:
            return a1
    elif all(a2 == a3) or all(a2 == a4):
        return p2
    try:
        g, h = solve(transpose([-a2 + a1, a4 - a3]), a1 - a3)
    except Exception as e:
        print(e)
        return False
    else:
        if 0.0 < g < 1.0 and 0.0 < h < 1.0:
            return a1 + g * (a2 - a1)
        else:
            return False


def trimfunc(l1, l2):
    """seems like a trimm function, but I don't have any clue what it does,
       sry ;)

    Args:
        l1 (_type_): _description_
        l2 (_type_): _description_

    Returns:
        _type_: _description_
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
                    l2 == [l2[0]]
                else:
                    l2 = l2[jk::-1]
                return [vstack([l1, [s]]), vstack([[s], l2])]
            j0 = j
            jk += 1
        i0 = i
        ik += 1
    return False


def diff_norm(vector_1, vector_2):
    """_summary_

    Args:
        vector_1 (np.array or list): the first vector
        vector_2 (np.array or list): the second vector

    Returns:
        float: the length of the distance between the two vectors
    """
    return norm(array(vector_2) - array(vector_1))


def nearestpts(involute, undercut):
    """finds the closest points of a involute and an undercutut

    Args:
        involute (array or list of 2d points ?): the involute section of the tooth
        undercut (array or list of 2d points ?): the undercut section of the tooth

    Returns:
        list of arrays: ????
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
    """return the intersection point of a line from point_1 to point_2 and a sphere of radius 1 and
    midpoint 0,0,0

    Args:
        point_1 (_type_): start of line
        point_2 (_type_): end of line
        radius (float): the radius of the sphere

    Returns:
        _type_: _description_
    """
    diff = point_2 - point_1
    diff /= norm(diff)
    p_half = diff.dot(point_1)
    q = point_1.dot(point_1) - radius ** 2
    t = -p_half + sqrt(p_half ** 2 - q)
    return point_1 + diff * t


def arc_from_points_and_center(point_1, point_2, center):
    """
    returns 3 points (point_1, point_12, point_2) which are on the arc with
    given center

    Args:
        point_1 (np.array with length 2): the start point of the arc
        point_2 (np.array with length 2): the end point of the arc
        center (np.array with length 2): the center of the arc

    Returns:
        [point_1, point_12, point_2]: returns the input points + the computed point
        which is on the arc and between the input points
    """
    r = (norm(point_1 - center) + norm(point_2 - center)) / 2
    p_12l = (point_1 + point_2) / 2
    v = p_12l - center
    v /= norm(v)
    p_12 = center + v * r
    return (point_1, p_12, point_2)
