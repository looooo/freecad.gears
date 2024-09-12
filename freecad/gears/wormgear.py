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

from freecad import app
from freecad import part

from .translateutils import translate
from pygears.involute_tooth import InvoluteTooth
from pygears._functions import rotation

from .basegear import BaseGear, helical_extrusion, fcvec


class WormGear(BaseGear):
    """FreeCAD gear rack"""

    def __init__(self, obj):
        super(WormGear, self).__init__(obj)
        obj.addProperty(
            "App::PropertyInteger",
            "num_teeth",
            "base",
            translate("WormGear", "number of teeth"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "module",
            "base",
            translate("WormGear", "module"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "height",
            "base",
            translate("WormGear", "height"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "diameter",
            "base",
            translate("WormGear", "diameter"),
        )
        obj.addProperty(
            "App::PropertyAngle",
            "beta",
            "computed",
            translate("WormGear", "beta"),
            1,
        )
        obj.addProperty(
            "App::PropertyAngle",
            "pressure_angle",
            "involute",
            translate("WormGear", "pressure angle"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "reverse_pitch",
            "base",
            translate("WormGear", "reverse rotation of helix"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "head",
            "tolerance",
            translate("WormGear", "head * module = additional length of head"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "clearance",
            "tolerance",
            translate("WormGear", "clearance * module = additional length of root"),
        )
        obj.num_teeth = 3
        obj.module = "1. mm"
        obj.pressure_angle = "20. deg"
        obj.height = "5. mm"
        obj.diameter = "5. mm"
        obj.clearance = 0.25
        obj.head = 0
        obj.reverse_pitch = False

        self.obj = obj
        obj.Proxy = self

    def generate_gear_shape(self, fp):
        m = fp.module.Value
        d = fp.diameter.Value
        t = fp.num_teeth
        h = fp.height

        clearance = fp.clearance
        head = fp.head
        alpha = fp.pressure_angle.Value
        beta = np.arctan(m * t / d)
        fp.beta = np.rad2deg(beta)
        beta = -(fp.reverse_pitch * 2 - 1) * (np.pi / 2 - beta)

        r_1 = (d - (2 + 2 * clearance) * m) / 2
        r_2 = (d + (2 + 2 * head) * m) / 2
        z_a = (2 + head + clearance) * m * np.tan(np.deg2rad(alpha))
        z_b = (m * np.pi - 4 * m * np.tan(np.deg2rad(alpha))) / 2
        z_0 = clearance * m * np.tan(np.deg2rad(alpha))
        z_1 = z_b - z_0
        z_2 = z_1 + z_a
        z_3 = z_2 + z_b - 2 * head * m * np.tan(np.deg2rad(alpha))
        z_4 = z_3 + z_a

        def helical_projection(r, z):
            phi = 2 * z / m / t
            x = r * np.cos(phi)
            y = r * np.sin(phi)
            z = 0 * y
            return np.array([x, y, z]).T

        # create a circle from phi=0 to phi_1 with r_1
        phi_0 = 2 * z_0 / m / t
        phi_1 = 2 * z_1 / m / t
        c1 = part.makeCircle(
            r_1,
            app.Vector(0, 0, 0),
            app.Vector(0, 0, 1),
            np.rad2deg(phi_0),
            np.rad2deg(phi_1),
        )

        # create first bspline
        z_values = np.linspace(z_1, z_2, 10)
        r_values = np.linspace(r_1, r_2, 10)
        points = helical_projection(r_values, z_values)
        bsp1 = part.BSplineCurve()
        bsp1.interpolate(list(map(fcvec, points)))
        bsp1 = bsp1.toShape()

        # create circle from phi_2 to phi_3
        phi_2 = 2 * z_2 / m / t
        phi_3 = 2 * z_3 / m / t
        c2 = part.makeCircle(
            r_2,
            app.Vector(0, 0, 0),
            app.Vector(0, 0, 1),
            np.rad2deg(phi_2),
            np.rad2deg(phi_3),
        )

        # create second bspline
        z_values = np.linspace(z_3, z_4, 10)
        r_values = np.linspace(r_2, r_1, 10)
        points = helical_projection(r_values, z_values)
        bsp2 = part.BSplineCurve()
        bsp2.interpolate(list(map(fcvec, points)))
        bsp2 = bsp2.toShape()

        wire = part.Wire([c1, bsp1, c2, bsp2])
        w_all = [wire]

        rot = app.Matrix()
        rot.rotateZ(2 * np.pi / t)
        for i in range(1, t):
            w_all.append(w_all[-1].transformGeometry(rot))

        full_wire = part.Wire(w_all)
        if h == 0:
            return full_wire
        else:
            shape = helical_extrusion(part.Face(full_wire), h, h * np.tan(beta) * 2 / d)
            return shape
