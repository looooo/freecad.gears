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


import numpy as np
import scipy as sp

from freecad import app
from freecad import part

from .translateutils import translate
from pygears._functions import rotation, reflection

from .basegear import BaseGear, fcvec, part_arc_from_points_and_center, insert_fillet


class TimingGearT(BaseGear):
    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyLength",
            "pitch",
            "base",
            translate("TimingGearT", "pitch of gear"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "teeth",
            "base",
            translate("TimingGearT", "number of teeth"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "tooth_height",
            "base",
            translate("TimingGearT", "radial height of tooth"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "u",
            "base",
            translate("TimingGearT", "radial distance from tooth-head to pitch circle"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "backlash",
            "tolerance",
            translate(
                "TimingGearT"
                "The arc length on the pitch circle by which the tooth thicknes is reduced.",
            ),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "head_fillet",
            "fillets",
            translate(
                "TimingGearT",
                "a fillet for the tooth-head, radius = head_fillet x module",
            ),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "root_fillet",
            "fillets",
            translate(
                "TimingGearT",
                "a fillet for the tooth-root, radius = root_fillet x module",
            ),
        )
        obj.addProperty(
            "App::PropertyAngle",
            "alpha",
            "base",
            translate("TimingGearT", "angle of tooth flanks"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "height",
            "base",
            translate("TimingGearT", "extrusion height"),
        )
        obj.pitch = "5. mm"
        obj.teeth = 15
        obj.tooth_height = "1.2 mm"
        obj.u = "0.6 mm"
        obj.alpha = "40. deg"
        obj.height = "5 mm"
        obj.backlash = "0. mm"
        obj.head_fillet = 0.4
        obj.root_fillet = 0.4
        self.obj = obj
        obj.Proxy = self

    def generate_gear_shape(self, obj):
        pitch = obj.pitch.Value
        teeth = obj.teeth
        u = obj.u.Value
        tooth_height = obj.tooth_height.Value
        alpha = obj.alpha.Value / 180.0 * np.pi  # we need radiant
        height = obj.height.Value
        backlash = obj.backlash.Value
        head_fillet = obj.head_fillet
        root_fillet = obj.root_fillet

        r_p = pitch * teeth / 2.0 / np.pi
        gamma_0 = pitch / r_p
        gamma_backlash = backlash / r_p
        gamma_1 = gamma_0 / 4 - gamma_backlash
        p_A = np.array([np.cos(-gamma_1), np.sin(-gamma_1)]) * (
            r_p - u - tooth_height / 2
        )

        def line(s):
            p = (
                p_A
                + np.array([np.cos(alpha / 2 - gamma_1), np.sin(alpha / 2 - gamma_1)])
                * s
            )
            return p

        def dist_p1(s):
            return (np.linalg.norm(line(s)) - (r_p - u - tooth_height)) ** 2

        def dist_p2(s):
            return (np.linalg.norm(line(s)) - (r_p - u)) ** 2

        s1 = sp.optimize.minimize(dist_p1, 0.0).x
        s2 = sp.optimize.minimize(dist_p2, 0.0).x

        p_1 = line(s1)
        p_2 = line(s2)

        mirror = reflection(0.0)  # reflect the points at the x-axis
        p_3, p_4 = mirror(np.array([p_2, p_1]))

        # for the fillets we need some more points
        rot = rotation(gamma_0)
        p_5, p_6, p_7 = rot(
            np.array([p_1, p_2, p_3])
        )  # the rotation expects a list of points

        e1 = part.LineSegment(fcvec(p_1), fcvec(p_2)).toShape()
        e2 = part_arc_from_points_and_center(p_2, p_3, np.array([0.0, 0.0])).toShape()
        e3 = part.LineSegment(fcvec(p_3), fcvec(p_4)).toShape()
        e4 = part_arc_from_points_and_center(p_4, p_5, np.array([0.0, 0.0])).toShape()
        e5 = part.LineSegment(fcvec(p_5), fcvec(p_6)).toShape()
        e6 = part_arc_from_points_and_center(p_6, p_7, np.array([0.0, 0.0])).toShape()
        edges = [e1, e2, e3, e4, e5, e6]
        edges = insert_fillet(edges, 4, head_fillet)

        # somehow we need to reverse the normal here
        edges = insert_fillet(edges, 3, root_fillet, reversed=True)
        edges = insert_fillet(edges, 2, root_fillet, reversed=True)
        edges = insert_fillet(edges, 1, head_fillet)
        edges = insert_fillet(edges, 0, head_fillet)
        edges = edges[2:-1]
        edges = [edge for edge in edges if edge is not None]
        w = part.Wire(edges)

        # now using a FreeCAD Matrix (this will turn in the right direction)
        rot = app.Matrix()
        rot.rotateZ(gamma_0)
        wires = []
        for i in range(teeth):
            w = w.transformGeometry(rot)
            wires.append(w.copy())
        contour = part.Wire(wires)
        if height == 0:
            return contour
        else:
            face = part.Face(part.Wire(wires))
            return face.extrude(app.Vector(0.0, 0.0, height))
