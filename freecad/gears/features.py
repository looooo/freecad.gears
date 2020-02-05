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
from pygears.involute_tooth import InvoluteTooth, InvoluteRack
from pygears.cycloide_tooth import CycloideTooth
from pygears.bevel_tooth import BevelTooth
from pygears._functions import rotation3D, rotation


import FreeCAD as App
import Part
from Part import BSplineCurve, Shape, Wire, Face, makePolygon, \
    BRepOffsetAPI, Shell, makeLoft, Solid, Line, BSplineSurface, makeCompound,\
    show, makePolygon, makeHelix, makeShell, makeSolid


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
            if fp.beta.Value == 0:
                sh = Face(wi)
                fp.Shape = sh.extrude(App.Vector(0, 0, fp.height.Value))
            else:
                fp.Shape = helicalextrusion(
                    wi, fp.height.Value, fp.height.Value * np.tan(fp.gear.beta) * 2 / fp.gear.d, fp.double_helix)
        else:
            rw = fp.gear.dw / 2
            fp.Shape = Part.makeCylinder(rw, fp.height.Value)

        fp.dw = "{}mm".format(fp.gear.dw)

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
            "App::PropertyFloat", "head", "gear_parameter", "head_value * modul_value = additional length of head")
        obj.addProperty(
            "App::PropertyFloat", "clearence", "gear_parameter", "head_value * modul_value = additional length of foot")
        obj.addProperty(
            "App::PropertyBool", "properties_from_tool", "gear_parameter", "if beta is given and properties_from_tool is enabled, \
            gear parameters are internally recomputed for the rotated gear")
        obj.addProperty("App::PropertyLength", "transverse_pitch",
            "computed", "pitch in the transverse plane", 1)
        obj.addProperty("App::PropertyPythonObject", "rack", "test", "test")
        obj.rack = self.involute_rack
        obj.teeth = 15
        obj.module = '1. mm'
        obj.pressure_angle = '20. deg'
        obj.height = '5. mm'
        obj.thickness = '5 mm'
        obj.beta = '0. deg'
        obj.clearence = 0.25
        obj.head = 0.
        obj.properties_from_tool = True
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
        if "clearence" in fp.PropertiesList:
            fp.rack.clearence = fp.clearence
        if "properties_from_tool" in fp.PropertiesList:
            fp.rack.properties_from_tool = fp.properties_from_tool
        fp.rack._update()
        pts = fp.rack.points()
        pol = Wire(makePolygon(list(map(fcvec, pts))))
        if fp.beta.Value == 0:
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
        if fp.beta.Value == 0:
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
        obj.addProperty("App::PropertyLength", "m", "gear_parameter", "m")
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
        obj.m = '1. mm'
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
        fp.gear.module = fp.m.Value
        fp.gear.pressure_angle = (90 - fp.pressure_angle.Value) * np.pi / 180.
        fp.gear.pitch_angle = fp.pitch_angle.Value * np.pi / 180
        fp.gear.backlash = fp.backlash.Value
        scale = fp.m.Value * fp.gear.z / 2 / \
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
        obj.teeth = 3
        obj.module = '1. mm'
        obj.pressure_angle = '20. deg'
        obj.height = '5. mm'
        obj.diameter = '5. mm'
        self.obj = obj
        obj.Proxy = self

    def execute(self, fp):
        m = fp.module.Value
        d = fp.diameter.Value
        t = fp.teeth
        h = fp.height
        alpha = fp.pressure_angle.Value
        beta = np.arctan(m * t / d)
        fp.beta = np.rad2deg(beta)
        beta = np.pi / 2 - beta

        r_1 = (d - 2 * m) / 2
        r_2 = (d + 2 * m) / 2
        z_a = 2 * m * np.tan(np.deg2rad(alpha))
        z_4 = m * np.pi
        z_2 = z_4 / 2
        z_1 = z_2 - z_a
        z_3 = z_4 - z_a

        def helical_projection(r, z):
            phi = 2 * z / m / t
            x = r * np.cos(phi)
            y = r * np.sin(phi)
            z = 0 * y
            return np.array([x, y, z]). T

        # create a circle from phi=0 to phi_1 with r_1
        phi_1 = 2 * z_1 / m / t
        c1 = Part.makeCircle(r_1, App.Vector(0, 0, 0),
                             App.Vector(0, 0, 1), 0, np.rad2deg(phi_1))

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
        shape = helicalextrusion(full_wire, h, h * np.tan(beta) * 2 / d)
        fp.Shape = shape

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


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
