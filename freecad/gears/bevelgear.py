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

from freecad import app
from freecad import part

import numpy as np
from pygears.bevel_tooth import BevelTooth
from pygears._functions import rotation3D

from .basegear import BaseGear, fcvec, make_bspline_wire


class BevelGear(BaseGear):

    """parameters:
    pressure_angle:  pressureangle,   10-30°
    pitch_angle:  cone angle,      0 < pitch_angle < pi/4
    """

    def __init__(self, obj):
        super(BevelGear, self).__init__(obj)
        self.bevel_tooth = BevelTooth()
        obj.addProperty("App::PropertyInteger", "teeth", "base", "number of teeth")
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty("App::PropertyAngle", "pitch_angle", "involute", "pitch_angle")
        obj.addProperty(
            "App::PropertyAngle",
            "pressure_angle",
            "involute_parameter",
            "pressure_angle",
        )
        obj.addProperty("App::PropertyLength", "module", "base", "module")
        obj.addProperty("App::PropertyFloat", "clearance", "tolerance", "clearance")
        obj.addProperty(
            "App::PropertyInteger",
            "numpoints",
            "precision",
            "number of points for spline",
        )
        obj.addProperty(
            "App::PropertyBool",
            "reset_origin",
            "base",
            "if value is true the gears outer face will match the z=0 plane",
        )
        obj.addProperty(
            "App::PropertyLength",
            "backlash",
            "tolerance",
            "The arc length on the pitch circle by which the tooth thicknes is reduced.",
        )
        obj.addProperty("App::PropertyPythonObject", "gear", "base", "test")
        obj.addProperty(
            "App::PropertyAngle", "beta", "helical", "angle used for spiral bevel-gears"
        )
        obj.addProperty("App::PropertyLength", "dw", "computed", "The pitch diameter.")
        obj.setExpression(
            "dw", "teeth * module"
        )  # calculate via expression to ease usage for placement
        obj.setEditorMode(
            "dw", 1
        )  # set read-only after setting the expression, else it won't be visible. bug?
        obj.addProperty(
            "App::PropertyAngle",
            "angular_backlash",
            "computed",
            "The angle by which this gear can turn without moving the mating gear.",
        )
        obj.setExpression(
            "angular_backlash", "backlash / dw * 360° / pi"
        )  # calculate via expression to ease usage for placement
        obj.setEditorMode(
            "angular_backlash", 1
        )  # set read-only after setting the expression, else it won't be visible. bug?
        obj.gear = self.bevel_tooth
        obj.module = "1. mm"
        obj.teeth = 15
        obj.pressure_angle = "20. deg"
        obj.pitch_angle = "45. deg"
        obj.height = "5. mm"
        obj.numpoints = 6
        obj.backlash = "0.00 mm"
        obj.clearance = 0.1
        obj.beta = "0 deg"
        obj.reset_origin = True
        self.obj = obj
        obj.Proxy = self

    def generate_gear_shape(self, fp):
        fp.gear.z = fp.teeth
        fp.gear.module = fp.module.Value
        fp.gear.pressure_angle = (90 - fp.pressure_angle.Value) * np.pi / 180.0
        fp.gear.pitch_angle = fp.pitch_angle.Value * np.pi / 180
        max_height = fp.gear.module * fp.teeth / 2 / np.tan(fp.gear.pitch_angle)
        if fp.height >= max_height:
            app.Console.PrintWarning(
                "height must be smaller than {}".format(max_height)
            )
        fp.gear.backlash = fp.backlash.Value
        scale = (
            fp.module.Value * fp.gear.z / 2 / np.tan(fp.pitch_angle.Value * np.pi / 180)
        )
        fp.gear.clearance = fp.clearance / scale
        fp.gear._update()
        pts = list(fp.gear.points(num=fp.numpoints))
        rot = rotation3D(- 2 * np.pi / fp.teeth)
        # if fp.beta.Value != 0:
        #     pts = [np.array([self.spherical_rot(j, fp.beta.Value * np.pi / 180.) for j in i]) for i in pts]

        rotated_pts = pts
        for i in range(fp.gear.z - 1):
            rotated_pts = list(map(rot, rotated_pts))
            pts.append(np.array([pts[-1][-1], rotated_pts[0][0]]))
            pts += rotated_pts
        pts.append(np.array([pts[-1][-1], pts[0][0]]))
        wires = []
        if not "version" in fp.PropertiesList:
            scale_0 = scale - fp.height.Value / 2
            scale_1 = scale + fp.height.Value / 2
        else:  # starting with version 0.0.2
            scale_0 = scale - fp.height.Value
            scale_1 = scale
        if fp.beta.Value == 0:
            wires.append(make_bspline_wire([scale_0 * p for p in pts]))
            wires.append(make_bspline_wire([scale_1 * p for p in pts]))
        else:
            for scale_i in np.linspace(scale_0, scale_1, 20):
                # beta_i = (scale_i - scale_0) * fp.beta.Value * np.pi / 180
                # rot = rotation3D(- beta_i)
                # points = [rot(pt) * scale_i for pt in pts]
                angle = (
                    fp.beta.Value
                    * np.pi
                    / 180.0
                    * np.sin(np.pi / 4)
                    / np.sin(fp.pitch_angle.Value * np.pi / 180.0)
                )
                points = [
                    np.array([self.spherical_rot(p, angle) for p in scale_i * pt])
                    for pt in pts
                ]
                wires.append(make_bspline_wire(points))
        shape = part.makeLoft(wires, True)
        if fp.reset_origin:
            mat = app.Matrix()
            mat.A33 = -1
            mat.move(fcvec([0, 0, scale_1]))
            shape = shape.transformGeometry(mat)
        return shape
        # return self.create_teeth(pts, pos1, fp.teeth)

    def create_tooth(self):
        w = []
        scal1 = (
            self.obj.m.Value
            * self.obj.gear.z
            / 2
            / np.tan(self.obj.pitch_angle.Value * np.pi / 180)
            - self.obj.height.Value / 2
        )
        scal2 = (
            self.obj.m.Value
            * self.obj.gear.z
            / 2
            / np.tan(self.obj.pitch_angle.Value * np.pi / 180)
            + self.obj.height.Value / 2
        )
        s = [scal1, scal2]
        pts = self.obj.gear.points(num=self.obj.numpoints)
        for j, pos in enumerate(s):
            w1 = []

            def scale(x):
                return fcvec(x * pos)

            for i in pts:
                i_scale = list(map(scale, i))
                w1.append(i_scale)
            w.append(w1)
        surfs = []
        w_t = zip(*w)
        for i in w_t:
            b = part.BSplineSurface()
            b.interpolate(i)
            surfs.append(b)
        return part.Shape(surfs)

    def spherical_rot(self, point, phi):
        new_phi = np.sqrt(np.linalg.norm(point)) * phi
        return rotation3D(- new_phi)(point)
