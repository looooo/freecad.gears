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

"""Involute tooth and rack geometry for spur and helical gears."""

from numpy import (
    tan,
    cos,
    sin,
    sqrt,
    arctan,
    pi,
    array,
    linspace,
    transpose,
    vstack,
    ndarray,
)
from ._functions import (
    nearestpts,
    rotation,
    reflection,
    trimfunc,
    diff_norm,
    translation,
)


class InvoluteTooth:
    """Single involute tooth geometry for a spur or helical gear."""

    def __init__(
        self,
        m=5,
        num_teeth=15,
        pressure_angle=20 * pi / 180.0,
        clearance=0.12,
        shift=0.5,
        beta=0.0,
        undercut=False,
        backlash=0.00,
        head=0.00,
        properties_from_tool=False,
        axle_hole=False,
        axle_holesize=10,
        offset_hole=False,
        offset_holesize=10,
        offset_holeoffset = 5,
    ):
        """Initialize involute tooth parameters and compute gear dimensions.

        Args:
            m (float): Normal module.
            num_teeth (int): Number of teeth on the gear.
            pressure_angle (float): Normal pressure angle [rad].
            clearance (float): Clearance factor (multiplied by module).
            shift (float): Profile shift coefficient.
            beta (float): Helix angle [rad]; 0 for spur gears.
            undercut (bool): Whether to include undercut geometry.
            backlash (float): Linear backlash at the pitch circle [length].
            head (float): Addendum factor (extra tooth height).
            properties_from_tool (bool): If True, interpret ``m`` and
                ``pressure_angle`` as normal-system tool values.
            axle_hole (bool): Reserved for CAD features (not used here).
            axle_holesize (float): Reserved for CAD features (not used here).
            offset_hole (bool): Reserved for CAD features (not used here).
            offset_holesize (float): Reserved for CAD features (not used here).
            offset_holeoffset (float): Reserved for CAD features (not used here).
        """
        self.pressure_angle = pressure_angle
        self.beta = beta
        self.m_n = m
        self.num_teeth = num_teeth
        self.undercut = undercut
        self.axle_hole = axle_hole
        self.axle_holesize = axle_holesize
        self.offset_hole = offset_hole
        self.offset_holesize = offset_holesize
        self.offset_holeoffset = offset_holeoffset
        self.undercut = undercut
        self.shift = shift
        self.clearance = clearance
        self.backlash = backlash
        self.head = head  # factor, rename!!!
        self.properties_from_tool = properties_from_tool
        self._calc_gear_factors()

    def _calc_gear_factors(self):
        """Compute derived diameters, angles and sampling limits."""
        if self.properties_from_tool:
            self.pressure_angle_t = arctan(tan(self.pressure_angle) / cos(self.beta))
            self.m = self.m_n / cos(self.beta)
        else:
            self.pressure_angle_t = self.pressure_angle
            self.m = self.m_n

        self.pitch = self.m * pi
        self.c = self.clearance * self.m_n
        self.midpoint = [0.0, 0.0]
        self.d = self.num_teeth * self.m
        self.dw = self.m * self.num_teeth
        self.da = self.dw + 2.0 * self.m_n + 2.0 * (self.shift + self.head) * self.m_n
        self.df = self.dw - 2.0 * self.m_n - 2 * self.c + 2.0 * self.shift * self.m_n
        self.dg = self.d * cos(self.pressure_angle_t)
        self.phipart = 2 * pi / self.num_teeth

        self.undercut_end = sqrt(-(self.df**2) + self.da**2) / self.da
        self.undercut_rot = (
            -self.df
            / self.dw
            * tan(
                arctan(
                    (
                        2
                        * (
                            (self.m * pi) / 4.0
                            - (self.c + self.m_n) * tan(self.pressure_angle_t)
                        )
                    )
                    / self.df
                )
            )
        )

        self.involute_end = sqrt(self.da**2 - self.dg**2) / self.dg
        self.involute_rot1 = sqrt(-(self.dg**2) + (self.dw) ** 2) / self.dg - arctan(
            sqrt(-(self.dg**2) + (self.dw) ** 2) / self.dg
        )
        if self.properties_from_tool:
            # normal system: tool is shifted by x*m_n. In the transverse plane the
            # tooth-thickness term carries x*cos(beta) (== x_t), see KHK eq. 6-11.
            self.involute_rot2 = 1 / self.num_teeth * (
                pi / 2 + 2 * self.shift * cos(self.beta) * tan(self.pressure_angle_t)
            )
        else:
            # transverse/radial system: shift is already the transverse coefficient.
            self.involute_rot2 = 1 / self.num_teeth * (
                pi / 2 + 2 * self.shift * tan(self.pressure_angle_t)
            )
        self.involute_rot = self.involute_rot1 + self.involute_rot2
        self.angular_backlash = self.backlash / (self.d / 2)
        self.involute_start = 0.0
        if self.dg <= self.df:
            self.involute_start = sqrt(self.df**2 - self.dg**2) / self.dg

    def undercut_points(self, num=10):
        """Sample the trochoidal undercut curve on one flank.

        Args:
            num (int): Number of sample points.

        Returns:
            numpy.ndarray: Undercut points as ``(num, 2)`` array.
        """
        pts = linspace(0, self.undercut_end, num=num)
        fx = self.undercut_function_x()
        x = array(list(map(fx, pts)))
        fy = self.undercut_function_y()
        y = array(list(map(fy, pts)))
        xy = transpose([x, y])
        rotate = rotation(
            -self.undercut_rot - self.phipart / 2 + self.angular_backlash / 2
        )
        xy = rotate(xy)
        return array(xy)

    def involute_points(self, num=10):
        """Sample the involute flank from root to tip.

        Args:
            num (int): Number of sample points.

        Returns:
            numpy.ndarray: Involute points as ``(num, 2)`` array.
        """
        pts = linspace(self.involute_start, self.involute_end, num=num)
        fx = self.involute_function_x()
        x = array(list(map(fx, pts)))
        fy = self.involute_function_y()
        y = array(list(map(fy, pts)))
        rot = rotation(-self.involute_rot + self.angular_backlash / 2)
        xy = rot(transpose(array([x, y])))
        return xy

    def points(self, num=10):
        """Build the wire segments of one complete tooth.

        Args:
            num (int): Number of sample points per involute/undercut segment.

        Returns:
            list: Wire segments, each a numpy array of 2D points. Segments
                include flanks and connecting edges between them.
        """
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
                    [[l2[0] * self.df / (diff_norm(l2[0], [0, 0]) * 2)], [l2[0]]]
                )
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
        return one_tooth

    def undercut_function_x(self):
        """Return the x-component of the trochoid parameterization."""
        def func(psi):
            return cos(psi - (self.df * tan(psi)) / self.dw) * sqrt(
                self.df**2 / 4 + (self.df**2 * tan(psi) ** 2) / 4.0
            )

        return func

    def undercut_function_y(self):
        """Return the y-component of the trochoid parameterization."""
        def func(psi):
            return sin(psi - (self.df * tan(psi)) / self.dw) * sqrt(
                self.df**2 / 4 + (self.df**2 * tan(psi) ** 2) / 4.0
            )

        return func

    def involute_function_x(self):
        """Return the x-component of the involute parameterization."""
        def func(phi):
            return self.dg / 2 * cos(phi) + phi * self.dg / 2 * sin(phi)

        return func

    def involute_function_y(self):
        """Return the y-component of the involute parameterization."""
        def func(phi):
            return self.dg / 2 * sin(phi) - phi * self.dg / 2 * cos(phi)

        return func

    def _update(self):
        """Recalculate gear factors after loading from an older file version."""
        if not hasattr(self, "properties_from_tool"):
            self.properties_from_tool = True
        self._calc_gear_factors()


class InvoluteRack(object):
    """Involute rack geometry (linear teeth along the y-axis)."""

    def __init__(
        self,
        m=5,
        num_teeth=15,
        pressure_angle=20 * pi / 180.0,
        thickness=5,
        beta=0,
        head=0,
        clearance=0.25,
        properties_from_tool=False,
        add_endings=False,
        simplified=False,
    ):
        """Initialize rack parameters.

        Args:
            m (float): Module.
            num_teeth (int): Number of teeth along the rack.
            pressure_angle (float): Pressure angle [rad].
            thickness (float): Rack body thickness in x direction.
            beta (float): Helix angle [rad].
            head (float): Addendum factor.
            clearance (float): Dedendum clearance factor.
            properties_from_tool (bool): Use normal-system tool interpretation.
            add_endings (bool): Extend profile with end-cap segments.
            simplified (bool): Use a simplified middle section for display.
        """
        self.pressure_angle = pressure_angle
        self.thickness = thickness
        self.m = m
        self.num_teeth = num_teeth
        self.beta = beta
        self.head = head
        self.clearance = clearance
        self.properties_from_tool = properties_from_tool
        self.add_endings = add_endings
        self.simplified = simplified

    def _update(self):
        """Apply defaults for attributes missing in older file versions."""
        if not hasattr(self, "add_endings"):
            self.add_endings = True
        if not hasattr(self, "simplified"):
            self.simplified = False

    def points(self, num=10):
        """Build a closed rack profile with all teeth.

        Args:
            num (int): Unused; kept for API compatibility with gear teeth.

        Returns:
            numpy.ndarray: Closed profile as ``(N, 2)`` array.
        """
        _, m_n, pitch, pressure_angle_t = self.compute_properties()

        a = (2 + self.head + self.clearance) * m_n * tan(pressure_angle_t)
        b = pitch / 4 - (1 + self.head) * m_n * tan(pressure_angle_t)
        tooth = [
            [-m_n * (1 + self.clearance), -a - b],
            [m_n * (1 + self.head), -b],
            [m_n * (1 + self.head), b],
            [-m_n * (1 + self.clearance), a + b],
        ]
        teeth = [tooth]
        trans = translation([0.0, pitch, 0.0])
        for i in range(self.num_teeth - 1):
            if self.simplified and i > 3 and i < (self.num_teeth - 6):
                tooth = trans(tooth).tolist()
            else:
                tooth = trans(tooth).tolist()
                teeth.append(tooth.copy())
                if self.simplified and (i == 3):
                    teeth[-1].pop()
                    teeth[-1].pop()
                    teeth[-1][-1][0] = 0
                    teeth[-1][-1][1] -= a / 2
                if self.simplified and (i == self.num_teeth - 6):
                    teeth[-1].pop(0)
                    teeth[-1].pop(0)
                    teeth[-1][0][0] = 0
                    teeth[-1][0][1] += a / 2

        teeth = array([v for t in teeth for v in t])  # flattening
        if self.add_endings:
            ext1 = teeth[0] + array([0.0, a + b - pitch / 2])
            ext2 = teeth[-1] - array([0.0, a + b - pitch / 2])
            teeth = (
                [ext1.tolist(), ext1.tolist()]
                + teeth.tolist()
                + [ext2.tolist(), ext2.tolist()]
            )
        else:
            teeth = [teeth[0].tolist()] + teeth.tolist() + [teeth[-1].tolist()]
        # teeth.append(list(teeth[-1]))
        teeth[0][0] -= self.thickness
        # teeth.append(list(teeth[0]))
        teeth[-1][0] -= self.thickness
        teeth.append(teeth[0])
        return array(teeth)

    def compute_properties(self):
        """Compute transverse module, normal module, pitch and pressure angle.

        Returns:
            tuple: ``(m, m_n, pitch, pressure_angle_t)`` where all angles are
                in radians and lengths share the module unit.
        """
        if self.properties_from_tool:
            pressure_angle_t = arctan(tan(self.pressure_angle) / cos(self.beta))
            m = self.m / cos(self.beta)
            m_n = self.m
        else:
            pressure_angle_t = self.pressure_angle
            m = self.m
            m_n = self.m

        pitch = m * pi
        return m, m_n, pitch, pressure_angle_t
