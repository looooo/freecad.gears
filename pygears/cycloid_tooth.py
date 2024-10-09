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

from numpy import cos, sin, arccos, pi, array, linspace, transpose, vstack
from ._functions import rotation, reflection


class CycloidTooth:
    def __init__(self, num_teeth_1=5, num_teeth_2=5, num_teeth=14, m=5, clearance=0.25, backlash=0.00, head=0.0):
        self.m = m
        self.num_teeth = num_teeth
        self.clearance = clearance
        self.backlash = backlash
        self.num_teeth_1 = num_teeth_1
        self.num_teeth_2 = num_teeth_2
        self.head = head
        self._calc_gear_factors()

    def _calc_gear_factors(self):
        self.d1 = self.num_teeth_1 * self.m
        self.d2 = self.num_teeth_2 * self.m
        self.phi = self.m * pi
        self.d = self.num_teeth * self.m
        self.da = self.d + 2 * (1 + self.head) * self.m
        self.di = self.d - 2 * (1 + self.clearance) * self.m
        self.phipart = 2 * pi / self.num_teeth
        self.angular_backlash = self.backlash / (self.d / 2)

    def epicycloid_x(self):
        def func(t):
            return ((self.d2 + self.d) * cos(t)) / 2.0 - (
                self.d2 * cos((1 + self.d / self.d2) * t)
            ) / 2.0

        return func

    def epicycloid_y(self):
        def func(t):
            return ((self.d2 + self.d) * sin(t)) / 2.0 - (
                self.d2 * sin((1 + self.d / self.d2) * t)
            ) / 2.0

        return func

    def hypocycloid_x(self):
        def func(t):
            return (self.d - self.d1) * cos(t) / 2 + self.d1 / 2 * cos(
                (self.d / self.d1 - 1) * t
            )

        return func

    def hypocycloid_y(self):
        def func(t):
            return (self.d - self.d1) * sin(t) / 2 - self.d1 / 2 * sin(
                (self.d / self.d1 - 1) * t
            )

        return func

    def inner_end(self):
        return -(
            (
                self.d1
                * arccos(
                    (2 * self.d1**2 - self.di**2 - 2 * self.d1 * self.d + self.d**2)
                    / (2.0 * self.d1 * (self.d1 - self.d))
                )
            )
            / self.d
        )

    def outer_end(self):
        return (
            self.d2
            * arccos(
                (2 * self.d2**2 - self.da**2 + 2 * self.d2 * self.d + self.d**2)
                / (2.0 * self.d2 * (self.d2 + self.d))
            )
        ) / self.d

    def points(self, num=10):
        inner_x = self.hypocycloid_x()
        inner_y = self.hypocycloid_y()
        outer_x = self.epicycloid_x()
        outer_y = self.epicycloid_y()
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
        rot = rotation(-self.phipart / 4 + self.angular_backlash / 2)
        pts1 = rot(pts1)
        ref = reflection(0.0)
        pts2 = ref(pts1)[::-1]
        one_tooth = [pts1, array([pts1[-1], pts2[0]]), pts2]
        return one_tooth

    def _update(self):
        self.__init__(
            m=self.m,
            num_teeth=self.num_teeth,
            num_teeth_1=self.num_teeth_1,
            num_teeth_2=self.num_teeth_2,
            clearance=self.clearance,
            backlash=self.backlash,
            head=self.head,
        )
