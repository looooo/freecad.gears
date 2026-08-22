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

"""Bevel gear tooth geometry on the z=1 projection plane."""

from numpy import (
    cos,
    sin,
    tan,
    arccos,
    arctan,
    pi,
    array,
    linspace,
    transpose,
    sqrt,
)
from ._functions import rotation3D, reflection3D, intersection_line_circle


class BevelTooth(object):
    """Single bevel gear tooth in 3D, projected onto the z=1 plane."""

    def __init__(
        self,
        pressure_angle=70 * pi / 180,
        pitch_angle=pi / 4,
        clearance=0.1,
        z=21,
        backlash=0.00,
        module=0.25,
    ):
        """Initialize bevel tooth parameters and compute sampling limits.

        Args:
            pressure_angle (float): Normal pressure angle [rad].
            pitch_angle (float): Pitch cone angle [rad].
            clearance (float): Clearance factor at the root.
            z (int): Number of teeth on the bevel gear.
            backlash (float): Linear backlash at the pitch circle [length].
            module (float): Module at the large end of the tooth.
        """
        self.pressure_angle = pressure_angle
        self.pitch_angle = pitch_angle
        self.z = z
        self.clearance = clearance
        self.backlash = backlash
        self.angular_backlash = backlash / (z * module / 2)
        self.module = module

        self.involute_end = arccos(
            1
            / sqrt(2)
            * sqrt(
                (
                    42.0
                    + 16.0 * cos(2.0 * self.pressure_angle)
                    + 6.0 * cos(4.0 * self.pressure_angle)
                    + cos(4.0 * self.pressure_angle - 4.0 * self.pitch_angle)
                    - 8.0 * cos(2.0 * self.pressure_angle - 2.0 * self.pitch_angle)
                    - 4.0 * cos(4.0 * self.pressure_angle - 2.0 * self.pitch_angle)
                    + 24.0 * cos(2.0 * self.pitch_angle)
                    - 2.0 * cos(4.0 * self.pitch_angle)
                    - 8.0 * cos(2.0 * (self.pressure_angle + self.pitch_angle))
                    + cos(4.0 * (self.pressure_angle + self.pitch_angle))
                    - 4.0 * cos(4.0 * self.pressure_angle + 2.0 * self.pitch_angle)
                    + 24.0 * cos((4.0 * sin(self.pitch_angle)) / self.z)
                    + 4.0
                    * cos(
                        2.0 * self.pressure_angle
                        - (4.0 * sin(self.pitch_angle)) / self.z
                    )
                    + 4.0
                    * cos(
                        2.0 * self.pressure_angle
                        - 4.0 * self.pitch_angle
                        - (4.0 * sin(self.pitch_angle)) / self.z
                    )
                    - 8.0
                    * cos(
                        2.0 * self.pressure_angle
                        - 2.0 * self.pitch_angle
                        - (4.0 * sin(self.pitch_angle)) / self.z
                    )
                    + 24.0
                    * cos(4.0 * (self.pitch_angle + sin(self.pitch_angle) / self.z))
                    - 8.0
                    * cos(
                        2.0
                        * (
                            self.pressure_angle
                            + self.pitch_angle
                            + (2.0 * sin(self.pitch_angle)) / self.z
                        )
                    )
                    + 4.0
                    * cos(
                        2.0 * self.pressure_angle
                        + (4.0 * sin(self.pitch_angle)) / self.z
                    )
                    + 16.0
                    * cos(
                        2.0 * self.pitch_angle + (4.0 * sin(self.pitch_angle)) / self.z
                    )
                    + 4.0
                    * cos(
                        2.0 * self.pressure_angle
                        + 4.0 * self.pitch_angle
                        + (4.0 * sin(self.pitch_angle)) / self.z
                    )
                    + 32.0
                    * abs(
                        cos(self.pitch_angle + (2.0 * sin(self.pitch_angle)) / self.z)
                    )
                    * cos(self.pressure_angle)
                    * sqrt(
                        4.0 * cos(2.0 * self.pressure_angle)
                        - 2.0
                        * (
                            -2.0
                            + cos(2.0 * self.pressure_angle - 2.0 * self.pitch_angle)
                            - 2.0 * cos(2.0 * self.pitch_angle)
                            + cos(2.0 * (self.pressure_angle + self.pitch_angle))
                            + 4.0
                            * cos(
                                2.0 * self.pitch_angle
                                + (4.0 * sin(self.pitch_angle)) / self.z
                            )
                        )
                    )
                    * sin(2.0 * self.pitch_angle)
                )
                / (
                    -6.0
                    - 2.0 * cos(2.0 * self.pressure_angle)
                    + cos(2.0 * self.pressure_angle - 2.0 * self.pitch_angle)
                    - 2.0 * cos(2.0 * self.pitch_angle)
                    + cos(2.0 * (self.pressure_angle + self.pitch_angle))
                )
                ** 2
            )
        )

        self.involute_start = -pi / 2.0 + arctan(
            1 / tan(self.pitch_angle) * 1 / cos(self.pressure_angle)
        )
        self.involute_start_radius = self.get_radius(self.involute_start)
        self.r_f = sin(
            self.pitch_angle - sin(pitch_angle) * 2 / self.z
        ) - self.clearance * sin(self.pitch_angle)
        self.z_f = cos(self.pitch_angle - sin(pitch_angle) * 2 / self.z)
        self.add_foot = True

    def involute_function_x(self):
        """Return the x-component of the spherical involute parameterization."""
        def func(s):
            return -(
                cos(s * 1 / sin(self.pressure_angle) * 1 / sin(self.pitch_angle))
                * sin(self.pressure_angle)
                * sin(s)
            ) + (
                cos(s) * sin(self.pitch_angle)
                + cos(self.pressure_angle) * cos(self.pitch_angle) * sin(s)
            ) * sin(s * 1 / sin(self.pressure_angle) * 1 / sin(self.pitch_angle))

        return func

    def involute_function_y(self):
        """Return the y-component of the spherical involute parameterization."""
        def func(s):
            return cos(s * 1 / sin(self.pressure_angle) * 1 / sin(self.pitch_angle)) * (
                cos(s) * sin(self.pitch_angle)
                + cos(self.pressure_angle) * cos(self.pitch_angle) * sin(s)
            ) + sin(self.pressure_angle) * sin(s) * sin(
                s * 1 / sin(self.pressure_angle) * 1 / sin(self.pitch_angle)
            )

        return func

    def involute_function_z(self):
        """Return the z-component of the spherical involute parameterization."""
        def func(s):
            return cos(self.pitch_angle) * cos(s) - cos(self.pressure_angle) * sin(
                self.pitch_angle
            ) * sin(s)

        return func

    def get_radius(self, s):
        """Return the radial distance from the axis at parameter ``s``.

        Args:
            s (float): Involute parameter.

        Returns:
            float: Radius in the xy-plane before conical projection.
        """
        x = self.involute_function_x()
        y = self.involute_function_y()
        rx = x(s)
        ry = y(s)
        return sqrt(rx**2 + ry**2)

    def involute_points(self, num=10):
        """Sample one involute flank, project to z=1 and trim at the root.

        Args:
            num (int): Number of sample points along the involute.

        Returns:
            list: 3D points ``[x, y, 1]`` on the z=1 projection plane.
        """
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
            if point.dot(point) >= r_cut**2:
                break
        if i > 0:
            self.add_foot = False
        intersection_point = intersection_line_circle(xy[i], point, r_cut)
        xy = array([intersection_point] + list(xy[i + 1 :]))
        xyz = [[p[0], p[1], 1] for p in xy]
        backlash_rot = rotation3D(-self.angular_backlash / 2)
        xyz = backlash_rot(xyz)
        return xyz

    def points(self, num=10):
        """Build the wire segments of one complete bevel tooth.

        Args:
            num (int): Number of sample points per involute segment.

        Returns:
            list: Wire segments, each a numpy array of 3D points on z=1.
        """
        pts = self.involute_points(num=num)
        rot = rotation3D(pi / self.z / 2)
        pts = rot(pts)
        ref = reflection3D(pi / 2)
        pts1 = ref(pts)[::-1]
        if self.add_foot:
            return [
                array([pts[0], pts[1]]),
                array(pts[1:]),
                array([pts[-1], pts1[0]]),
                array(pts1[:-1]),
                array([pts1[-2], pts1[-1]]),
            ]
        return [pts, array([pts[-1], pts1[0]]), pts1]

    def _update(self):
        """Recalculate tooth geometry after a parameter change."""
        self.__init__(  # pylint: disable=unnecessary-dunder-call
            z=self.z,
            clearance=self.clearance,
            pressure_angle=self.pressure_angle,
            pitch_angle=self.pitch_angle,
            backlash=self.backlash,
            module=self.module,
        )
