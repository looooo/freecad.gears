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
from numpy import tan, cos, sin, sqrt, arctan, pi, array, linspace, transpose, vstack, ndarray
from ._functions import nearestpts, rotation, reflection, trimfunc, diff_norm, translation


class InvoluteTooth():
    def __init__(self, m=5, z=15, pressure_angle=20 * pi / 180., clearance=0.12, shift=0.5, beta=0.,
                 undercut=False, backlash=0.00, head=0.00, properties_from_tool=False):
        self.pressure_angle = pressure_angle
        self.beta = beta
        self.m_n = m
        self.z = z
        self.undercut = undercut
        self.shift = shift
        self.clearance = clearance
        self.backlash = backlash
        self.head = head        # factor, rename!!!
        self.properties_from_tool = properties_from_tool
        self._calc_gear_factors()

    def _calc_gear_factors(self):
        if self.properties_from_tool:
            self.pressure_angle_t = arctan(
                tan(self.pressure_angle) / cos(self.beta))
            self.m = self.m_n / cos(self.beta)
        else:
            self.pressure_angle_t = self.pressure_angle
            self.m = self.m_n

        self.pitch = self.m * pi
        self.c = self.clearance * self.m_n
        self.midpoint = [0., 0.]
        self.d = self.z * self.m
        self.dw = self.m * self.z
        self.da = self.dw + 2. * self.m_n + 2. * \
            (self.shift + self.head) * self.m_n
        self.df = self.dw - 2. * self.m_n - \
            2 * self.c + 2. * self.shift * self.m_n
        self.dg = self.d * cos(self.pressure_angle_t)
        self.phipart = 2 * pi / self.z

        self.undercut_end = sqrt(-self.df ** 2 + self.da ** 2) / self.da
        self.undercut_rot = (-self.df / self.dw * tan(arctan((2 * ((self.m * pi) / 4. -
                                                                   (self.c + self.m_n) * tan(self.pressure_angle_t))) / self.df)))

        self.involute_end = sqrt(self.da ** 2 - self.dg ** 2) / self.dg
        self.involute_rot1 = sqrt(-self.dg ** 2 + (self.dw) ** 2) / self.dg - arctan(
            sqrt(-self.dg ** 2 + (self.dw) ** 2) / self.dg)
        self.involute_rot2 = self.m / \
            (self.d) * (pi / 2 + 2 * self.shift * tan(self.pressure_angle_t))
        self.involute_rot2 = 1 / self.z * \
            (pi / 2 + 2 * self.shift * tan(self.pressure_angle_t))
        self.involute_rot = self.involute_rot1 + self.involute_rot2
        self.angular_backlash = self.backlash / (self.d / 2)
        self.involute_start = 0.
        if self.dg <= self.df:
            self.involute_start = sqrt(self.df ** 2 - self.dg ** 2) / self.dg

    def undercut_points(self, num=10):
        pts = linspace(0, self.undercut_end, num=num)
        fx = self.undercut_function_x()
        x = array(list(map(fx, pts)))
        fy = self.undercut_function_y()
        y = array(list(map(fy, pts)))
        xy = transpose([x, y])
        rotate = rotation(
            self.undercut_rot + self.phipart / 2 - self.angular_backlash / 2)
        xy = rotate(xy)
        return(array(xy))

    def involute_points(self, num=10):
        pts = linspace(self.involute_start, self.involute_end, num=num)
        fx = self.involute_function_x()
        x = array(list(map(fx, pts)))
        fy = self.involute_function_y()
        y = array(list(map(fy, pts)))
        rot = rotation(self.involute_rot - self.angular_backlash / 2)
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
                    [[l2[0] * self.df / (diff_norm(l2[0], [0, 0]) * 2)], [l2[0]]])
                e1 = l2
            else:
                e1 = l2

        reflect = reflection(0)
        e2 = reflect(e1)[::-1]
        if isinstance(u1, bool):
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
            return(self.dg / 2 * cos(phi) + phi * self.dg / 2 * sin(phi))
        return(func)

    def involute_function_y(self):
        def func(phi):
            return(self.dg / 2 * sin(phi) - phi * self.dg / 2 * cos(phi))
        return(func)

    def _update(self):
        if not hasattr(self, "properties_from_tool"):
            self.properties_from_tool = True
        self._calc_gear_factors()


class InvoluteRack(object):
    def __init__(self, m=5, z=15, pressure_angle=20 * pi / 180., thickness=5, beta=0, head=0, clearance=0.25, 
                 properties_from_tool=False, add_endings=False, simplified=False):
        self.pressure_angle = pressure_angle
        self.thickness = thickness
        self.m = m
        self.z = z
        self.beta = beta
        self.head = head
        self.clearance = clearance
        self.properties_from_tool = properties_from_tool
        self.add_endings = add_endings
        self.simplified = simplified


# this is not good. Find better way to stay backward compatible -> versions
    def _update(self):
        if not hasattr(self, "add_endings"):
            self.add_endings = True
        if not hasattr(self, "simplified"):
            self.simplified = False

    def points(self, num=10):
        import copy
        m, m_n, pitch, pressure_angle_t = self.compute_properties()

        a = (2 + self.head + self.clearance) * m_n * tan(pressure_angle_t)
        b = pitch / 4 - (1 + self.head) * m_n * tan(pressure_angle_t)
        tooth = [
            [-m_n * (1 + self.clearance), -a - b],
            [m_n * (1 + self.head), -b],
            [m_n * (1 + self.head), b],
            [-m_n * (1 + self.clearance), a + b]
        ]
        teeth = [tooth]
        trans = translation([0., pitch, 0.])
        for i in range(self.z - 1):
            if self.simplified and i > 3 and i < (self.z - 6):
                tooth = trans(tooth).tolist()
            else:
                tooth = trans(tooth).tolist()
                teeth.append(copy.deepcopy(tooth))
                if self.simplified and (i == 3):
                    teeth[-1].pop()
                    teeth[-1].pop()
                    teeth[-1][-1][0] = 0
                    teeth[-1][-1][1] -= a / 2 
                if self.simplified and (i == self.z - 6):
                    teeth[-1].pop(0)
                    teeth[-1].pop(0)
                    teeth[-1][0][0] = 0
                    teeth[-1][0][1] += a / 2

        teeth = array([v for t in teeth for v in t])  # flattening
        if self.add_endings:
            ext1 = teeth[0] + array([0., a + b - pitch / 2])
            ext2 = teeth[-1] - array([0., a + b - pitch / 2])
            teeth = [ext1.tolist(), ext1.tolist()] + teeth.tolist() + [ext2.tolist(), ext2.tolist()]
        else:
            teeth = [teeth[0].tolist()] + teeth.tolist() + [teeth[-1].tolist()]
        #teeth.append(list(teeth[-1]))
        teeth[0][0] -= self.thickness
        #teeth.append(list(teeth[0]))
        teeth[-1][0] -= self.thickness
        teeth.append(teeth[0])
        return array(teeth)

    def compute_properties(self):
        if self.properties_from_tool:
            pressure_angle_t = arctan(tan(self.pressure_angle) / cos(self.beta))
            m = self.m / cos(self.beta)
            m_n = self.m
        else:
            pressure_angle_t = self.pressure_angle
            m = self.m
            m_n  = self.m

        pitch = m * pi
        return m, m_n, pitch, pressure_angle_t
