# -*- coding: utf-8 -*-
#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

from __future__ import division
from numpy import tan, cos, sin, sqrt, arctan, pi, array, linspace, transpose, vstack, ndarray
from _functions import nearestpts, rotation, reflection, trimfunc, norm

class involute_tooth():
    def __init__(self, m=5, z=15, alpha=20 * pi / 180., clearence=0.12, shift=0.5, beta=0., undercut=False, backslash=0.01):
        self.alpha = alpha
        self.beta = beta
        self.m_n = m
        self.z = z
        self.undercut = undercut
        self.shift = shift
        self.clearence = clearence
        self.backslash = backslash
        self._calc_gear_factors()

    def _calc_gear_factors(self):
    	self.alpha_t = arctan(tan(self.alpha) / cos(self.beta))
        self.m = self.m_n / cos(self.beta)
        self.c = self.clearence * self.m_n
        self.midpoint = [0., 0.]
        self.d = self.z * self.m
        self.dw = self.m * self.z
        self.da = self.dw + 2. * self.m_n + 2. * self.shift * self.m_n
        self.df = self.dw - 2. * self.m_n - \
            2 * self.c + 2. * self.shift * self.m_n
        self.dg = self.d * cos(self.alpha_t)
        self.phipart = 2 * pi / self.z

        self.undercut_end = sqrt(-self.df ** 2 + self.da ** 2) / self.da
        self.undercut_rot = (-self.df / self.dw * tan(arctan((2 * ((self.m * pi) / 4. -
                            (self.c + self.m_n) * tan(self.alpha_t))) / self.df)))

        self.involute_end = sqrt(self.da ** 2 - self.dg ** 2) / self.dg
        self.involute_rot1 = sqrt(-self.dg ** 2 + (self.dw) ** 2) / self.dg - arctan(
            sqrt(-self.dg ** 2 + (self.dw) ** 2) / self.dg)
        self.involute_rot2 = self.m / \
            (self.d) * (pi / 2 + 2 * self.shift * tan(self.alpha_t))
        self.involute_rot = self.involute_rot1 + self.involute_rot2
        self.involute_start = 0.
        if self.dg <= self.df:
            self.involute_start = sqrt(self.df ** 2 - self.dg ** 2) / self.dg


    def undercut_points(self, num=10):
        pts = linspace(0, self.undercut_end, num=num)
        fx = self.undercut_function_x()
        x = array(map(fx, pts))
        fy = self.undercut_function_y()
        y = array(map(fy, pts))
        xy = transpose([x, y])
        rotate = rotation(
            self.undercut_rot + self.phipart / 2 - self.backslash / 4)
        xy = rotate(xy)
        return(array(xy))

    def involute_points(self, num=10):
        pts = linspace(self.involute_start, self.involute_end, num=num)
        fx = self.involute_function_x()
        x = array(map(fx, pts))
        fy = self.involute_function_y()
        y = array(map(fy, pts))
        rot = rotation(self.involute_rot - self.backslash / 4)
        xy = rot(transpose(array([x, y])))
        return(xy)

    def points(self, num=10):
        l1 = self.undercut_points(num=num)
        l2 = self.involute_points(num=num)
        s = trimfunc(l1, l2[::-1])
        if self.undercut:
            if isinstance(s, ndarray):
                u1, e1 = s
            else:
                u1, e1 = nearestpts(l2, l1)
        else:
            u1 = False
            if self.dg > self.df:
                u1 = vstack(
                    [[l2[0] * self.df / (norm(l2[0], [0, 0]) * 2)], [l2[0]]])
                e1 = l2
            else:
                e1 = l2

        reflect = reflection(0)
        e2 = reflect(e1)[::-1]
        if isinstance(u1, bool):
            u2 = False
            one_tooth = [e1, [e1[-1], e2[0]], e2]
        else:
            u2 = reflect(u1)[::-1]
            one_tooth = [u1, e1, [e1[-1], e2[0]], e2, u2]
        return(one_tooth)

    def gearfunc(self, x):
        rot = rotation(2 * x / self.dw, self.midpoint)
        return(rot)

    def undercut_function_x(self):
        def func(psi):
            return(
               cos(psi - (self.df * tan(psi)) / self.dw) * sqrt(self.df ** 2 / 4 +
                                                                (self.df ** 2 * tan(psi) ** 2) / 4.))
        return(func)

    def undercut_function_y(self):
        def func(psi):
            return(
                sin(psi - (self.df * tan(psi)) / self.dw) * sqrt(self.df ** 2 / 4 +
                                                                (self.df ** 2 * tan(psi) ** 2) / 4.))
        return(func)

    def involute_function_x(self):
        def func(phi):
            return(array(self.dg / 2 * cos(phi) + phi * self.dg / 2 * sin(phi)))
        return(func)

    def involute_function_y(self):
        def func(phi):
            return(self.dg / 2 * sin(phi) - phi * self.dg / 2 * cos(phi))
        return(func)

    def _update(self):
        self.__init__(m = self.m_n, z = self.z,
                alpha = self.alpha, clearence = self.clearence, shift = self.shift,
                beta = self.beta, undercut = self.undercut, backslash = self.backslash)

if __name__ == "__main__":
	from matplotlib import pyplot
	gear = involute_tooth(undercut=True, backslash=0.)
	x = []
	y = []
	for i in gear.points(30):
		for j in i:
			x.append(j[0])
			y.append(j[1])
	pyplot.plot(x[:-4],y[:-4])
	pyplot.show()

