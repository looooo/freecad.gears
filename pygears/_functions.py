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

from __future__ import division
from numpy import sin, cos, dot, array, ndarray, vstack, transpose, sqrt
from numpy.linalg import solve, norm


def reflection(angle):
    mat = array(
        [[cos(2 * angle), -sin(2 * angle)], [-sin(2 * angle), -cos(2 * angle)]])

    def func(x):
        return(dot(x, mat))
    return(func)


def reflection3D(angle):
    mat = array([[cos(2 * angle), -sin(2 * angle), 0.],
                 [-sin(2 * angle), -cos(2 * angle), 0.], [0., 0., 1.]])

    def func(x):
        return(dot(x, mat))
    return(func)


def rotation(angle, midpoint=None):
    midpoint = midpoint or [0., 0.]
    mat = array([[cos(angle), -sin(angle)],
                 [sin(angle), cos(angle)]])
    midpoint = array(midpoint)
    vec = midpoint - dot(midpoint, mat)
    trans = translation(vec)

    def func(xx):
        return(trans(dot(xx, mat)))
    return(func)


def rotation3D(angle):
    mat = array(
        [
            [cos(angle), -sin(angle), 0.],
            [sin(angle), cos(angle), 0.],
            [0., 0., 1.]])

    def func(xx):
        return(dot(xx, mat))
    return(func)


def translation(vec):
    def trans(x):
        return([x[0] + vec[0], x[1] + vec[1]])

    def func(x):
        return(array(list(map(trans, x))))
    return(func)


def trim(p1, p2, p3, p4):
    a1 = array(p1)
    a2 = array(p2)
    a3 = array(p3)
    a4 = array(p4)
    if all(a1 == a2) or all(a3 == a4):
        if all(a1 == a3):
            return(a1)
        else:
            return(False)
    elif all(a1 == a3):
        if all(a2 == a4):
            return((a1 + a2) / 2)
        else:
            return(a1)
    elif all(a1 == a4):
        if all(a2 == a3):
            return((a1 + a2) / 2)
        else:
            return(a1)
    elif all(a2 == a3) or all(a2 == a4):
        return(p2)
    try:
        g, h = solve(transpose([-a2 + a1, a4 - a3]), a1 - a3)
    except Exception as e:
        print(e)
        return(False)
    else:
        if 0. < g < 1. and 0. < h < 1.:
            return(a1 + g * (a2 - a1))
        else:
            return(False)


def trimfunc(l1, l2):
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
                return([vstack([l1, [s]]), vstack([[s], l2])])
            j0 = j
            jk += 1
        i0 = i
        ik += 1
    return(False)


def diff_norm(vec1, vec2):
    vec = array(vec2) - array(vec1)
    return norm(vec)


def nearestpts(evolv, underc):
    ik = 0
    iout = 0
    jout = 0
    outmin = 1000.
    for i in array(evolv[1:]):
        jk = 0
        for j in array(underc[1:]):
            l = diff_norm(i, j)
            if l < outmin:
                re = diff_norm(i, [0, 0])
                ru = diff_norm(j, [0, 0])
                if re > ru:
                    outmin = l
                    iout, jout = [ik, jk]
            jk += 1
        ik += 1
    return([vstack([underc[:jout], evolv[iout]]), evolv[iout:]])


def intersection_line_circle(p1, p2, r):
    """return the intersection point of a line from p1 to p2 and a sphere of radius 1 and 
    midpoint 0,0,0"""
    d = p2 - p1
    d /= norm(d)
    p_half = d.dot(p1)
    q = p1.dot(p1) - r ** 2
    t = -p_half + sqrt(p_half ** 2 - q)
    return p1 + d * t


def arc_from_points_and_center(p_1, p_2, m):
    """return 3 points (x1, x12, x2) which can be used to create the arc"""
    r = (norm(p_1 - m) + norm(p_2 - m)) / 2
    p_12l = (p_1 + p_2) / 2
    v = p_12l - m
    v /= norm(v)
    p_12 = m + v * r
    return (p_1, p_12, p_2)

    