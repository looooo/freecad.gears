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

import math

import numpy as np

from freecad import app
from freecad import part

from .translateutils import translate
from pygears.bevel_tooth import BevelTooth
from pygears._functions import rotation

from .basegear import BaseGear, make_bspline_wire


class HypoCycloidGear(BaseGear):

    """parameters:
    pressure_angle:  pressureangle,   10-30°
    pitch_angle:  cone angle,      0 < pitch_angle < pi/4
    """

    def __init__(self, obj):
        super(HypoCycloidGear, self).__init__(obj)
        obj.addProperty(
            "App::PropertyFloat",
            "pin_circle_radius",
            "gear_parameter",
            translate(
                "HypoCycloidGear", "Pin ball circle radius (overrides Tooth Pitch)"
            ),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "roller_diameter",
            "gear_parameter",
            translate("HypoCycloidGear", "Roller Diameter"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "eccentricity",
            "gear_parameter",
            translate("HypoCycloidGear", "Eccentricity"),
        )
        obj.addProperty(
            "App::PropertyAngle",
            "pressure_angle_lim",
            "gear_parameter",
            translate("HypoCycloidGear", "Pressure angle limit"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "pressure_angle_offset",
            "gear_parameter",
            translate("HypoCycloidGear", "Offset in pressure angle"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "teeth_number",
            "gear_parameter",
            translate("HypoCycloidGear", "Number of teeth in Cam"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "segment_count",
            "gear_parameter",
            translate(
                "HypoCycloidGear", "Number of points used for spline interpolation"
            ),
        )
        obj.addProperty(
            "App::PropertyLength",
            "hole_radius",
            "gear_parameter",
            translate("HypoCycloidGear", "Center hole's radius"),
        )

        obj.addProperty(
            "App::PropertyBool",
            "show_pins",
            "Pins",
            translate("HypoCycloidGear", "Create pins in place"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "pin_height",
            "Pins",
            translate("HypoCycloidGear", "height"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "center_pins",
            "Pins",
            translate("HypoCycloidGear", "Center pin Z axis to generated disks"),
        )

        obj.addProperty(
            "App::PropertyBool",
            "show_disk0",
            "Disks",
            translate("HypoCycloidGear", "Show main cam disk"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "show_disk1",
            "Disks",
            translate("HypoCycloidGear", "Show another reversed cam disk on top"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "disk_height",
            "Disks",
            translate("HypoCycloidGear", "height"),
        )

        obj.pin_circle_radius = 66
        obj.roller_diameter = 3
        obj.eccentricity = 1.5
        obj.pressure_angle_lim = "50.0 deg"
        obj.pressure_angle_offset = 0.01
        obj.teeth_number = 42
        obj.segment_count = 42
        obj.hole_radius = "30. mm"

        obj.show_pins = True
        obj.pin_height = "20. mm"
        obj.center_pins = True

        obj.show_disk0 = True
        obj.show_disk1 = True
        obj.disk_height = "10. mm"

        self.obj = obj
        obj.Proxy = self

    def to_polar(self, x, y):
        return (x**2 + y**2) ** 0.5, math.atan2(y, x)

    def to_rect(self, r, a):
        return r * math.cos(a), r * math.sin(a)

    def calcyp(self, p, a, e, n):
        return math.atan(math.sin(n * a) / (math.cos(n * a) + (n * p) / (e * (n + 1))))

    def calc_x(self, p, d, e, n, a):
        return (
            (n * p) * math.cos(a)
            + e * math.cos((n + 1) * a)
            - d / 2 * math.cos(self.calcyp(p, a, e, n) + a)
        )

    def calc_y(self, p, d, e, n, a):
        return (
            (n * p) * math.sin(a)
            + e * math.sin((n + 1) * a)
            - d / 2 * math.sin(self.calcyp(p, a, e, n) + a)
        )

    def calc_pressure_angle(self, p, d, n, a):
        ex = 2**0.5
        r3 = p * n
        rg = r3 / ex
        pp = rg * (ex**2 + 1 - 2 * ex * math.cos(a)) ** 0.5 - d / 2
        return math.asin((r3 * math.cos(a) - rg) / (pp + d / 2)) * 180 / math.pi

    def calc_pressure_limit(self, p, d, e, n, a):
        ex = 2**0.5
        r3 = p * n
        rg = r3 / ex
        q = (r3**2 + rg**2 - 2 * r3 * rg * math.cos(a)) ** 0.5
        x = rg - e + (q - d / 2) * (r3 * math.cos(a) - rg) / q
        y = (q - d / 2) * r3 * math.sin(a) / q
        return (x**2 + y**2) ** 0.5

    def check_limit(self, x, y, maxrad, minrad, offset):
        r, a = self.to_polar(x, y)
        if (r > maxrad) or (r < minrad):
            r = r - offset
            x, y = self.to_rect(r, a)
        return x, y

    def generate_gear_shape(self, fp):
        b = fp.pin_circle_radius
        d = fp.roller_diameter
        e = fp.eccentricity
        n = fp.teeth_number
        p = b / n
        s = fp.segment_count
        ang = fp.pressure_angle_lim
        c = fp.pressure_angle_offset

        q = 2 * math.pi / float(s)

        # Find the pressure angle limit circles
        minAngle = -1.0
        maxAngle = -1.0
        for i in range(0, 180):
            x = self.calc_pressure_angle(p, d, n, i * math.pi / 180.0)
            if (x < ang) and (minAngle < 0):
                minAngle = float(i)
            if (x < -ang) and (maxAngle < 0):
                maxAngle = float(i - 1)

        minRadius = self.calc_pressure_limit(p, d, e, n, minAngle * math.pi / 180.0)
        maxRadius = self.calc_pressure_limit(p, d, e, n, maxAngle * math.pi / 180.0)
        # unused
        # part.Wire(part.makeCircle(minRadius, app.Vector(-e, 0, 0)))
        # part.Wire(part.makeCircle(maxRadius, app.Vector(-e, 0, 0)))

        app.Console.PrintMessage("Generating cam disk\r\n")
        # generate the cam profile - note: shifted in -x by eccentricicy amount
        i = 0
        x = self.calc_x(p, d, e, n, q * i / float(n))
        y = self.calc_y(p, d, e, n, q * i / n)
        x, y = self.check_limit(x, y, maxRadius, minRadius, c)
        points = [app.Vector(x - e, y, 0)]
        for i in range(0, s):
            x = self.calc_x(p, d, e, n, q * (i + 1) / n)
            y = self.calc_y(p, d, e, n, q * (i + 1) / n)
            x, y = self.check_limit(x, y, maxRadius, minRadius, c)
            points.append([x - e, y, 0])

        wi = make_bspline_wire([points])
        wires = []
        mat = app.Matrix()
        mat.move(app.Vector(e, 0.0, 0.0))
        mat.rotateZ(2 * np.pi / n)
        mat.move(app.Vector(-e, 0.0, 0.0))
        for _ in range(n):
            wi = wi.transformGeometry(mat)
            wires.append(wi)

        cam = part.Face(part.Wire(wires))
        # add a circle in the center of the cam
        if fp.hole_radius.Value:
            centerCircle = part.Face(
                part.Wire(part.makeCircle(fp.hole_radius.Value, app.Vector(-e, 0, 0)))
            )
            cam = cam.cut(centerCircle)

        to_be_fused = []
        if fp.show_disk0 == True:
            if fp.disk_height.Value == 0:
                to_be_fused.append(cam)
            else:
                to_be_fused.append(cam.extrude(app.Vector(0, 0, fp.disk_height.Value)))

        # secondary cam disk
        if fp.show_disk1 == True:
            app.Console.PrintMessage("Generating secondary cam disk\r\n")
            second_cam = cam.copy()
            mat = app.Matrix()
            mat.rotateZ(np.pi)
            mat.move(app.Vector(-e, 0, 0))
            if n % 2 == 0:
                mat.rotateZ(np.pi / n)
            mat.move(app.Vector(e, 0, 0))
            second_cam = second_cam.transformGeometry(mat)
            if fp.disk_height.Value == 0:
                to_be_fused.append(second_cam)
            else:
                to_be_fused.append(
                    second_cam.extrude(app.Vector(0, 0, -fp.disk_height.Value))
                )

        # pins
        if fp.show_pins == True:
            app.Console.PrintMessage("Generating pins\r\n")
            pins = []
            for i in range(0, n + 1):
                x = p * n * math.cos(2 * math.pi / (n + 1) * i)
                y = p * n * math.sin(2 * math.pi / (n + 1) * i)
                pins.append(part.Wire(part.makeCircle(d / 2, app.Vector(x, y, 0))))

            pins = part.Face(pins)

            z_offset = -fp.pin_height.Value / 2
            if fp.center_pins == True:
                if fp.show_disk0 == True and fp.show_disk1 == False:
                    z_offset += fp.disk_height.Value / 2
                elif fp.show_disk0 == False and fp.show_disk1 == True:
                    z_offset += -fp.disk_height.Value / 2
            # extrude
            if z_offset != 0:
                pins.translate(app.Vector(0, 0, z_offset))
            if fp.pin_height != 0:
                pins = pins.extrude(app.Vector(0, 0, fp.pin_height.Value))

            to_be_fused.append(pins)

        if to_be_fused:
            return part.makeCompound(to_be_fused)
