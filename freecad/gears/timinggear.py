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

import FreeCAD as App
import Part

import numpy as np

from pygears._functions import reflection
from .features import BaseGear, part_arc_from_points_and_center


class TimingGear(BaseGear):
    """FreeCAD gear rack"""

    data = {
        "gt2": {
            "pitch": 2.0,
            "u": 0.254,
            "h": 0.75,
            "H": 1.38,
            "r0": 0.555,
            "r1": 1.0,
            "rs": 0.15,
            "offset": 0.40,
        },
        "gt3": {
            "pitch": 3.0,
            "u": 0.381,
            "h": 1.14,
            "H": 2.40,
            "r0": 0.85,
            "r1": 1.52,
            "rs": 0.25,
            "offset": 0.61,
        },
        "gt5": {
            "pitch": 5.0,
            "u": 0.5715,
            "h": 1.93,
            "H": 3.81,
            "r0": 1.44,
            "r1": 2.57,
            "rs": 0.416,
            "offset": 1.03,
        },
        "gt8": {
            "pitch": 8.0,
            "u": 0.9144,
            "h": 3.088,
            "H": 6.096,
            "r0": 2.304,
            "r1": 4.112,
            "rs": 0.6656,
            "offset": 1.648,
        },
        "htd3": {
            "pitch": 3.0,
            "u": 0.381,
            "h": 1.21,
            "H": 2.40,
            "r0": 0.89,
            "r1": 0.89,
            "rs": 0.26,
            "offset": 0.0,
        },
        "htd5": {
            "pitch": 5.0,
            "u": 0.5715,
            "h": 2.06,
            "H": 3.80,
            "r0": 1.49,
            "r1": 1.49,
            "rs": 0.43,
            "offset": 0.0,
        },
        "htd8": {
            "pitch": 8.0,
            "u": 0.686,
            "h": 3.45,
            "H": 6.00,
            "r0": 2.46,
            "r1": 2.46,
            "rs": 0.70,
            "offset": 0.0,
        },
    }

    def __init__(self, obj):
        super(TimingGear, self).__init__(obj)
        obj.addProperty("App::PropertyInteger", "teeth", "base", "number of teeth")
        obj.addProperty(
            "App::PropertyEnumeration", "type", "base", "type of timing-gear"
        )
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty("App::PropertyLength", "pitch", "computed", "pitch of gear", 1)
        obj.addProperty(
            "App::PropertyLength", "h", "computed", "radial height of teeth", 1
        )
        obj.addProperty(
            "App::PropertyLength",
            "u",
            "computed",
            "radial difference between pitch diameter and head of gear",
            1,
        )
        obj.addProperty(
            "App::PropertyLength", "r0", "computed", "radius of first arc", 1
        )
        obj.addProperty(
            "App::PropertyLength", "r1", "computed", "radius of second arc", 1
        )
        obj.addProperty(
            "App::PropertyLength", "rs", "computed", "radius of third arc", 1
        )
        obj.addProperty(
            "App::PropertyLength",
            "offset",
            "computed",
            "x-offset of second arc-midpoint",
            1,
        )
        obj.teeth = 15
        obj.type = ["gt2", "gt3", "gt5", "gt8", "htd3", "htd5", "htd8"]
        obj.height = "5. mm"

        self.obj = obj
        obj.Proxy = self

    def generate_gear_shape(self, fp):
        # m ... center of arc/circle
        # r ... radius of arc/circle
        # x ... end-point of arc
        # phi ... angle
        tp = fp.type
        gt_data = self.data[tp]
        pitch = fp.pitch = gt_data["pitch"]
        h = fp.h = gt_data["h"]
        u = fp.u = gt_data["u"]
        r_12 = fp.r0 = gt_data["r0"]
        r_23 = fp.r1 = gt_data["r1"]
        r_34 = fp.rs = gt_data["rs"]
        offset = fp.offset = gt_data["offset"]

        arcs = []
        if offset == 0.0:
            phi5 = np.pi / fp.teeth
            ref = reflection(-phi5 - np.pi / 2.0)
            rp = pitch * fp.teeth / np.pi / 2.0 - u

            m_34 = np.array([-(r_12 + r_34), rp - h + r_12])
            x2 = np.array([-r_12, m_34[1]])
            x4 = np.array([m_34[0], m_34[1] + r_34])
            x6 = ref(x4)

            mir = np.array([-1.0, 1.0])
            xn2 = mir * x2
            xn4 = mir * x4
            mn_34 = mir * m_34

            arcs.append(part_arc_from_points_and_center(xn4, xn2, mn_34).toShape())
            arcs.append(
                Part.Arc(
                    App.Vector(*xn2, 0.0),
                    App.Vector(0, rp - h, 0.0),
                    App.Vector(*x2, 0.0),
                ).toShape()
            )
            arcs.append(part_arc_from_points_and_center(x2, x4, m_34).toShape())
            arcs.append(
                part_arc_from_points_and_center(x4, x6, np.array([0.0, 0.0])).toShape()
            )

        else:
            phi_12 = np.arctan(np.sqrt(1.0 / (((r_12 - r_23) / offset) ** 2 - 1)))
            rp = pitch * fp.teeth / np.pi / 2.0
            r4 = r5 = rp - u

            m_12 = np.array([0.0, r5 - h + r_12])
            m_23 = np.array([offset, offset / np.tan(phi_12) + m_12[1]])
            m_23y = m_23[1]

            # solving for phi4:
            # sympy.solve(
            # ((r5 - r_34) * sin(phi4) + offset) ** 2 + \
            # ((r5 - r_34) * cos(phi4) - m_23y) ** 2 - \
            # ((r_34 + r_23) ** 2), phi4)

            phi4 = 2 * np.arctan(
                (
                    -2 * offset * r5
                    + 2 * offset * r_34
                    + np.sqrt(
                        -(m_23y**4)
                        - 2 * m_23y**2 * offset**2
                        + 2 * m_23y**2 * r5**2
                        - 4 * m_23y**2 * r5 * r_34
                        + 2 * m_23y**2 * r_23**2
                        + 4 * m_23y**2 * r_23 * r_34
                        + 4 * m_23y**2 * r_34**2
                        - offset**4
                        + 2 * offset**2 * r5**2
                        - 4 * offset**2 * r5 * r_34
                        + 2 * offset**2 * r_23**2
                        + 4 * offset**2 * r_23 * r_34
                        + 4 * offset**2 * r_34**2
                        - r5**4
                        + 4 * r5**3 * r_34
                        + 2 * r5**2 * r_23**2
                        + 4 * r5**2 * r_23 * r_34
                        - 4 * r5**2 * r_34**2
                        - 4 * r5 * r_23**2 * r_34
                        - 8 * r5 * r_23 * r_34**2
                        - r_23**4
                        - 4 * r_23**3 * r_34
                        - 4 * r_23**2 * r_34**2
                    )
                )
                / (
                    m_23y**2
                    + 2 * m_23y * r5
                    - 2 * m_23y * r_34
                    + offset**2
                    + r5**2
                    - 2 * r5 * r_34
                    - r_23**2
                    - 2 * r_23 * r_34
                )
            )

            phi5 = np.pi / fp.teeth

            m_34 = (r5 - r_34) * np.array([-np.sin(phi4), np.cos(phi4)])

            x2 = np.array([-r_12 * np.sin(phi_12), m_12[1] - r_12 * np.cos(phi_12)])
            x3 = m_34 + r_34 / (r_34 + r_23) * (m_23 - m_34)
            x4 = r4 * np.array([-np.sin(phi4), np.cos(phi4)])

            ref = reflection(-phi5 - np.pi / 2)
            x6 = ref(x4)
            mir = np.array([-1.0, 1.0])
            xn2 = mir * x2
            xn3 = mir * x3
            xn4 = mir * x4

            mn_34 = mir * m_34
            mn_23 = mir * m_23

            arcs.append(part_arc_from_points_and_center(xn4, xn3, mn_34).toShape())
            arcs.append(part_arc_from_points_and_center(xn3, xn2, mn_23).toShape())
            arcs.append(part_arc_from_points_and_center(xn2, x2, m_12).toShape())
            arcs.append(part_arc_from_points_and_center(x2, x3, m_23).toShape())
            arcs.append(part_arc_from_points_and_center(x3, x4, m_34).toShape())
            arcs.append(
                part_arc_from_points_and_center(x4, x6, np.array([0.0, 0.0])).toShape()
            )

        wire = Part.Wire(arcs)
        wires = [wire]
        rot = App.Matrix()
        rot.rotateZ(np.pi * 2 / fp.teeth)
        for _ in range(fp.teeth - 1):
            wire = wire.transformGeometry(rot)
            wires.append(wire)

        wi = Part.Wire(wires)
        if fp.height.Value == 0:
            return wi
        else:
            return Part.Face(wi).extrude(App.Vector(0, 0, fp.height))
