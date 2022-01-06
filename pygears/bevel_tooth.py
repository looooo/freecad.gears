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
from __future__ import division
from numpy import cos, sin, tan, arccos, arctan, pi, array, linspace, transpose, vstack, sqrt
from ._functions import rotation3D, reflection3D, intersection_line_circle


class BevelTooth(object):
    def __init__(self, pressure_angle=70 * pi / 180, pitch_angle=pi / 4, clearance=0.1,
                 z=21, backlash=0.00, module=0.25):
        self.pressure_angle = pressure_angle
        self.pitch_angle = pitch_angle
        self.z = z
        self.clearance = clearance
        self.backlash = backlash
        self.angular_backlash = backlash / (z * module / 2)
        self.module = module

        self.involute_end = arccos(
            1 / sqrt(2) * sqrt((42. + 16.*cos(2.*self.pressure_angle) +
                                6.*cos(4.*self.pressure_angle) + cos(4.*self.pressure_angle - 4.*self.pitch_angle) - 8.*cos(2.*self.pressure_angle - 2.*self.pitch_angle) -
                                4.*cos(4.*self.pressure_angle - 2.*self.pitch_angle) + 24.*cos(2.*self.pitch_angle) - 2.*cos(4.*self.pitch_angle) -
                                8.*cos(2.*(self.pressure_angle + self.pitch_angle)) + cos(4.*(self.pressure_angle + self.pitch_angle)) -
                                4.*cos(4.*self.pressure_angle + 2.*self.pitch_angle) + 24.*cos((4.*sin(self.pitch_angle))/self.z) +
                                4.*cos(2.*self.pressure_angle - (4.*sin(self.pitch_angle))/self.z) + 4.*cos(2.*self.pressure_angle -
                                                                                                            4.*self.pitch_angle - (4.*sin(self.pitch_angle))/self.z) - 8.*cos(2.*self.pressure_angle - 2.*self.pitch_angle -
                                                                                                                                                                              (4.*sin(self.pitch_angle))/self.z) + 24.*cos(4.*(self.pitch_angle + sin(self.pitch_angle)/self.z)) -
                                8.*cos(2.*(self.pressure_angle + self.pitch_angle + (2.*sin(self.pitch_angle))/self.z)) + 4.*cos(2.*self.pressure_angle +
                                                                                                                                 (4.*sin(self.pitch_angle))/self.z) + 16.*cos(2.*self.pitch_angle + (4.*sin(self.pitch_angle))/self.z) +
                                4.*cos(2.*self.pressure_angle + 4.*self.pitch_angle + (4.*sin(self.pitch_angle))/self.z) + 32.*abs(cos(self.pitch_angle +
                                                                                                                                       (2.*sin(self.pitch_angle))/self.z))*cos(self.pressure_angle)*sqrt(4.*cos(2.*self.pressure_angle) -
                                                                                                                                                                                                         2.*(-2. + cos(2.*self.pressure_angle - 2.*self.pitch_angle) - 2.*cos(2.*self.pitch_angle) + cos(2.*(self.pressure_angle + self.pitch_angle)) +
                                                                                                                                                                                                             4.*cos(2.*self.pitch_angle + (4.*sin(self.pitch_angle))/self.z)))*sin(2.*self.pitch_angle))/(-6. - 2.*cos(2.*self.pressure_angle) +
                                                                                                                                                                                                                                                                                                          cos(2.*self.pressure_angle - 2.*self.pitch_angle) - 2.*cos(2.*self.pitch_angle) + cos(2.*(self.pressure_angle + self.pitch_angle)))**2))

        self.involute_start = -pi/2. + \
            arctan(1/tan(self.pitch_angle)*1/cos(self.pressure_angle))
        self.involute_start_radius = self.get_radius(self.involute_start)
        self.r_f = sin(self.pitch_angle - sin(pitch_angle) * 2 /
                       self.z) - self.clearance * sin(self.pitch_angle)
        self.z_f = cos(self.pitch_angle - sin(pitch_angle) * 2 / self.z)
        self.add_foot = True

    def involute_function_x(self):
        def func(s):
            return((
                -(cos(s*1/sin(self.pressure_angle)*1/sin(self.pitch_angle))*sin(self.pressure_angle)*sin(s)) +
                (cos(s)*sin(self.pitch_angle) + cos(self.pressure_angle)*cos(self.pitch_angle)*sin(s)) *
                sin(s*1/sin(self.pressure_angle)*1/sin(self.pitch_angle))))
        return(func)

    def involute_function_y(self):
        def func(s):
            return((
                cos(s*1/sin(self.pressure_angle)*1/sin(self.pitch_angle))*(cos(s)*sin(self.pitch_angle) +
                                                                           cos(self.pressure_angle)*cos(self.pitch_angle)*sin(s)) + sin(self.pressure_angle)*sin(s) *
                sin(s*1/sin(self.pressure_angle)*1/sin(self.pitch_angle))))
        return(func)

    def involute_function_z(self):
        def func(s):
            return((
                cos(self.pitch_angle)*cos(s) - cos(self.pressure_angle)*sin(self.pitch_angle)*sin(s)))
        return(func)

    def get_radius(self, s):
        x = self.involute_function_x()
        y = self.involute_function_y()
        rx = x(s)
        ry = y(s)
        return(sqrt(rx**2 + ry**2))

    def involute_points(self, num=10):
        pts = linspace(self.involute_start, self.involute_end, num=num)
        fx = self.involute_function_x()
        x = array(list(map(fx, pts)))
        fy = self.involute_function_y()
        y = array(list(map(fy, pts)))
        fz = self.involute_function_z()
        z = array(list(map(fz, pts)))
        xyz = transpose(array([x, y, z]))
        # conical projection to z=1
        xy = [[i[0] / i[2], i[1] / i[2]] for i in xyz]
        xy = array([[0, 0]] + xy)

        r_cut = self.r_f / self.z_f
        for i, point in enumerate(xy[1:]):
            if point.dot(point) >= r_cut ** 2:
                break
        if i > 0:
            self.add_foot = False
        intersection_point = intersection_line_circle(xy[i], point, r_cut)
        xy = array([intersection_point] + list(xy[i+1:]))
        xyz = [[p[0], p[1], 1] for p in xy]
        backlash_rot = rotation3D(self.angular_backlash / 2)
        xyz = backlash_rot(xyz)
        return(xyz)

    def points(self, num=10):
        pts = self.involute_points(num=num)
        rot = rotation3D(-pi/self.z/2)
        pts = rot(pts)
        ref = reflection3D(pi/2)
        pts1 = ref(pts)[::-1]
        if self.add_foot:
            return([
                array([pts[0], pts[1]]),
                array(pts[1:]),
                array([pts[-1], pts1[0]]),
                array(pts1[:-1]),
                array([pts1[-2], pts1[-1]])
            ])
        else:
            return([pts, array([pts[-1], pts1[0]]), pts1])

    def _update(self):
        self.__init__(z=self.z, clearance=self.clearance,
                      pressure_angle=self.pressure_angle,
                      pitch_angle=self.pitch_angle,
                      backlash=self.backlash, module=self.module)
