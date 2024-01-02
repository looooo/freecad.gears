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

from pygears.bevel_tooth import BevelTooth
from pygears._functions import rotation

from .basegear import BaseGear, fcvec, part_arc_from_points_and_center


class LanternGear(BaseGear):
    def __init__(self, obj):
        super(LanternGear, self).__init__(obj)
        obj.addProperty(
            "App::PropertyInteger", "teeth", "gear_parameter", "number of teeth"
        )
        obj.addProperty("App::PropertyLength", "module", "base", "module")
        obj.addProperty(
            "App::PropertyLength",
            "bolt_radius",
            "base",
            "the bolt radius of the rack/chain",
        )
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty(
            "App::PropertyInteger",
            "num_profiles",
            "accuracy",
            "number of profiles used for loft",
        )
        obj.addProperty(
            "App::PropertyFloat",
            "head",
            "tolerance",
            "head * module = additional length of head",
        )

        obj.teeth = 15
        obj.module = "1. mm"
        obj.bolt_radius = "1 mm"

        obj.height = "5. mm"
        obj.num_profiles = 10

        self.obj = obj
        obj.Proxy = self

    def generate_gear_shape(self, fp):
        m = fp.module.Value
        teeth = fp.teeth
        r_r = fp.bolt_radius.Value
        r_0 = m * teeth / 2
        r_max = r_0 + r_r + fp.head * m

        phi_max = (r_r + np.sqrt(r_max**2 - r_0**2)) / r_0

        def find_phi_min(phi_min):
            return r_0 * (
                phi_min**2 * r_0
                - 2 * phi_min * r_0 * np.sin(phi_min)
                - 2 * phi_min * r_r
                - 2 * r_0 * np.cos(phi_min)
                + 2 * r_0
                + 2 * r_r * np.sin(phi_min)
            )

        phi_min = sp.optimize.root(find_phi_min, (phi_max + r_r / r_0 * 4) / 5).x[
            0
        ]  # , r_r / r_0, phi_max)

        # phi_min = 0 # r_r / r_0
        phi = np.linspace(phi_min, phi_max, fp.num_profiles)
        x = r_0 * (np.cos(phi) + phi * np.sin(phi)) - r_r * np.sin(phi)
        y = r_0 * (np.sin(phi) - phi * np.cos(phi)) + r_r * np.cos(phi)
        xy1 = np.array([x, y]).T
        p_1 = xy1[0]
        p_1_end = xy1[-1]
        bsp_1 = part.BSplineCurve()
        bsp_1.interpolate(list(map(fcvec, xy1)))
        w_1 = bsp_1.toShape()

        xy2 = xy1 * np.array([1.0, -1.0])
        p_2 = xy2[0]
        p_2_end = xy2[-1]
        bsp_2 = part.BSplineCurve()
        bsp_2.interpolate(list(map(fcvec, xy2)))
        w_2 = bsp_2.toShape()

        p_12 = np.array([r_0 - r_r, 0.0])

        arc = part.Arc(
            app.Vector(*p_1, 0.0), app.Vector(*p_12, 0.0), app.Vector(*p_2, 0.0)
        ).toShape()

        rot = rotation(np.pi * 2 / teeth)
        p_3 = rot(np.array([p_2_end]))[0]
        # l = part.LineSegment(fcvec(p_1_end), fcvec(p_3)).toShape()
        l = part_arc_from_points_and_center(
            p_1_end, p_3, np.array([0.0, 0.0])
        ).toShape()
        w = part.Wire([w_2, arc, w_1, l])
        wires = [w]

        rot = app.Matrix()
        for _ in range(teeth - 1):
            rot.rotateZ(np.pi * 2 / teeth)
            wires.append(w.transformGeometry(rot))

        wi = part.Wire(wires)
        if fp.height.Value == 0:
            return wi
        else:
            return part.Face(wi).extrude(app.Vector(0, 0, fp.height))
