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
from .basegear import BaseGear, fcvec


class CrownGear(BaseGear):
    """
    A crown gear (also known as a face gear or a contrate gear) is a gear
    which has teeth that project at right angles to the face of the wheel.
    In particular, a crown gear is a type of bevel gear where the pitch cone
    angle is 90 degrees. https://en.wikipedia.org/wiki/Crown_gear
    """

    def __init__(self, obj):
        super(CrownGear, self).__init__(obj)
        obj.addProperty(
            "App::PropertyInteger",
            "num_teeth",
            "base",
            translate("CrownGear", "number of teeth"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "other_teeth",
            "base",
            translate("CrownGear", "number of teeth of other gear"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "module",
            "base",
            translate("CrownGear", "module"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "height",
            "base",
            translate("CrownGear", "height"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "thickness",
            "base",
            translate("CrownGear", "thickness"),
        )
        obj.addProperty(
            "App::PropertyAngle",
            "pressure_angle",
            "involute",
            translate("CrownGear", "pressure angle"),
        )
        self.add_accuracy_properties(obj)
        obj.num_teeth = 15
        obj.other_teeth = 15
        obj.module = "1. mm"
        obj.pressure_angle = "20. deg"
        obj.height = "2. mm"
        obj.thickness = "5 mm"
        obj.num_profiles = 4
        obj.preview_mode = True
        self.obj = obj
        obj.Proxy = self

        app.Console.PrintMessage(
            "Gear module: Crown gear created, preview_mode = true for improved performance. "
            "Set preview_mode property to false when ready to cut teeth."
        )

    def add_accuracy_properties(self, obj):
        obj.addProperty(
            "App::PropertyInteger",
            "num_profiles",
            "accuracy",
            translate("CrownGear", "number of profiles used for loft"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "preview_mode",
            "accuracy",
            translate("CrownGear", "if true no boolean operation is done"),
        )

    def profile(self, m, r, r0, t_c, t_i, alpha_w, y0, y1, y2):
        r_ew = m * t_i / 2

        # 1: modifizierter Waelzkreisdurchmesser:
        r_e = r / r0 * r_ew

        # 2: modifizierter Schraegungswinkel:
        alpha = np.arccos(r0 / r * np.cos(alpha_w))

        # 3: winkel phi bei senkrechter stellung eines zahns:
        phi = np.pi / t_i / 2 + (alpha - alpha_w) + (np.tan(alpha_w) - np.tan(alpha))

        # 4: Position des Eingriffspunktes:
        x_c = r_e * np.sin(phi)
        dy = -r_e * np.cos(phi) + r_ew

        # 5: oberer Punkt:
        b = y1 - dy
        a = np.tan(alpha) * b
        x1 = a + x_c

        # 6: unterer Punkt
        d = y2 + dy
        c = np.tan(alpha) * d
        x2 = x_c - c

        r *= np.cos(phi)
        pts = [[-x1, r, y0], [-x2, r, y0 - y1 - y2], [x2, r, y0 - y1 - y2], [x1, r, y0]]
        pts.append(pts[0])
        return pts

    def generate_gear_shape(self, fp):
        inner_diameter = fp.module.Value * fp.num_teeth
        outer_diameter = inner_diameter + fp.height.Value * 2
        inner_circle = part.Wire(part.makeCircle(inner_diameter / 2.0))
        outer_circle = part.Wire(part.makeCircle(outer_diameter / 2.0))
        inner_circle.reverse()
        face = part.Face([outer_circle, inner_circle])
        solid = face.extrude(app.Vector([0.0, 0.0, -fp.thickness.Value]))
        if fp.preview_mode:
            return solid

        # cutting obj
        alpha_w = np.deg2rad(fp.pressure_angle.Value)
        m = fp.module.Value
        t = fp.num_teeth
        t_c = t
        t_i = fp.other_teeth
        rm = inner_diameter / 2
        y0 = m * 0.5
        y1 = m + y0
        y2 = m
        r0 = inner_diameter / 2 - fp.height.Value * 0.1
        r1 = outer_diameter / 2 + fp.height.Value * 0.3
        polies = []
        for r_i in np.linspace(r0, r1, fp.num_profiles):
            pts = self.profile(m, r_i, rm, t_c, t_i, alpha_w, y0, y1, y2)
            poly = part.Wire(part.makePolygon(list(map(fcvec, pts))))
            polies.append(poly)
        loft = part.makeLoft(polies, True)
        rot = app.Matrix()
        rot.rotateZ(2 * np.pi / t)
        cut_shapes = []
        for _ in range(t):
            loft = loft.transformGeometry(rot)
            cut_shapes.append(loft)
        return solid.cut(cut_shapes)
