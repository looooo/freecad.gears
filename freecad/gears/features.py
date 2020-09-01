# -*- coding: utf-8 -*-
# ***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

from __future__ import division
import os

import numpy as np
import math
from pygears.involute_tooth import InvoluteTooth, InvoluteRack
from pygears.cycloide_tooth import CycloideTooth
from pygears.bevel_tooth import BevelTooth
from pygears._functions import rotation3D, rotation, reflection, arc_from_points_and_center


import FreeCAD as App
import Part
from Part import BSplineCurve, Shape, Wire, Face, makePolygon, \
    makeLoft, Line, BSplineSurface, \
    makePolygon, makeHelix, makeShell, makeSolid


__all__ = ["InvoluteGear",
           "CycloideGear",
           "BevelGear",
           "InvoluteGearRack",
           "ViewProviderGear"]


def fcvec(x):
    if len(x) == 2:
        return(App.Vector(x[0], x[1], 0))
    else:
        return(App.Vector(x[0], x[1], x[2]))


class ViewProviderGear(object):
    def __init__(self, obj):
        ''' Set this object to the proxy object of the actual view provider '''
        obj.Proxy = self

    def attach(self, vobj):
        self.vobj = vobj

    def getIcon(self):
        __dirname__ = os.path.dirname(__file__)
        return(os.path.join(__dirname__, "icons", "involutegear.svg"))

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class InvoluteGear(object):

    """FreeCAD gear"""

    def __init__(self, obj):
        self.involute_tooth = InvoluteTooth()
        obj.addProperty(
            "App::PropertyBool", "simple", "gear_parameter", "simple")
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyBool", "undercut", "gear_parameter", "undercut")
        obj.addProperty(
            "App::PropertyFloat", "shift", "gear_parameter", "shift")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyAngle", "pressure_angle", "involute_parameter", "pressure angle")
        obj.addProperty(
            "App::PropertyFloat", "clearance", "gear_parameter", "clearance")
        obj.addProperty("App::PropertyInteger", "numpoints",
                        "gear_parameter", "number of points for spline")
        obj.addProperty(
            "App::PropertyAngle", "beta", "gear_parameter", "beta ")
        obj.addProperty(
            "App::PropertyBool", "double_helix", "gear_parameter", "double helix")
        obj.addProperty(
            "App::PropertyLength", "backlash", "tolerance", "backlash")
        obj.addProperty(
            "App::PropertyBool", "reversed_backlash", "tolerance", "backlash direction")
        obj.addProperty(
            "App::PropertyFloat", "head", "gear_parameter", "head_value * modul_value = additional length of head")
        obj.addProperty(
            "App::PropertyBool", "properties_from_tool", "gear_parameter", "if beta is given and properties_from_tool is enabled, \
            gear parameters are internally recomputed for the rotated gear")
        obj.addProperty("App::PropertyPythonObject",
                        "gear", "gear_parameter", "test")
        obj.addProperty("App::PropertyLength", "dw",
                        "computed", "pitch diameter", 1)
        obj.addProperty("App::PropertyLength", "transverse_pitch",
                        "computed", "transverse_pitch", 1)
        obj.gear = self.involute_tooth
        obj.simple = False
        obj.undercut = False
        obj.teeth = 15
        obj.module = '1. mm'
        obj.shift = 0.
        obj.pressure_angle = '20. deg'
        obj.beta = '0. deg'
        obj.height = '5. mm'
        obj.clearance = 0.25
        obj.head = 0.
        obj.numpoints = 6
        obj.double_helix = False
        obj.backlash = '0.00 mm'
        obj.reversed_backlash = False
        obj.properties_from_tool = True
        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        fp.gear.double_helix = fp.double_helix
        fp.gear.m_n = fp.module.Value
        fp.gear.z = fp.teeth
        fp.gear.undercut = fp.undercut
        fp.gear.shift = fp.shift
        fp.gear.pressure_angle = fp.pressure_angle.Value * np.pi / 180.
        fp.gear.beta = fp.beta.Value * np.pi / 180
        fp.gear.clearance = fp.clearance
        fp.gear.backlash = fp.backlash.Value * \
            (-fp.reversed_backlash + 0.5) * 2.
        fp.gear.head = fp.head
        # checksbackwardcompatibility:
        if "properties_from_tool" in fp.PropertiesList:
            fp.gear.properties_from_tool = fp.properties_from_tool
        fp.gear._update()
        pts = fp.gear.points(num=fp.numpoints)
        rotated_pts = pts
        rot = rotation(-fp.gear.phipart)
        for i in range(fp.gear.z - 1):
            rotated_pts = list(map(rot, rotated_pts))
            pts.append(np.array([pts[-1][-1], rotated_pts[0][0]]))
            pts += rotated_pts
        pts.append(np.array([pts[-1][-1], pts[0][0]]))
        if not fp.simple:
            wi = []
            for i in pts:
                out = BSplineCurve()
                out.interpolate(list(map(fcvec, i)))
                wi.append(out.toShape())
            wi = Wire(wi)
            if fp.height.Value == 0:
                fp.Shape = wi
            elif fp.beta.Value == 0:
                sh = Face(wi)
                fp.Shape = sh.extrude(App.Vector(0, 0, fp.height.Value))
            else:
                fp.Shape = helicalextrusion(
                    wi, fp.height.Value, fp.height.Value * np.tan(fp.gear.beta) * 2 / fp.gear.d, fp.double_helix)
        else:
            rw = fp.gear.dw / 2
            fp.Shape = Part.makeCylinder(rw, fp.height.Value)

        # computed properties
        fp.dw = "{}mm".format(fp.gear.dw)
        fp.transverse_pitch = "{}mm".format(fp.gear.pitch)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class InvoluteGearRack(object):

    """FreeCAD gear rack"""

    def __init__(self, obj):
        self.involute_rack = InvoluteRack()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyLength", "thickness", "gear_parameter", "thickness")
        obj.addProperty(
            "App::PropertyAngle", "beta", "gear_parameter", "beta ")
        obj.addProperty(
            "App::PropertyAngle", "pressure_angle", "involute_parameter", "pressure angle")
        obj.addProperty(
            "App::PropertyBool", "double_helix", "gear_parameter", "double helix")
        obj.addProperty(
            "App::PropertyFloat", "head", "gear_parameter", "head * module = additional length of head")
        obj.addProperty(
            "App::PropertyFloat", "clearance", "gear_parameter", "clearance * module = additional length of foot")
        obj.addProperty(
            "App::PropertyBool", "properties_from_tool", "gear_parameter", "if beta is given and properties_from_tool is enabled, \
            gear parameters are internally recomputed for the rotated gear")
        obj.addProperty("App::PropertyLength", "transverse_pitch",
            "computed", "pitch in the transverse plane", 1)
        obj.addProperty("App::PropertyBool", "add_endings", "gear_parameter", "if enabled the total length of the rack is teeth x pitch, \
            otherwise the rack starts with a tooth-flank")
        obj.addProperty(
            "App::PropertyBool", "simplified", "gear_parameter", "if enabled the rack is drawn with a constant number of \
            teeth to avoid topologic renaming.")
        obj.addProperty("App::PropertyPythonObject", "rack", "test", "test")
        obj.rack = self.involute_rack
        obj.teeth = 15
        obj.module = '1. mm'
        obj.pressure_angle = '20. deg'
        obj.height = '5. mm'
        obj.thickness = '5 mm'
        obj.beta = '0. deg'
        obj.clearance = 0.25
        obj.head = 0.
        obj.properties_from_tool = True
        obj.add_endings = True
        obj.simplified = False
        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        fp.rack.m = fp.module.Value
        fp.rack.z = fp.teeth
        fp.rack.pressure_angle = fp.pressure_angle.Value * np.pi / 180.
        fp.rack.thickness = fp.thickness.Value
        fp.rack.beta = fp.beta.Value * np.pi / 180.
        fp.rack.head = fp.head
        # checksbackwardcompatibility:
        if "clearance" in fp.PropertiesList:
            fp.rack.clearance = fp.clearance
        if "properties_from_tool" in fp.PropertiesList:
            fp.rack.properties_from_tool = fp.properties_from_tool
        if "add_endings" in fp.PropertiesList:
            fp.rack.add_endings = fp.add_endings
        if "simplified" in fp.PropertiesList:
            fp.rack.simplified = fp.simplified
        fp.rack._update()
        pts = fp.rack.points()
        pol = Wire(makePolygon(list(map(fcvec, pts))))
        if fp.height.Value == 0:
            fp.Shape = pol
        elif fp.beta.Value == 0:
            face = Face(Wire(pol))
            fp.Shape = face.extrude(fcvec([0., 0., fp.height.Value]))
        elif fp.double_helix:
            beta = fp.beta.Value * np.pi / 180.
            pol2 = Part.Wire(pol)
            pol2.translate(
                fcvec([0., np.tan(beta) * fp.height.Value / 2, fp.height.Value / 2]))
            pol3 = Part.Wire(pol)
            pol3.translate(fcvec([0., 0., fp.height.Value]))
            fp.Shape = makeLoft([pol, pol2, pol3], True, True)
        else:
            beta = fp.beta.Value * np.pi / 180.
            pol2 = Part.Wire(pol)
            pol2.translate(
                fcvec([0., np.tan(beta) * fp.height.Value, fp.height.Value]))
            fp.Shape = makeLoft([pol, pol2], True)
        # computed properties
        if "transverse_pitch" in fp.PropertiesList:
            fp.transverse_pitch = "{} mm".format(fp.rack.compute_properties()[2])

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class CrownGear(object):
    def __init__(self, obj):
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty("App::PropertyInteger",
                        "other_teeth", "gear_parameter", "number of teeth of other gear")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyLength", "thickness", "gear_parameter", "thickness")
        obj.addProperty(
            "App::PropertyAngle", "pressure_angle", "involute_parameter", "pressure angle")
        obj.addProperty("App::PropertyInteger",
                        "num_profiles", "accuracy", "number of profiles used for loft")
        obj.addProperty("App::PropertyBool",
                        "construct", "accuracy", "number of profiles used for loft")
        obj.teeth = 15
        obj.other_teeth = 15
        obj.module = '1. mm'
        obj.pressure_angle = '20. deg'
        obj.height = '2. mm'
        obj.thickness = '5 mm'
        obj.num_profiles = 4
        obj.construct = True
        self.obj = obj
        obj.Proxy = self

        App.Console.PrintMessage("Gear module: Crown gear created, construct mode = true for improved performance. "\
                                 "Set construct property to false when ready to cut teeth.")

    def profile(self, m, r, r0, t_c, t_i, alpha_w, y0, y1, y2):
        r_ew = m * t_i / 2

        # 1: modifizierter Waelzkreisdurchmesser:
        r_e = r / r0 * r_ew

        # 2: modifizierter Schraegungswinkel:
        alpha = np.arccos(r0 / r * np.cos(alpha_w))

        # 3: winkel phi bei senkrechter stellung eines zahns:
        phi = np.pi / t_i / 2 + (alpha - alpha_w) + \
            (np.tan(alpha_w) - np.tan(alpha))

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
        pts = [
            [-x1, r, y0],
            [-x2, r, y0 - y1 - y2],
            [x2, r, y0 - y1 - y2],
            [x1, r, y0]
        ]
        pts.append(pts[0])
        return pts

    def execute(self, fp):
        inner_diameter = fp.module.Value * fp.teeth
        outer_diameter = inner_diameter + fp.height.Value * 2
        inner_circle = Part.Wire(Part.makeCircle(inner_diameter / 2.))
        outer_circle = Part.Wire(Part.makeCircle(outer_diameter / 2.))
        inner_circle.reverse()
        face = Part.Face([outer_circle, inner_circle])
        solid = face.extrude(App.Vector([0., 0., -fp.thickness.Value]))

        # cutting obj
        alpha_w = np.deg2rad(fp.pressure_angle.Value)
        m = fp.module.Value
        t = fp.teeth
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
            poly = Wire(makePolygon(list(map(fcvec, pts))))
            polies.append(poly)
        loft = makeLoft(polies, True)
        rot = App.Matrix()
        rot.rotateZ(2 * np.pi / t)
        if fp.construct:
            cut_shapes = [solid]
            for _ in range(t):
                loft = loft.transformGeometry(rot)
                cut_shapes.append(loft)
            fp.Shape = Part.Compound(cut_shapes)
        else:
            for i in range(t):
                loft = loft.transformGeometry(rot)
                solid = solid.cut(loft)
            fp.Shape = solid

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass


class CycloideGear(object):
    """FreeCAD gear"""

    def __init__(self, obj):
        self.cycloide_tooth = CycloideTooth()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyLength", "inner_diameter", "cycloid_parameter", "inner_diameter")
        obj.addProperty(
            "App::PropertyLength", "outer_diameter", "cycloid_parameter", "outer_diameter")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyBool", "double_helix", "gear_parameter", "double helix")
        obj.addProperty(
            "App::PropertyFloat", "clearance", "gear_parameter", "clearance")
        obj.addProperty("App::PropertyInteger", "numpoints",
                        "gear_parameter", "number of points for spline")
        obj.addProperty("App::PropertyAngle", "beta", "gear_parameter", "beta")
        obj.addProperty(
            "App::PropertyLength", "backlash", "gear_parameter", "backlash in mm")
        obj.addProperty("App::PropertyPythonObject", "gear",
                        "gear_parameter", "the python object")
        obj.gear = self.cycloide_tooth
        obj.teeth = 15
        obj.module = '1. mm'
        obj.inner_diameter = '5 mm'
        obj.outer_diameter = '5 mm'
        obj.beta = '0. deg'
        obj.height = '5. mm'
        obj.clearance = 0.25
        obj.numpoints = 15
        obj.backlash = '0.00 mm'
        obj.double_helix = False
        obj.Proxy = self

    def execute(self, fp):
        fp.gear.m = fp.module.Value
        fp.gear.z = fp.teeth
        fp.gear.z1 = fp.inner_diameter.Value
        fp.gear.z2 = fp.outer_diameter.Value
        fp.gear.clearance = fp.clearance
        fp.gear.backlash = fp.backlash.Value
        fp.gear._update()
        pts = fp.gear.points(num=fp.numpoints)
        rotated_pts = pts
        rot = rotation(-fp.gear.phipart)
        for i in range(fp.gear.z - 1):
            rotated_pts = list(map(rot, rotated_pts))
            pts.append(np.array([pts[-1][-1], rotated_pts[0][0]]))
            pts += rotated_pts
        pts.append(np.array([pts[-1][-1], pts[0][0]]))
        wi = []
        for i in pts:
            out = BSplineCurve()
            out.interpolate(list(map(fcvec, i)))
            wi.append(out.toShape())
        wi = Wire(wi)
        if fp.height.Value == 0:
            fp.Shape = wi
        elif fp.beta.Value == 0:
            sh = Face(wi)
            fp.Shape = sh.extrude(App.Vector(0, 0, fp.height.Value))
        else:
            fp.Shape = helicalextrusion(
                wi, fp.height.Value, fp.height.Value * np.tan(fp.beta.Value * np.pi / 180) * 2 / fp.gear.d, fp.double_helix)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class BevelGear(object):

    """parameters:
        pressure_angle:  pressureangle,   10-30°
        pitch_angle:  cone angle,      0 < pitch_angle < pi/4
    """

    def __init__(self, obj):
        self.bevel_tooth = BevelTooth()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyAngle", "pitch_angle", "involute_parameter", "pitch_angle")
        obj.addProperty(
            "App::PropertyAngle", "pressure_angle", "involute_parameter", "pressure_angle")
        obj.addProperty("App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyFloat", "clearance", "gear_parameter", "clearance")
        obj.addProperty("App::PropertyInteger", "numpoints",
                        "gear_parameter", "number of points for spline")
        obj.addProperty("App::PropertyBool", "reset_origin", "gear_parameter",
                        "if value is true the gears outer face will match the z=0 plane")
        obj.addProperty(
            "App::PropertyLength", "backlash", "gear_parameter", "backlash in mm")
        obj.addProperty("App::PropertyPythonObject",
                        "gear", "gear_paramenter", "test")
        obj.addProperty("App::PropertyAngle", "beta",
                        "gear_paramenter", "test")
        obj.gear = self.bevel_tooth
        obj.module = '1. mm'
        obj.teeth = 15
        obj.pressure_angle = '20. deg'
        obj.pitch_angle = '45. deg'
        obj.height = '5. mm'
        obj.numpoints = 6
        obj.backlash = '0.00 mm'
        obj.clearance = 0.1
        obj.beta = '0 deg'
        obj.reset_origin = True
        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        fp.gear.z = fp.teeth
        fp.gear.module = fp.module.Value
        fp.gear.pressure_angle = (90 - fp.pressure_angle.Value) * np.pi / 180.
        fp.gear.pitch_angle = fp.pitch_angle.Value * np.pi / 180
        fp.gear.backlash = fp.backlash.Value
        scale = fp.module.Value * fp.gear.z / 2 / \
            np.tan(fp.pitch_angle.Value * np.pi / 180)
        fp.gear.clearance = fp.clearance / scale
        fp.gear._update()
        pts = list(fp.gear.points(num=fp.numpoints))
        rot = rotation3D(2 * np.pi / fp.teeth)
        # if fp.beta.Value != 0:
        #     pts = [np.array([self.spherical_rot(j, fp.beta.Value * np.pi / 180.) for j in i]) for i in pts]

        rotated_pts = pts
        for i in range(fp.gear.z - 1):
            rotated_pts = list(map(rot, rotated_pts))
            pts.append(np.array([pts[-1][-1], rotated_pts[0][0]]))
            pts += rotated_pts
        pts.append(np.array([pts[-1][-1], pts[0][0]]))
        wires = []
        scale_0 = scale - fp.height.Value / 2
        scale_1 = scale + fp.height.Value / 2
        if fp.beta.Value == 0:
            wires.append(makeBSplineWire([scale_0 * p for p in pts]))
            wires.append(makeBSplineWire([scale_1 * p for p in pts]))
        else:
            for scale_i in np.linspace(scale_0, scale_1, 20):
                # beta_i = (scale_i - scale_0) * fp.beta.Value * np.pi / 180
                # rot = rotation3D(beta_i)
                # points = [rot(pt) * scale_i for pt in pts]
                angle = fp.beta.Value * np.pi / 180. * \
                    np.sin(np.pi / 4) / \
                    np.sin(fp.pitch_angle.Value * np.pi / 180.)
                points = [np.array([self.spherical_rot(p, angle)
                                    for p in scale_i * pt]) for pt in pts]
                wires.append(makeBSplineWire(points))
        shape = makeLoft(wires, True)
        if fp.reset_origin:
            mat = App.Matrix()
            mat.A33 = -1
            mat.move(fcvec([0, 0, scale_1]))
            shape = shape.transformGeometry(mat)
        fp.Shape = shape
        # fp.Shape = self.create_teeth(pts, pos1, fp.teeth)

    def create_tooth(self):
        w = []
        scal1 = self.obj.m.Value * self.obj.gear.z / 2 / np.tan(
            self.obj.pitch_angle.Value * np.pi / 180) - self.obj.height.Value / 2
        scal2 = self.obj.m.Value * self.obj.gear.z / 2 / np.tan(
            self.obj.pitch_angle.Value * np.pi / 180) + self.obj.height.Value / 2
        s = [scal1, scal2]
        pts = self.obj.gear.points(num=self.obj.numpoints)
        for j, pos in enumerate(s):
            w1 = []

            def scale(x): return fcvec(x * pos)
            for i in pts:
                i_scale = list(map(scale, i))
                w1.append(i_scale)
            w.append(w1)
        surfs = []
        w_t = zip(*w)
        for i in w_t:
            b = BSplineSurface()
            b.interpolate(i)
            surfs.append(b)
        return Shape(surfs)

    def spherical_rot(self, point, phi):
        new_phi = np.sqrt(np.linalg.norm(point)) * phi
        return rotation3D(new_phi)(point)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class WormGear(object):

    """FreeCAD gear rack"""

    def __init__(self, obj):
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyLength", 'diameter', "gear_parameter", "diameter")
        obj.addProperty(
            "App::PropertyAngle", "beta", "gear_parameter", "beta ", 1)
        obj.addProperty(
            "App::PropertyAngle", "pressure_angle", "involute_parameter", "pressure angle")
        obj.addProperty(
            "App::PropertyFloat", "head", "gear_parameter", "head * module = additional length of head")
        obj.addProperty(
            "App::PropertyFloat", "clearance", "gear_parameter", "clearance * module = additional length of foot")

        obj.teeth = 3
        obj.module = '1. mm'
        obj.pressure_angle = '20. deg'
        obj.height = '5. mm'
        obj.diameter = '5. mm'
        obj.clearance = 0.25
        obj.head = 0

        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        m = fp.module.Value
        d = fp.diameter.Value
        t = fp.teeth
        h = fp.height

        clearance = fp.clearance
        head = fp.head
        alpha = fp.pressure_angle.Value
        beta = np.arctan(m * t / d)
        fp.beta = np.rad2deg(beta)
        beta = np.pi / 2 - beta

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
            return np.array([x, y, z]). T

        # create a circle from phi=0 to phi_1 with r_1
        phi_0 = 2 * z_0 / m / t
        phi_1 = 2 * z_1 / m / t
        c1 = Part.makeCircle(r_1, App.Vector(0, 0, 0),
                             App.Vector(0, 0, 1), np.rad2deg(phi_0), np.rad2deg(phi_1))

        # create first bspline
        z_values = np.linspace(z_1, z_2, 10)
        r_values = np.linspace(r_1, r_2, 10)
        points = helical_projection(r_values, z_values)
        bsp1 = Part.BSplineCurve()
        bsp1.interpolate(list(map(fcvec, points)))
        bsp1 = bsp1.toShape()

        # create circle from phi_2 to phi_3
        phi_2 = 2 * z_2 / m / t
        phi_3 = 2 * z_3 / m / t
        c2 = Part.makeCircle(r_2, App.Vector(0, 0, 0), App.Vector(
            0, 0, 1), np.rad2deg(phi_2), np.rad2deg(phi_3))

        # create second bspline
        z_values = np.linspace(z_3, z_4, 10)
        r_values = np.linspace(r_2, r_1, 10)
        points = helical_projection(r_values, z_values)
        bsp2 = Part.BSplineCurve()
        bsp2.interpolate(list(map(fcvec, points)))
        bsp2 = bsp2.toShape()

        wire = Part.Wire([c1, bsp1, c2, bsp2])
        w_all = [wire]

        rot = App.Matrix()
        rot.rotateZ(2 * np.pi / t)
        for i in range(1, t):
            w_all.append(w_all[-1].transformGeometry(rot))

        full_wire = Part.Wire(Part.Wire(w_all))
        if h == 0:
            fp.Shape = full_wire
        else:
            shape = helicalextrusion(full_wire, h, h * np.tan(beta) * 2 / d)
            fp.Shape = shape

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class TimingGear(object):

    """FreeCAD gear rack"""
    data = {"gt2":  {'pitch': 2.0, 'u': 0.254,  'h': 0.75,
                    'H': 1.38,    'r0': 0.555, 'r1': 1.0,
                    'rs': 0.15,   'offset': 0.40
                    },
            "gt3":  {'pitch': 3.0, 'u': 0.381, 'h': 1.14,
                    'H': 2.40, 'r0': 0.85, 'r1': 1.52,
                    'rs': 0.25, 'offset': 0.61
                    },
            "gt5":  {
                    'pitch': 5.0,  'u': 0.5715,  'h': 1.93,
                    'H': 3.81,  'r0': 1.44,  'r1': 2.57,
                    'rs': 0.416,  'offset': 1.03
                    }
            }

    def __init__(self, obj):
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyEnumeration", "type", "gear_parameter", "type of timing-gear")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty(
            "App::PropertyLength", "pitch", "computed", "pitch off gear", 1)
        obj.addProperty(
            "App::PropertyLength", "h", "computed", "radial height of teeth", 1)
        obj.addProperty(
            "App::PropertyLength", "u", "computed", "radial difference between pitch \
            diameter and head of gear", 1)
        obj.addProperty(
            "App::PropertyLength", "r0", "computed", "radius of first arc", 1)
        obj.addProperty(
            "App::PropertyLength", "r1", "computed", "radius of second arc", 1)
        obj.addProperty(
            "App::PropertyLength", "rs", "computed", "radius of third arc", 1)
        obj.addProperty(
            "App::PropertyLength", "offset", "computed", "x-offset of second arc-midpoint", 1)
        obj.teeth = 15
        obj.type = ['gt2', 'gt3', 'gt5']
        obj.height = '5. mm'

        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
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

        phi_12 = np.arctan(np.sqrt(1. / (((r_12 - r_23) / offset) ** 2 - 1)))
        rp = pitch * fp.teeth / np.pi / 2.
        r4 = r5 = rp - u

        m_12 = np.array([0., r5 - h + r_12])
        m_23 = np.array([offset, offset / np.tan(phi_12) + m_12[1]])
        m_23y = m_23[1]

        # solving for phi4:
        # sympy.solve(
        # ((r5 - r_34) * sin(phi4) + offset) ** 2 + \
        # ((r5 - r_34) * cos(phi4) - m_23y) ** 2 - \
        # ((r_34 + r_23) ** 2), phi4)

        
        phi4 = 2*np.arctan((-2*offset*r5 + 2*offset*r_34 + np.sqrt(-m_23y**4 - 2*m_23y**2*offset**2 + \
        2*m_23y**2*r5**2 - 4*m_23y**2*r5*r_34 + 2*m_23y**2*r_23**2 + \
        4*m_23y**2*r_23*r_34 + 4*m_23y**2*r_34**2 - offset**4 + 2*offset**2*r5**2 - \
        4*offset**2*r5*r_34 + 2*offset**2*r_23**2 + 4*offset**2*r_23*r_34 + 4*offset**2*r_34**2 - \
        r5**4 + 4*r5**3*r_34 + 2*r5**2*r_23**2 + 4*r5**2*r_23*r_34 - \
        4*r5**2*r_34**2 - 4*r5*r_23**2*r_34 - 8*r5*r_23*r_34**2 - r_23**4 - \
        4*r_23**3*r_34 - 4*r_23**2*r_34**2))/(m_23y**2 + 2*m_23y*r5 - \
        2*m_23y*r_34 + offset**2 + r5**2 - 2*r5*r_34 - r_23**2 - 2*r_23*r_34))

        phi5 = np.pi / fp.teeth


        m_34 = (r5 - r_34) * np.array([-np.sin(phi4), np.cos(phi4)])


        x2 = np.array([-r_12 * np.sin(phi_12), m_12[1] - r_12 * np.cos(phi_12)])
        x3 = m_34 + r_34 / (r_34 + r_23) * (m_23 - m_34)
        x4 = r4 * np.array([-np.sin(phi4), np.cos(phi4)])


        ref = reflection(-phi5 - np.pi / 2)
        x6 = ref(x4)
        mir = np.array([-1., 1.])
        xn2 = mir * x2
        xn3 = mir * x3
        xn4 = mir * x4

        mn_34 = mir * m_34
        mn_23 = mir * m_23


        arc_1 = part_arc_from_points_and_center(xn4, xn3, mn_34).toShape()
        arc_2 = part_arc_from_points_and_center(xn3, xn2, mn_23).toShape()
        arc_3 = part_arc_from_points_and_center(xn2, x2, m_12).toShape()
        arc_4 = part_arc_from_points_and_center(x2, x3, m_23).toShape()
        arc_5 = part_arc_from_points_and_center(x3, x4, m_34).toShape()
        arc_6 = part_arc_from_points_and_center(x4, x6, np.array([0. ,0.])).toShape()

        wire = Part.Wire([arc_1, arc_2, arc_3, arc_4, arc_5, arc_6])
        wires = [wire]
        rot = App.Matrix()
        rot.rotateZ(np.pi * 2 / fp.teeth)
        for _ in range(fp.teeth - 1):
            wire = wire.transformGeometry(rot)
            wires.append(wire)

        wi = Part.Wire(wires)
        if fp.height.Value == 0:
            fp.Shape = wi
        else:
            fp.Shape = Part.Face(wi).extrude(App.Vector(0, 0, fp.height))

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass


class LanternGear(object):
    def __init__(self, obj):
        obj.addProperty("App::PropertyInteger",
                        "teeth", "gear_parameter", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "gear_parameter", "module")
        obj.addProperty(
            "App::PropertyLength", "bolt_radius", "gear_parameter", "the bolt radius of the rack/chain")
        obj.addProperty(
            "App::PropertyLength", "height", "gear_parameter", "height")
        obj.addProperty("App::PropertyInteger",
                        "num_profiles", "accuracy", "number of profiles used for loft")
        obj.addProperty(
            "App::PropertyFloat", "head", "gear_parameter", "head * module = additional length of head")

        obj.teeth = 15
        obj.module = '1. mm'
        obj.bolt_radius = '1 mm'
        
        obj.height = '5. mm'
        obj.num_profiles = 10
        
        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        m = fp.module.Value
        teeth = fp.teeth
        r_r = fp.bolt_radius.Value
        r_0 = m * teeth / 2
        r_max = r_0 + r_r + fp.head * m

        phi_max = (r_r + np.sqrt(r_max**2 - r_0**2)) / r_0

        def find_phi_min(phi_min):
            return r_0*(phi_min**2*r_0 - 2*phi_min*r_0*np.sin(phi_min) - \
                   2*phi_min*r_r - 2*r_0*np.cos(phi_min) + 2*r_0 + 2*r_r*np.sin(phi_min))
        try:
            import scipy.optimize
            phi_min = scipy.optimize.root(find_phi_min, (phi_max + r_r / r_0 * 4) / 5).x[0] # , r_r / r_0, phi_max)
        except importError:
            App.Console.Warning("scipy not available. Can't compute numerical root. Leads to a wrong bolt-radius")
            phi_min = r_r / r_0

        # phi_min = 0 # r_r / r_0
        phi = np.linspace(phi_min, phi_max, fp.num_profiles)
        x = r_0 * (np.cos(phi) + phi * np.sin(phi)) - r_r * np.sin(phi)
        y = r_0 * (np.sin(phi) - phi * np.cos(phi)) + r_r * np.cos(phi)
        xy1 = np.array([x, y]).T
        p_1 = xy1[0]
        p_1_end = xy1[-1]
        bsp_1 = BSplineCurve()
        bsp_1.interpolate(list(map(fcvec, xy1)))
        w_1 = bsp_1.toShape()

        xy2 = xy1 * np.array([1., -1.])
        p_2 = xy2[0]
        p_2_end = xy2[-1]
        bsp_2 = BSplineCurve()
        bsp_2.interpolate(list(map(fcvec, xy2)))
        w_2 = bsp_2.toShape()

        p_12 = np.array([r_0 - r_r, 0.])

        arc = Part.Arc(App.Vector(*p_1, 0.), App.Vector(*p_12, 0.), App.Vector(*p_2, 0.)).toShape()

        rot = rotation(-np.pi * 2 / teeth)
        p_3 = rot(np.array([p_2_end]))[0]
        # l = Part.LineSegment(fcvec(p_1_end), fcvec(p_3)).toShape()
        l = part_arc_from_points_and_center(p_1_end, p_3, np.array([0., 0.])).toShape()
        w = Part.Wire([w_2, arc, w_1, l])
        wires = [w]

        rot = App.Matrix()
        for _ in range(teeth - 1):
            rot.rotateZ(np.pi * 2 / teeth)
            wires.append(w.transformGeometry(rot))

        wi = Part.Wire(wires)
        if fp.height.Value == 0:
            fp.Shape = wi
        else:
            fp.Shape = Part.Face(wi).extrude(App.Vector(0, 0, fp.height))

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass

class HypoCycloidGear(object):

    """parameters:
        pressure_angle:  pressureangle,   10-30°
        pitch_angle:  cone angle,      0 < pitch_angle < pi/4
    """

    def __init__(self, obj):
        obj.addProperty("App::PropertyFloat","pin_circle_diameter",     "gear_parameter","Pin bold circle diameter(overrides Tooth Pitch")
        obj.addProperty("App::PropertyFloat","roller_diameter",         "gear_parameter","Roller Diameter")
        obj.addProperty("App::PropertyFloat","eccentricity",            "gear_parameter","Eccentricity")
        obj.addProperty("App::PropertyAngle","pressure_angle_lim",      "gear_parameter","Pressure angle limit")
        obj.addProperty("App::PropertyFloat","pressure_angle_offset",   "gear_parameter","Offset in pressure angle")
        obj.addProperty("App::PropertyInteger","teeth_number",          "gear_parameter","Number of teeth in Cam")
        obj.addProperty("App::PropertyInteger","segment_count",         "gear_parameter","Overall line segments")
        obj.addProperty("App::PropertyLength","hole_radius",            "gear_parameter","Center hole's radius")


        obj.addProperty("App::PropertyBool", "show_pins", "Pins", "Create pins in place")
        obj.addProperty("App::PropertyLength","pin_height", "Pins", "height")
        obj.addProperty("App::PropertyBool", "center_pins", "Pins", "Center pin Z axis to generated disks")

        obj.addProperty("App::PropertyBool", "show_disk0", "Disks", "Show main cam disk")
        obj.addProperty("App::PropertyBool", "show_disk1", "Disks", "Show another reversed cam disk on top")
        obj.addProperty("App::PropertyLength","disk_height", "Disks", "height")

        obj.pin_circle_diameter = 184
        obj.roller_diameter = 6
        obj.eccentricity = 3
        obj.pressure_angle_lim = '50.0 deg'
        obj.pressure_angle_offset = 0.01
        obj.teeth_number = 20
        obj.segment_count = 400
        obj.hole_radius = '30. mm'

        obj.show_pins  = True
        obj.pin_height = '20. mm'
        obj.center_pins= True

        obj.show_disk0 = True
        obj.show_disk1 = True
        obj.disk_height= '10. mm'

        self.obj = obj
        obj.Proxy = self

    def toPolar(self,x, y):
        return (x**2 + y**2)**0.5, math.atan2(y, x)
    def toRect(self,r, a):
        return r*math.cos(a), r*math.sin(a)
    def calcyp(self,p,a,e,n):
        return math.atan(math.sin(n*a)/(math.cos(n*a)+(n*p)/(e*(n+1))))
    def calcX(self,p,d,e,n,a):
        return (n*p)*math.cos(a)+e*math.cos((n+1)*a)-d/2*math.cos(self.calcyp(p,a,e,n)+a)
    def calcY(self,p,d,e,n,a):
        return (n*p)*math.sin(a)+e*math.sin((n+1)*a)-d/2*math.sin(self.calcyp(p,a,e,n)+a)
    def calcPressureAngle(self,p,d,n,a):
        ex = 2**0.5
        r3 = p*n
        rg = r3/ex
        pp = rg * (ex**2 + 1 - 2*ex*math.cos(a))**0.5 - d/2
        return math.asin( (r3*math.cos(a)-rg)/(pp+d/2))*180/math.pi
    def calcPressureLimit(self,p,d,e,n,a):
        ex = 2**0.5
        r3 = p*n
        rg = r3/ex
        q = (r3**2 + rg**2 - 2*r3*rg*math.cos(a))**0.5
        x = rg - e + (q-d/2)*(r3*math.cos(a)-rg)/q
        y = (q-d/2)*r3*math.sin(a)/q
        return (x**2 + y**2)**0.5
    def checkLimit(self,x,y,maxrad,minrad,offset):
        r, a = self.toPolar(x, y)
        if (r > maxrad) or (r < minrad):
                r = r - offset
                x, y = self.toRect(r, a)
        return x, y

    def execute(self,fp):
        b = fp.pin_circle_diameter
        d = fp.roller_diameter
        e = fp.eccentricity
        n = fp.teeth_number
        p = b/n
        s = fp.segment_count
        ang = fp.pressure_angle_lim
        c = fp.pressure_angle_offset

        q = 2*math.pi/float(s)

        # Find the pressure angle limit circles
        minAngle = -1.0
        maxAngle = -1.0
        for i in range(0,180):
            x = self.calcPressureAngle(p,d,n,float(i)*math.pi/180)
            if ( x < ang) and (minAngle < 0):
                minAngle = float(i)
            if (x < -ang) and (maxAngle < 0):
                maxAngle = float(i-1)

        minRadius = self.calcPressureLimit(p,d,e,n,minAngle*math.pi/180)
        maxRadius = self.calcPressureLimit(p,d,e,n,maxAngle*math.pi/180)
        Wire(Part.makeCircle(minRadius,App.Vector(-e,0,0)))
        Wire(Part.makeCircle(maxRadius,App.Vector(-e,0,0)))

        App.Console.PrintMessage("Generating cam disk\r\n")
        #generate the cam profile - note: shifted in -x by eccentricicy amount
        i=0
        x = self.calcX(p,d,e,n,q*i)
        y = self.calcY(p,d,e,n,q*i)
        x,y = self.checkLimit(x,y,maxRadius,minRadius,c)
        points = [App.Vector(x-e,y,0)]
        for i in range(0,s):
            x = self.calcX(p,d,e,n,q*(i+1))
            y = self.calcY(p,d,e,n,q*(i+1))
            x, y = self.checkLimit(x,y,maxRadius, minRadius, c)
            points.append(App.Vector(x-e,y,0))

        cam = Face(Wire(makePolygon(points)))
        #add a circle in the center of the cam
        centerCircle = Face(Wire(Part.makeCircle(fp.hole_radius.Value,App.Vector(-e,0,0))))
        cam = cam.cut(centerCircle)

        to_be_fused = []
        if fp.show_disk0==True:
            if fp.disk_height.Value==0:
                to_be_fused.append(cam)
            else:
                to_be_fused.append(cam.extrude(App.Vector(0,0,fp.disk_height.Value)))

        #secondary cam disk
        if fp.show_disk1==True:
            App.Console.PrintMessage("Generating secondary cam disk\r\n")
            second_cam = cam.copy()
            mat= App.Matrix()
            mat.rotateZ(np.pi)
            mat.move(App.Vector(-e,0,0))
            mat.rotateZ(np.pi/n)
            mat.move(App.Vector(e,0,0))
            second_cam = second_cam.transformGeometry(mat)
            if fp.disk_height.Value==0:
                to_be_fused.append(second_cam)
            else:
                to_be_fused.append(second_cam.extrude(App.Vector(0,0,-fp.disk_height.Value)))

        #pins
        if fp.show_pins==True:
            App.Console.PrintMessage("Generating pins\r\n")
            pins = []
            for i in range(0,n+1):
                x = p*n*math.cos(2*math.pi/(n+1)*i)
                y = p*n*math.sin(2*math.pi/(n+1)*i)
                pins.append(Wire(Part.makeCircle(d/2,App.Vector(x,y,0))))

            pins = Face(pins)

            z_offset = -fp.pin_height.Value/2;

            if fp.center_pins==True:
                if fp.show_disk0==True and fp.show_disk1==False:
                    z_offset += fp.disk_height.Value/2;
                elif fp.show_disk0==False and fp.show_disk1==True:
                    z_offset += -fp.disk_height.Value/2;
            #extrude
            if z_offset!=0:
                pins.translate(App.Vector(0,0,z_offset))
            if fp.pin_height!=0:
                pins = pins.extrude(App.Vector(0,0,fp.pin_height.Value))

            to_be_fused.append(pins);

        if to_be_fused:
            fp.Shape = Part.makeCompound(to_be_fused)

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass

def part_arc_from_points_and_center(p_1, p_2, m):
    p_1, p_12, p_2 = arc_from_points_and_center(p_1, p_2, m)
    return Part.Arc(App.Vector(*p_1, 0.), App.Vector(*p_12, 0.), App.Vector(*p_2, 0.))


def helicalextrusion(wire, height, angle, double_helix=False):
    direction = bool(angle < 0)
    if double_helix:
        first_spine = makeHelix(height * 2. * np.pi /
                                abs(angle), 0.5 * height, 10., 0, direction)
        first_solid = first_spine.makePipeShell([wire], True, True)
        second_solid = first_solid.mirror(
            fcvec([0., 0., 0.]), fcvec([0, 0, 1]))
        faces = first_solid.Faces + second_solid.Faces
        faces = [f for f in faces if not on_mirror_plane(
            f, 0., fcvec([0., 0., 1.]))]
        solid = makeSolid(makeShell(faces))
        mat = App.Matrix()
        mat.move(fcvec([0, 0, 0.5 * height]))
        return solid.transformGeometry(mat)
    else:
        first_spine = makeHelix(height * 2 * np.pi /
                                abs(angle), height, 10., 0, direction)
        first_solid = first_spine.makePipeShell([wire], True, True)
        return first_solid


def make_face(edge1, edge2):
    v1, v2 = edge1.Vertexes
    v3, v4 = edge2.Vertexes
    e1 = Wire(edge1)
    e2 = Line(v1.Point, v3.Point).toShape().Edges[0]
    e3 = edge2
    e4 = Line(v4.Point, v2.Point).toShape().Edges[0]
    w = Wire([e3, e4, e1, e2])
    return(Face(w))


def makeBSplineWire(pts):
    wi = []
    for i in pts:
        out = BSplineCurve()
        out.interpolate(list(map(fcvec, i)))
        wi.append(out.toShape())
    return Wire(wi)


def on_mirror_plane(face, z, direction, small_size=0.000001):
    # the tolerance is very high. Maybe there is a bug in Part.makeHelix.
    return (face.normalAt(0, 0).cross(direction).Length < small_size and
            abs(face.CenterOfMass.z - z) < small_size)
