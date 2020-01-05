# -*- coding: utf-8 -*-
# ***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

from __future__ import division
from numpy import cos, sin, arccos, pi, array, linspace, transpose, vstack
from ._functions import rotation, reflection


class CycloideTooth():
    def __init__(self, z1=5, z2=5, z=14, m=5, clearance=0.12, backlash=0.00):
        self.m = m
        self.z = z
        self.clearance = clearance
        self.backlash = backlash
        self.z1 = z1
        self.z2 = z2
        self._calc_gear_factors()

    def _calc_gear_factors(self):
        self.d1 = self.z1 * self.m
        self.d2 = self.z2 * self.m
        self.phi = self.m * pi
        self.d = self.z * self.m
        self.da = self.d + 2*self.m
        self.di = self.d - 2*self.m - self.clearance * self.m
        self.phipart = 2 * pi / self.z

    def epicycloide_x(self):
        def func(t):
            return(((self.d2 + self.d) * cos(t))/2. - (self.d2 * cos((1 + self.d / self.d2) * t))/2.)
        return(func)

    def epicycloide_y(self):
        def func(t):
            return(((self.d2 + self.d) * sin(t))/2. - (self.d2 * sin((1 + self.d / self.d2) * t))/2.)
        return(func)

    def hypocycloide_x(self):
        def func(t):
            return((self.d - self.d1)*cos(t)/2 + self.d1/2 * cos((self.d / self.d1 - 1) * t))
        return(func)

    def hypocycloide_y(self):
        def func(t):
            return((self.d - self.d1)*sin(t)/2 - self.d1/2 * sin((self.d/self.d1 - 1)*t))
        return(func)

    def inner_end(self):
        return(
            -((self.d1*arccos((2*self.d1**2 - self.di**2 -
                               2*self.d1*self.d + self.d**2)/(2.*self.d1 *
                                                              (self.d1 - self.d))))/self.d)
        )

    def outer_end(self):
        return(
            (self.d2*arccos((2*self.d2**2 - self.da**2 +
                             2*self.d2*self.d + self.d**2) /
                            (2.*self.d2*(self.d2 + self.d))))/self.d
        )

    def points(self, num=10):

        inner_x = self.hypocycloide_x()
        inner_y = self.hypocycloide_y()
        outer_x = self.epicycloide_x()
        outer_y = self.epicycloide_y()
        t_inner_end = self.inner_end()
        t_outer_end = self.outer_end()
        t_vals_outer = linspace(0, t_outer_end, num)
        t_vals_inner = linspace(t_inner_end, 0, num)
        pts_outer_x = list(map(outer_x, t_vals_outer))
        pts_outer_y = list(map(outer_y, t_vals_outer))
        pts_inner_x = list(map(inner_x, t_vals_inner))
        pts_inner_y = list(map(inner_y, t_vals_inner))
        pts_outer = transpose([pts_outer_x, pts_outer_y])
        pts_inner = transpose([pts_inner_x, pts_inner_y])
        pts1 = vstack([pts_inner[:-2], pts_outer])
        rot = rotation(self.phipart / 4 - self.backlash)
        pts1 = rot(pts1)
        ref = reflection(0.)
        pts2 = ref(pts1)[::-1]
        one_tooth = [pts1, array([pts1[-1], pts2[0]]), pts2]
        return(one_tooth)

    def _update(self):
        self.__init__(m=self.m, z=self.z, z1=self.z1, z2=self.z2,
                      clearance=self.clearance, backlash=self.backlash)


if __name__ == "__main__":
    from matplotlib import pyplot
    gear = CycloideTooth()
    x = []
    y = []
    for i in gear.points(30):
        for j in i:
            x.append(j[0])
            y.append(j[1])
    pyplot.plot(x[-60:], y[-60:])
    pyplot.show()
