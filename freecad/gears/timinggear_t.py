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
import Part

from pygears._functions import rotation, reflection

from .basegear import BaseGear, fcvec


class TimingGearT(BaseGear):
    def __init__(self, obj):
        print("hello gear")
        obj.addProperty("App::PropertyLength", "pitch", "base", "pitch of gear")
        obj.addProperty("App::PropertyInteger", "teeth", "base", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "tooth_height", "base", "radial height of tooth"
        )
        obj.addProperty(
            "App::PropertyLength",
            "u",
            "base",
            "radial distance from tooth-head to pitch circle",
        )
        obj.addProperty("App::PropertyAngle", "alpha", "base", "angle of tooth flanks")
        obj.addProperty("App::PropertyLength", "height", "base", "extrusion height")
        obj.pitch = "5. mm"
        obj.teeth = 15
        obj.tooth_height = "1.2 mm"
        obj.u = "0.6 mm"
        obj.alpha = "40. deg"
        obj.height = "5 mm"
        self.obj = obj
        obj.Proxy = self

    def generate_gear_shape(self, fp):
        print("generate gear shape")
        pitch = fp.pitch.Value
        teeth = fp.teeth
        u = fp.u.Value
        tooth_height = fp.tooth_height.Value
        alpha = fp.alpha.Value / 180.0 * np.pi  # we need radiant
        height = fp.height.Value

        r_p = pitch * teeth / 2.0 / np.pi
        gamma_0 = pitch / r_p
        gamma_1 = gamma_0 / 4

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

        rot = rotation(-gamma_0)  # why is the rotation in wrong direction ???
        p_5 = rot(np.array([p_1]))[0]  # the rotation expects a list of points

        l1 = Part.LineSegment(fcvec(p_1), fcvec(p_2)).toShape()
        l2 = Part.LineSegment(fcvec(p_2), fcvec(p_3)).toShape()
        l3 = Part.LineSegment(fcvec(p_3), fcvec(p_4)).toShape()
        l4 = Part.LineSegment(fcvec(p_4), fcvec(p_5)).toShape()
        w = Part.Wire([l1, l2, l3, l4])

        # now using a FreeCAD Matrix (this will turn in the right direction)
        rot = app.Matrix()
        rot.rotateZ(gamma_0)
        wires = []
        for i in range(teeth):
            w = w.transformGeometry(rot)
            wires.append(w.copy())
        contour = Part.Wire(wires)
        if height == 0:
            return contour
        else:
            face = Part.Face(Part.Wire(wires))
            return face.extrude(app.Vector(0.0, 0.0, height))
