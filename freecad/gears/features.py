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

from __future__ import division
import os
import copy

import numpy as np
import math
from pygears import __version__
from pygears.involute_tooth import InvoluteTooth, InvoluteRack
from pygears.cycloid_tooth import CycloidTooth
from pygears.bevel_tooth import BevelTooth
from pygears._functions import rotation3D, rotation, reflection, arc_from_points_and_center


import FreeCAD as App
import Part
from Part import BSplineCurve, Shape, Wire, Face, makePolygon, \
    makeLoft, BSplineSurface, \
    makePolygon, makeHelix, makeShell, makeSolid, LineSegment


__all__ = ["InvoluteGear",
           "CycloidGear",
           "BevelGear",
           "InvoluteGearRack",
           "CrownGear",
           "WormGear",
           "HypoCycloidGear",
           "ViewProviderGear"]


def fcvec(x):
    if len(x) == 2:
        return(App.Vector(x[0], x[1], 0))
    else:
        return(App.Vector(x[0], x[1], x[2]))


class ViewProviderGear(object):
    def __init__(self, obj, icon_fn=None):
        # Set this object to the proxy object of the actual view provider
        obj.Proxy = self
        self._check_attr()
        dirname = os.path.dirname(__file__)
        self.icon_fn = icon_fn or os.path.join(dirname, "icons", "involutegear.svg")
            
    def _check_attr(self):
        ''' Check for missing attributes. '''
        if not hasattr(self, "icon_fn"):
            setattr(self, "icon_fn", os.path.join(os.path.dirname(__file__), "icons", "involutegear.svg"))

    def attach(self, vobj):
        self.vobj = vobj

    def getIcon(self):
        self._check_attr()
        return self.icon_fn

    def __getstate__(self):
        self._check_attr()
        return {"icon_fn": self.icon_fn}

    def __setstate__(self, state):
        if state and "icon_fn" in state:
            self.icon_fn = state["icon_fn"]

class BaseGear(object):
    def __init__(self, obj):
        obj.addProperty("App::PropertyString", "version", "version", "freecad.gears-version", 1)
        obj.version = __version__
        self.make_attachable(obj)

    def make_attachable(self, obj):
        # Needed to make this object "attachable",
        # aka able to attach parameterically to other objects
        # cf. https://wiki.freecadweb.org/Scripted_objects_with_attachment
        if int(App.Version()[1]) >= 19:
            obj.addExtension('Part::AttachExtensionPython')
        else:
            obj.addExtension('Part::AttachExtensionPython', obj)
        # unveil the "Placement" property, which seems hidden by default in PartDesign
        obj.setEditorMode('Placement', 0) #non-readonly non-hidden

    def execute(self, fp):
        # checksbackwardcompatibility:
        if not hasattr(fp, "positionBySupport"):
            self.make_attachable(fp)
        fp.positionBySupport()
        gear_shape = self.generate_gear_shape(fp)
        if hasattr(fp, "BaseFeature") and fp.BaseFeature != None:
            # we're inside a PartDesign Body, thus need to fuse with the base feature
            gear_shape.Placement = fp.Placement # ensure the gear is placed correctly before fusing
            result_shape = fp.BaseFeature.Shape.fuse(gear_shape)
            result_shape.transformShape(fp.Placement.inverse().toMatrix(), True) # account for setting fp.Shape below moves the shape to fp.Placement, ignoring its previous placement
            fp.Shape = result_shape
        else:
            fp.Shape = gear_shape

    def generate_gear_shape(self, fp):
        """
        This method has to return the TopoShape of the gear.
        """
        raise NotImplementedError("generate_gear_shape not implemented")

class InvoluteGear(BaseGear):

    """FreeCAD gear"""

    def __init__(self, obj):
        super(InvoluteGear, self).__init__(obj)
        self.involute_tooth = InvoluteTooth()

        obj.addProperty("App::PropertyPythonObject",
                        "gear", "base", "python gear object")

        self.add_gear_properties(obj)
        self.add_fillet_properties(obj)
        self.add_helical_properties(obj)
        self.add_computed_properties(obj)
        self.add_tolerance_properties(obj)
        self.add_accuracy_properties(obj)

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
        obj.properties_from_tool = False
        obj.head_fillet = 0
        obj.root_fillet = 0
        self.obj = obj
        obj.Proxy = self
        self.compute_traverse_properties(obj)

    def add_gear_properties(self, obj):
        obj.addProperty("App::PropertyInteger", "teeth", "base", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "base", "normal module if properties_from_tool=True, \
                                                                else it's the transverse module.")
        obj.addProperty(
            "App::PropertyLength", "height", "base", "height")
        obj.addProperty(
            "App::PropertyAngle", "pressure_angle", "involute", "pressure angle")
        obj.addProperty("App::PropertyFloat", "shift", "involute", "shift")

    def add_fillet_properties(self, obj):
        obj.addProperty("App::PropertyBool", "undercut", "fillets", "undercut")
        obj.addProperty("App::PropertyFloat", "head_fillet", "fillets",
                        "a fillet for the tooth-head, radius = head_fillet x module")
        obj.addProperty("App::PropertyFloat", "root_fillet", "fillets",
                        "a fillet for the tooth-root, radius = root_fillet x module")

    def add_helical_properties(self, obj):
        obj.addProperty("App::PropertyBool", "properties_from_tool",
                        "helical", "if beta is given and properties_from_tool is enabled, \
                         gear parameters are internally recomputed for the rotated gear")
        obj.addProperty("App::PropertyAngle", "beta", "helical", "beta ")
        obj.addProperty("App::PropertyBool", "double_helix", "helical", "double helix")

    def add_computed_properties(self, obj):
        obj.addProperty("App::PropertyLength", "da",
                        "computed", "outside diameter", 1)
        obj.addProperty("App::PropertyLength", "df",
                        "computed", "root diameter", 1)
        obj.addProperty("App::PropertyLength", "traverse_module", "computed", "traverse module of the generated gear", 1)
        obj.addProperty("App::PropertyLength", "dw", "computed", "The pitch diameter.", 1)
        obj.addProperty("App::PropertyAngle", "angular_backlash", "computed",
            "The angle by which this gear can turn without moving the mating gear.")
        obj.setExpression('angular_backlash', 'backlash / dw * 360° / pi') # calculate via expression to ease usage for placement
        obj.setEditorMode('angular_backlash', 1) # set read-only after setting the expression, else it won't be visible. bug?
        obj.addProperty("App::PropertyLength", "transverse_pitch",
                        "computed", "transverse_pitch", 1)

    def add_tolerance_properties(self, obj):
        obj.addProperty("App::PropertyLength", "backlash", "tolerance",
            "The arc length on the pitch circle by which the tooth thicknes is reduced.")
        obj.addProperty("App::PropertyBool", "reversed_backlash", "tolerance", "backlash direction")
        obj.addProperty(
            "App::PropertyFloat", "clearance", "tolerance", "clearance")
        obj.addProperty(
            "App::PropertyFloat", "head", "tolerance", "head_value * modul_value = additional length of head")

    def add_accuracy_properties(self, obj):
        obj.addProperty("App::PropertyBool", "simple", "accuracy", "simple")
        obj.addProperty("App::PropertyInteger", "numpoints",
                        "accuracy", "number of points for spline")

    def compute_traverse_properties(self, obj):
        if obj.properties_from_tool:
            obj.traverse_module = obj.module / np.cos(obj.gear.beta)
        else:
            obj.traverse_module = obj.module

        obj.transverse_pitch = "{}mm".format(obj.gear.pitch)
        obj.da = "{}mm".format(obj.gear.da)
        obj.df = "{}mm".format(obj.gear.df)
        obj.dw = "{}mm".format(obj.gear.dw)

    def generate_gear_shape(self, obj):
        obj.gear.double_helix = obj.double_helix
        obj.gear.m_n = obj.module.Value
        obj.gear.z = obj.teeth
        obj.gear.undercut = obj.undercut
        obj.gear.shift = obj.shift
        obj.gear.pressure_angle = obj.pressure_angle.Value * np.pi / 180.
        obj.gear.beta = obj.beta.Value * np.pi / 180
        obj.gear.clearance = obj.clearance
        obj.gear.backlash = obj.backlash.Value * \
            (-obj.reversed_backlash + 0.5) * 2.
        obj.gear.head = obj.head
        obj.gear.properties_from_tool = obj.properties_from_tool

        obj.gear._update()
        self.compute_traverse_properties(obj)


        if not obj.simple:

            pts = obj.gear.points(num=obj.numpoints)
            rot = rotation(-obj.gear.phipart)
            rotated_pts = list(map(rot, pts))
            pts.append([pts[-1][-1],rotated_pts[0][0]])
            pts += rotated_pts
            tooth = points_to_wire(pts)
            edges = tooth.Edges

            # head-fillet:
            r_head = float(obj.head_fillet * obj.module)
            r_root = float(obj.root_fillet * obj.module)
            if obj.undercut and r_root != 0.:
                r_root = 0.
                App.Console.PrintWarning("root fillet is not allowed if undercut is computed")
            if len(tooth.Edges) == 11:
                pos_head = [1, 3, 9]
                pos_root = [6, 8]
                edge_range = [2, 12]
            else:
                pos_head = [0, 2, 6]
                pos_root = [4, 6]
                edge_range = [1, 9]

            for pos in pos_head:
                edges = insert_fillet(edges, pos, r_head)

            for pos in pos_root:
                try:
                    edges = insert_fillet(edges, pos, r_root)
                except RuntimeError:
                    edges.pop(8)
                    edges.pop(6)
                    edge_range = [2, 10]
                    pos_root = [5, 7]
                    for pos in pos_root:
                        edges = insert_fillet(edges, pos, r_root)
                    break
            edges = edges[edge_range[0]:edge_range[1]]
            edges = [e for e in edges if e is not None]

            tooth = Wire(edges)
            profile = rotate_tooth(tooth, obj.teeth)

            if obj.height.Value == 0:
                return profile
            base = Face(profile)
            if obj.beta.Value == 0:
                return base.extrude(App.Vector(0, 0, obj.height.Value))
            else:
                twist_angle = obj.height.Value * np.tan(obj.gear.beta) * 2 / obj.gear.d
                return helicalextrusion(base, obj.height.Value, twist_angle, obj.double_helix)
        else:
            rw = obj.gear.dw / 2
            return Part.makeCylinder(rw, obj.height.Value)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class InternalInvoluteGear(BaseGear):
    """FreeCAD internal involute gear

    Using the same tooth as the external, just turning it inside-out:
    addedum becomes dedendum, clearance becomes head, negate the backslash, ...
    """

    def __init__(self, obj):
        super(InternalInvoluteGear, self).__init__(obj)
        self.involute_tooth = InvoluteTooth()
        obj.addProperty(
            "App::PropertyBool", "simple", "precision", "simple")
        obj.addProperty("App::PropertyInteger", "teeth", "base", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "base", "normal module if properties_from_tool=True, \
                                                                else it's the transverse module.")
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty("App::PropertyLength", "thickness", "base", "thickness")
        obj.addProperty("App::PropertyInteger", "numpoints",
                        "accuracy", "number of points for spline")
        obj.addProperty("App::PropertyPythonObject", "gear", "base", "test")

        self.add_involute_properties(obj)
        self.add_tolerance_properties(obj)
        self.add_fillet_properties(obj)
        self.add_computed_properties(obj)
        self.add_limiting_diameter_properties(obj)
        self.add_helical_properties(obj)

        obj.gear = self.involute_tooth
        obj.simple = False
        obj.teeth = 15
        obj.module = '1. mm'
        obj.shift = 0.
        obj.pressure_angle = '20. deg'
        obj.beta = '0. deg'
        obj.height = '5. mm'
        obj.thickness = '5 mm'
        obj.clearance = 0.25
        obj.head = -0.4 # using head=0 and shift=0.5 may be better, but makes placeing the pinion less intuitive
        obj.numpoints = 6
        obj.double_helix = False
        obj.backlash = '0.00 mm'
        obj.reversed_backlash = False
        obj.properties_from_tool = False
        obj.head_fillet = 0
        obj.root_fillet = 0
        self.obj = obj
        obj.Proxy = self

    def add_limiting_diameter_properties(self, obj):
        obj.addProperty("App::PropertyLength", "da",
                        "computed", "inside diameter", 1)
        obj.addProperty("App::PropertyLength", "df",
                        "computed", "root diameter", 1)

    def add_computed_properties(self, obj):
        obj.addProperty("App::PropertyLength", "dw", "computed", "The pitch diameter.")
        obj.addProperty("App::PropertyAngle", "angular_backlash", "computed",
            "The angle by which this gear can turn without moving the mating gear.")
        obj.setExpression('angular_backlash', 'backlash / dw * 360° / pi') # calculate via expression to ease usage for placement
        obj.setEditorMode('angular_backlash', 1) # set read-only after setting the expression, else it won't be visible. bug?
        obj.addProperty("App::PropertyLength", "transverse_pitch", "computed", "transverse_pitch", 1)
        obj.addProperty("App::PropertyLength", "outside_diameter", "computed", "Outside diameter", 1)

    def add_fillet_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "head_fillet", "fillets", "a fillet for the tooth-head, radius = head_fillet x module")
        obj.addProperty("App::PropertyFloat", "root_fillet", "fillets", "a fillet for the tooth-root, radius = root_fillet x module")

    def add_tolerance_properties(self, obj):
        obj.addProperty("App::PropertyLength", "backlash", "tolerance",
            "The arc length on the pitch circle by which the tooth thicknes is reduced.")
        obj.addProperty("App::PropertyBool", "reversed_backlash", "tolerance", "backlash direction")
        obj.addProperty("App::PropertyFloat", "head", "tolerance", "head_value * modul_value = additional length of head")
        obj.addProperty("App::PropertyFloat", "clearance", "tolerance", "clearance")

    def add_involute_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "shift", "involute", "shift")
        obj.addProperty("App::PropertyAngle", "pressure_angle", "involute", "pressure angle")

    def add_helical_properties(self, obj):
        obj.addProperty("App::PropertyAngle", "beta", "helical", "beta ")
        obj.addProperty("App::PropertyBool", "double_helix", "helical", "double helix")
        obj.addProperty(
            "App::PropertyBool", "properties_from_tool", "helical", "if beta is given and properties_from_tool is enabled, \
            gear parameters are internally recomputed for the rotated gear")

    def generate_gear_shape(self, fp):
        fp.gear.double_helix = fp.double_helix
        fp.gear.m_n = fp.module.Value
        fp.gear.z = fp.teeth
        fp.gear.undercut = False # no undercut for internal gears
        fp.gear.shift = fp.shift
        fp.gear.pressure_angle = fp.pressure_angle.Value * np.pi / 180.
        fp.gear.beta = fp.beta.Value * np.pi / 180
        fp.gear.clearance = fp.head # swap head and clearance to become "internal"
        fp.gear.backlash = fp.backlash.Value * \
            (fp.reversed_backlash - 0.5) * 2. # negate "reversed_backslash", for "internal"
        fp.gear.head = fp.clearance # swap head and clearance to become "internal"
        fp.gear.properties_from_tool = fp.properties_from_tool
        fp.gear._update()

        fp.dw = "{}mm".format(fp.gear.dw)
        
        # computed properties
        fp.transverse_pitch = "{}mm".format(fp.gear.pitch)
        fp.outside_diameter = fp.dw + 2 * fp.thickness
        # checksbackwardcompatibility:
        if not "da" in fp.PropertiesList:
            self.add_limiting_diameter_properties(fp)
        fp.da = "{}mm".format(fp.gear.df) # swap addednum and dedendum for "internal"
        fp.df = "{}mm".format(fp.gear.da) # swap addednum and dedendum for "internal"


        outer_circle = Part.Wire(Part.makeCircle(fp.outside_diameter / 2.))
        outer_circle.reverse()
        if not fp.simple:
            # head-fillet:
            pts = fp.gear.points(num=fp.numpoints)
            rot = rotation(-fp.gear.phipart)
            rotated_pts = list(map(rot, pts))
            pts.append([pts[-1][-1],rotated_pts[0][0]])
            pts += rotated_pts
            tooth = points_to_wire(pts)
            r_head = float(fp.root_fillet * fp.module)  # reversing head
            r_root = float(fp.head_fillet * fp.module)  # and foot
            edges = tooth.Edges
            if len(tooth.Edges) == 11:
                pos_head = [1, 3, 9]
                pos_root = [6, 8]
                edge_range = [2, 12]
            else:
                pos_head = [0, 2, 6]
                pos_root = [4, 6]
                edge_range = [1, 9]

            for pos in pos_head:
                edges = insert_fillet(edges, pos, r_head)

            for pos in pos_root:
                try:
                    edges = insert_fillet(edges, pos, r_root)
                except RuntimeError:
                    edges.pop(8)
                    edges.pop(6)
                    edge_range = [2, 10]
                    pos_root = [5, 7]
                    for pos in pos_root:
                        edges = insert_fillet(edges, pos, r_root)
                    break
            edges = edges[edge_range[0]:edge_range[1]]
            edges = [e for e in edges if e is not None]

            tooth = Wire(edges)
            profile = rotate_tooth(tooth, fp.teeth)
            if fp.height.Value == 0:
                return Part.makeCompound([outer_circle, profile])
            base = Face([outer_circle, profile])
            if fp.beta.Value == 0:
                return base.extrude(App.Vector(0, 0, fp.height.Value))
            else:
                twist_angle = fp.height.Value * np.tan(fp.gear.beta) * 2 / fp.gear.d
                return helicalextrusion(base, fp.height.Value, twist_angle, fp.double_helix)
        else:
            inner_circle = Part.Wire(Part.makeCircle(fp.dw / 2.))
            inner_circle.reverse()
            base = Face([outer_circle, inner_circle])
            return base.extrude(App.Vector(0, 0, fp.height.Value))

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class InvoluteGearRack(BaseGear):

    """FreeCAD gear rack"""

    def __init__(self, obj):
        super(InvoluteGearRack, self).__init__(obj)
        self.involute_rack = InvoluteRack()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "base", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "height", "base", "height")
        obj.addProperty(
            "App::PropertyLength", "module", "base", "module")
        obj.addProperty(
            "App::PropertyLength", "thickness", "base", "thickness")
        obj.addProperty(
            "App::PropertyBool", "simplified", "precision", "if enabled the rack is drawn with a constant number of \
            teeth to avoid topologic renaming.")
        obj.addProperty("App::PropertyPythonObject", "rack", "base", "test")

        self.add_helical_properties(obj)
        self.add_computed_properties(obj)
        self.add_tolerance_properties(obj)
        self.add_involute_properties(obj)
        self.add_fillet_properties(obj)
        obj.rack = self.involute_rack
        obj.teeth = 15
        obj.module = '1. mm'
        obj.pressure_angle = '20. deg'
        obj.height = '5. mm'
        obj.thickness = '5 mm'
        obj.beta = '0. deg'
        obj.clearance = 0.25
        obj.head = 0.
        obj.properties_from_tool = False
        obj.add_endings = True
        obj.simplified = False
        self.obj = obj
        obj.Proxy = self

    def add_helical_properties(self, obj):
        obj.addProperty(
            "App::PropertyBool", "properties_from_tool", "helical", "if beta is given and properties_from_tool is enabled, \
            gear parameters are internally recomputed for the rotated gear")
        obj.addProperty(
            "App::PropertyAngle", "beta", "helical", "beta ")
        obj.addProperty(
            "App::PropertyBool", "double_helix", "helical", "double helix")

    def add_computed_properties(self, obj):
        obj.addProperty("App::PropertyLength", "transverse_pitch",
            "computed", "pitch in the transverse plane", 1)
        obj.addProperty("App::PropertyBool", "add_endings", "base", "if enabled the total length of the rack is teeth x pitch, \
            otherwise the rack starts with a tooth-flank")

    def add_tolerance_properties(self, obj):
        obj.addProperty(
            "App::PropertyFloat", "head", "tolerance", "head * module = additional length of head")
        obj.addProperty(
            "App::PropertyFloat", "clearance", "tolerance", "clearance * module = additional length of root")

    def add_involute_properties(self, obj):
        obj.addProperty(
            "App::PropertyAngle", "pressure_angle", "involute", "pressure angle")

    def add_fillet_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "head_fillet", "fillets", "a fillet for the tooth-head, radius = head_fillet x module")
        obj.addProperty("App::PropertyFloat", "root_fillet", "fillets", "a fillet for the tooth-root, radius = root_fillet x module")

    def generate_gear_shape(self, obj):
        obj.rack.m = obj.module.Value
        obj.rack.z = obj.teeth
        obj.rack.pressure_angle = obj.pressure_angle.Value * np.pi / 180.
        obj.rack.thickness = obj.thickness.Value
        obj.rack.beta = obj.beta.Value * np.pi / 180.
        obj.rack.head = obj.head
        # checksbackwardcompatibility:
        if "clearance" in obj.PropertiesList:
            obj.rack.clearance = obj.clearance
        if "properties_from_tool" in obj.PropertiesList:
            obj.rack.properties_from_tool = obj.properties_from_tool
        if "add_endings" in obj.PropertiesList:
            obj.rack.add_endings = obj.add_endings
        if "simplified" in obj.PropertiesList:
            obj.rack.simplified = obj.simplified
        obj.rack._update()
        m, m_n, pitch, pressure_angle_t = obj.rack.compute_properties()
        obj.transverse_pitch = "{} mm".format(pitch)
        t = obj.thickness.Value
        c = obj.clearance
        h = obj.head
        alpha = obj.pressure_angle.Value * np.pi / 180.
        head_fillet = obj.head_fillet
        root_fillet = obj.root_fillet
        x1 = -m * np.pi / 2
        y1 = -m * (1 + c)
        y2 = y1
        x2 = -m * np.pi / 4 + y2 * np.tan(alpha)
        y3 = m * (1 + h)
        x3 = -m * np.pi / 4 + y3 * np.tan(alpha)
        x4 = -x3
        x5 = -x2
        x6 = -x1
        y4 = y3
        y5 = y2
        y6 = y1
        p1 = np.array([y1, x1])
        p2 = np.array([y2, x2])
        p3 = np.array([y3, x3])
        p4 = np.array([y4, x4])
        p5 = np.array([y5, x5])
        p6 = np.array([y6, x6])
        line1 = [p1, p2]
        line2 = [p2, p3]
        line3 = [p3, p4]
        line4 = [p4, p5]
        line5 = [p5, p6]
        tooth = Wire(points_to_wire([line1, line2, line3, line4, line5]))

        edges = tooth.Edges
        edges = insert_fillet(edges, 0, m * root_fillet)
        edges = insert_fillet(edges, 2, m * head_fillet)
        edges = insert_fillet(edges, 4, m * head_fillet)
        edges = insert_fillet(edges, 6, m * root_fillet)

        tooth_edges = [e for e in edges if e is not None]
        p_end = np.array(tooth_edges[-2].lastVertex().Point[:-1])
        p_start = np.array(tooth_edges[1].firstVertex().Point[:-1])
        p_start += np.array([0, np.pi * m])
        edge = points_to_wire([[p_end, p_start]]).Edges
        tooth = Wire(tooth_edges[1:-1] + edge)
        teeth = [tooth]

        for i in range(obj.teeth - 1):
            tooth = copy.deepcopy(tooth)
            tooth.translate(App.Vector(0, np.pi * m, 0))
            teeth.append(tooth)

        teeth[-1] = Wire(teeth[-1].Edges[:-1])

        if obj.add_endings:
            teeth = [Wire(tooth_edges[0])] + teeth
            last_edge = tooth_edges[-1]
            last_edge.translate(App.Vector(0, np.pi * m * (obj.teeth - 1), 0))
            teeth = teeth + [Wire(last_edge)]

        p_start = np.array(teeth[0].Edges[0].firstVertex().Point[:-1])
        p_end = np.array(teeth[-1].Edges[-1].lastVertex().Point[:-1])
        p_start_1 = p_start - np.array([obj.thickness.Value, 0.])
        p_end_1 = p_end - np.array([obj.thickness.Value, 0.])

        line6 = [p_start, p_start_1]
        line7 = [p_start_1, p_end_1]
        line8 = [p_end_1, p_end]

        bottom = points_to_wire([line6, line7, line8])

        pol = Wire([bottom] + teeth)

        if obj.height.Value == 0:
            return pol
        elif obj.beta.Value == 0:
            face = Face(Wire(pol))
            return face.extrude(fcvec([0., 0., obj.height.Value]))
        elif obj.double_helix:
            beta = obj.beta.Value * np.pi / 180.
            pol2 = Part.Wire(pol)
            pol2.translate(
                fcvec([0., np.tan(beta) * obj.height.Value / 2, obj.height.Value / 2]))
            pol3 = Part.Wire(pol)
            pol3.translate(fcvec([0., 0., obj.height.Value]))
            return makeLoft([pol, pol2, pol3], True, True)
        else:
            beta = obj.beta.Value * np.pi / 180.
            pol2 = Part.Wire(pol)
            pol2.translate(
                fcvec([0., np.tan(beta) * obj.height.Value, obj.height.Value]))
            return makeLoft([pol, pol2], True)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class CycloidGearRack(BaseGear):

    """FreeCAD gear rack"""

    def __init__(self, obj):
        super(CycloidGearRack, self).__init__(obj)
        obj.addProperty("App::PropertyInteger",
                        "teeth", "base", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "height", "base", "height")
        obj.addProperty(
            "App::PropertyLength", "thickness", "base", "thickness")
        obj.addProperty(
            "App::PropertyLength", "module", "involute", "module")
        obj.addProperty(
            "App::PropertyBool", "simplified", "precision", "if enabled the rack is drawn with a constant number of \
            teeth to avoid topologic renaming.")
        obj.addProperty("App::PropertyInteger", "numpoints", "accuracy", "number of points for spline")
        obj.addProperty("App::PropertyPythonObject", "rack", "base", "test")

        self.add_helical_properties(obj)
        self.add_computed_properties(obj)
        self.add_tolerance_properties(obj)
        self.add_cycloid_properties(obj)
        self.add_fillet_properties(obj)
        obj.teeth = 15
        obj.module = '1. mm'
        obj.inner_diameter = 7.5
        obj.outer_diameter = 7.5
        obj.height = '5. mm'
        obj.thickness = '5 mm'
        obj.beta = '0. deg'
        obj.clearance = 0.25
        obj.head = 0.
        obj.add_endings = True
        obj.simplified = False
        obj.numpoints = 15
        self.obj = obj
        obj.Proxy = self

    def add_helical_properties(self, obj):
        obj.addProperty(
            "App::PropertyAngle", "beta", "helical", "beta ")
        obj.addProperty(
            "App::PropertyBool", "double_helix", "helical", "double helix")

    def add_computed_properties(self, obj):
        obj.addProperty("App::PropertyLength", "transverse_pitch",
            "computed", "pitch in the transverse plane", 1)
        obj.addProperty("App::PropertyBool", "add_endings", "base", "if enabled the total length of the rack is teeth x pitch, \
            otherwise the rack starts with a tooth-flank")

    def add_tolerance_properties(self, obj):
        obj.addProperty(
            "App::PropertyFloat", "head", "tolerance", "head * module = additional length of head")
        obj.addProperty(
            "App::PropertyFloat", "clearance", "tolerance", "clearance * module = additional length of root")

    def add_cycloid_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "inner_diameter", "cycloid", "inner_diameter divided by module (hypocycloid)")
        obj.addProperty("App::PropertyFloat", "outer_diameter", "cycloid", "outer_diameter divided by module (epicycloid)")

    def add_fillet_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "head_fillet", "fillets", "a fillet for the tooth-head, radius = head_fillet x module")
        obj.addProperty("App::PropertyFloat", "root_fillet", "fillets", "a fillet for the tooth-root, radius = root_fillet x module")
    
    def generate_gear_shape(self, obj):
        numpoints = obj.numpoints
        m = obj.module.Value
        t = obj.thickness.Value
        r_i = obj.inner_diameter / 2 * m
        r_o = obj.outer_diameter / 2 * m
        c = obj.clearance
        h = obj.head
        head_fillet = obj.head_fillet
        root_fillet = obj.root_fillet
        phi_i_end = np.arccos(1 - m / r_i * (1 + c))
        phi_o_end = np.arccos(1 - m / r_o * (1 + h))
        phi_i = np.linspace(phi_i_end, 0, numpoints)
        phi_o = np.linspace(0, phi_o_end, numpoints)
        y_i = r_i * (np.cos(phi_i) - 1)
        y_o = r_o * (1 - np.cos(phi_o))
        x_i = r_i * (np.sin(phi_i) - phi_i) - m * np.pi / 4
        x_o = r_o * (phi_o - np.sin(phi_o)) - m * np.pi / 4
        x = x_i.tolist()[:-1] + x_o.tolist()
        y = y_i.tolist()[:-1] + y_o.tolist()
        points = np.array([y, x]).T
        mirror = reflection(0)
        points_1 = mirror(points)[::-1]
        line_1 = [points[-1], points_1[0]]
        line_2 = [points_1[-1], np.array([-(1 + c) * m , m * np.pi / 2])]
        line_0 = [np.array([-(1 + c) * m , -m * np.pi / 2]), points[0]]
        tooth = points_to_wire([line_0, points, line_1, points_1, line_2])

        edges = tooth.Edges
        edges = insert_fillet(edges, 0, m * root_fillet)
        edges = insert_fillet(edges, 2, m * head_fillet)
        edges = insert_fillet(edges, 4, m * head_fillet)
        edges = insert_fillet(edges, 6, m * root_fillet)

        tooth_edges = [e for e in edges if e is not None]
        p_end = np.array(tooth_edges[-2].lastVertex().Point[:-1])
        p_start = np.array(tooth_edges[1].firstVertex().Point[:-1])
        p_start += np.array([0, np.pi * m])
        edge = points_to_wire([[p_end, p_start]]).Edges
        tooth = Wire(tooth_edges[1:-1] + edge)
        teeth = [tooth]

        for i in range(obj.teeth - 1):
            tooth = copy.deepcopy(tooth)
            tooth.translate(App.Vector(0, np.pi * m, 0))
            teeth.append(tooth)

        teeth[-1] = Wire(teeth[-1].Edges[:-1])

        if obj.add_endings:
            teeth = [Wire(tooth_edges[0])] + teeth
            last_edge = tooth_edges[-1]
            last_edge.translate(App.Vector(0, np.pi * m * (obj.teeth - 1), 0))
            teeth = teeth + [Wire(last_edge)]

        p_start = np.array(teeth[0].Edges[0].firstVertex().Point[:-1])
        p_end = np.array(teeth[-1].Edges[-1].lastVertex().Point[:-1])
        p_start_1 = p_start - np.array([obj.thickness.Value, 0.])
        p_end_1 = p_end - np.array([obj.thickness.Value, 0.])

        line6 = [p_start, p_start_1]
        line7 = [p_start_1, p_end_1]
        line8 = [p_end_1, p_end]

        bottom = points_to_wire([line6, line7, line8])

        pol = Wire([bottom] + teeth)

        if obj.height.Value == 0:
            return pol
        elif obj.beta.Value == 0:
            face = Face(Wire(pol))
            return face.extrude(fcvec([0., 0., obj.height.Value]))
        elif obj.double_helix:
            beta = obj.beta.Value * np.pi / 180.
            pol2 = Part.Wire(pol)
            pol2.translate(
                fcvec([0., np.tan(beta) * obj.height.Value / 2, obj.height.Value / 2]))
            pol3 = Part.Wire(pol)
            pol3.translate(fcvec([0., 0., obj.height.Value]))
            return makeLoft([pol, pol2, pol3], True, True)
        else:
            beta = obj.beta.Value * np.pi / 180.
            pol2 = Part.Wire(pol)
            pol2.translate(
                fcvec([0., np.tan(beta) * obj.height.Value, obj.height.Value]))
            return makeLoft([pol, pol2], True)





    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class CrownGear(BaseGear):
    def __init__(self, obj):
        super(CrownGear, self).__init__(obj)
        obj.addProperty("App::PropertyInteger",
                        "teeth", "base", "number of teeth")
        obj.addProperty("App::PropertyInteger",
                        "other_teeth", "base", "number of teeth of other gear")
        obj.addProperty("App::PropertyLength", "module", "base", "module")
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty("App::PropertyLength", "thickness", "base", "thickness")
        obj.addProperty("App::PropertyAngle", "pressure_angle", "involute", "pressure angle")
        self.add_accuracy_properties(obj)
        obj.teeth = 15
        obj.other_teeth = 15
        obj.module = '1. mm'
        obj.pressure_angle = '20. deg'
        obj.height = '2. mm'
        obj.thickness = '5 mm'
        obj.num_profiles = 4
        obj.preview_mode = True
        self.obj = obj
        obj.Proxy = self

        App.Console.PrintMessage("Gear module: Crown gear created, preview_mode = true for improved performance. "\
                                 "Set preview_mode property to false when ready to cut teeth.")

    def add_accuracy_properties(self, obj):
        obj.addProperty("App::PropertyInteger", "num_profiles", "accuracy", "number of profiles used for loft")
        obj.addProperty("App::PropertyBool", "preview_mode", "accuracy", "if true no boolean operation is done")

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

    def generate_gear_shape(self, fp):
        inner_diameter = fp.module.Value * fp.teeth
        outer_diameter = inner_diameter + fp.height.Value * 2
        inner_circle = Part.Wire(Part.makeCircle(inner_diameter / 2.))
        outer_circle = Part.Wire(Part.makeCircle(outer_diameter / 2.))
        inner_circle.reverse()
        face = Part.Face([outer_circle, inner_circle])
        solid = face.extrude(App.Vector([0., 0., -fp.thickness.Value]))
        if fp.preview_mode:
            return solid

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
        cut_shapes = []
        for _ in range(t):
            loft = loft.transformGeometry(rot)
            cut_shapes.append(loft)
        return solid.cut(cut_shapes)

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass


class CycloidGear(BaseGear):
    """FreeCAD gear"""

    def __init__(self, obj):
        super(CycloidGear, self).__init__(obj)
        self.cycloid_tooth = CycloidTooth()
        obj.addProperty("App::PropertyInteger",
                        "teeth", "base", "number of teeth")
        obj.addProperty(
            "App::PropertyLength", "module", "base", "module")
        obj.addProperty(
            "App::PropertyLength", "height", "base", "height")

        obj.addProperty("App::PropertyInteger", "numpoints", "accuracy", "number of points for spline")
        obj.addProperty("App::PropertyPythonObject", "gear",
                        "base", "the python object")

        self.add_helical_properties(obj)
        self.add_fillet_properties(obj)
        self.add_tolerance_properties(obj)
        self.add_cycloid_properties(obj)
        self.add_computed_properties(obj)
        obj.gear = self.cycloid_tooth
        obj.teeth = 15
        obj.module = '1. mm'
        obj.setExpression('inner_diameter', 'teeth / 2') # teeth/2 makes the hypocycloid a straight line to the center
        obj.outer_diameter = 7.5 # we don't know the mating gear, so we just set the default to mesh with our default
        obj.beta = '0. deg'
        obj.height = '5. mm'
        obj.clearance = 0.25
        obj.numpoints = 15
        obj.backlash = '0.00 mm'
        obj.double_helix = False
        obj.head = 0
        obj.head_fillet = 0
        obj.root_fillet = 0
        obj.Proxy = self

    def add_helical_properties(self, obj):
        obj.addProperty("App::PropertyBool", "double_helix", "helical", "double helix")
        obj.addProperty("App::PropertyAngle", "beta", "helical", "beta")

    def add_fillet_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "head_fillet", "fillets", "a fillet for the tooth-head, radius = head_fillet x module")
        obj.addProperty("App::PropertyFloat", "root_fillet", "fillets", "a fillet for the tooth-root, radius = root_fillet x module")

    def add_tolerance_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "clearance", "tolerance", "clearance")
        obj.addProperty("App::PropertyLength", "backlash", "tolerance",
            "The arc length on the pitch circle by which the tooth thicknes is reduced.")
        obj.addProperty("App::PropertyFloat", "head", "tolerance", "head_value * modul_value = additional length of head")

    def add_cycloid_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "inner_diameter", "cycloid", "inner_diameter divided by module (hypocycloid)")
        obj.addProperty("App::PropertyFloat", "outer_diameter", "cycloid", "outer_diameter divided by module (epicycloid)")

    def add_computed_properties(self, obj):
        obj.addProperty("App::PropertyLength", "dw", "computed", "The pitch diameter.")
        obj.setExpression('dw', 'teeth * module') # calculate via expression to ease usage for placement
        obj.setEditorMode('dw', 1) # set read-only after setting the expression, else it won't be visible. bug?
        obj.addProperty("App::PropertyAngle", "angular_backlash", "computed",
            "The angle by which this gear can turn without moving the mating gear.")
        obj.setExpression('angular_backlash', 'backlash / dw * 360° / pi') # calculate via expression to ease usage for placement
        obj.setEditorMode('angular_backlash', 1) # set read-only after setting the expression, else it won't be visible. bug?

    def generate_gear_shape(self, fp):
        fp.gear.m = fp.module.Value
        fp.gear.z = fp.teeth
        fp.dw = fp.module * fp.teeth
        fp.gear.z1 = fp.inner_diameter
        fp.gear.z2 = fp.outer_diameter
        fp.gear.clearance = fp.clearance
        fp.gear.head = fp.head
        fp.gear.backlash = fp.backlash.Value
        fp.gear._update()

        pts = fp.gear.points(num=fp.numpoints)
        rot = rotation(-fp.gear.phipart)
        rotated_pts = list(map(rot, pts))
        pts.append([pts[-1][-1],rotated_pts[0][0]])
        pts += rotated_pts
        tooth = points_to_wire(pts)
        edges = tooth.Edges

        r_head = float(fp.head_fillet * fp.module)
        r_root = float(fp.root_fillet * fp.module)

        pos_head = [0, 2, 6]
        pos_root = [4, 6]
        edge_range = [1, 9]

        for pos in pos_head:
            edges = insert_fillet(edges, pos, r_head)

        for pos in pos_root:
            edges = insert_fillet(edges, pos, r_root)

        edges = edges[edge_range[0]:edge_range[1]]
        edges = [e for e in edges if e is not None]

        tooth = Wire(edges)

        profile = rotate_tooth(tooth, fp.teeth)
        if fp.height.Value == 0:
            return profile
        base = Face(profile)
        if fp.beta.Value == 0:
            return base.extrude(App.Vector(0, 0, fp.height.Value))
        else:
            twist_angle = fp.height.Value * np.tan(fp.beta.Value * np.pi / 180) * 2 / fp.gear.d
            return helicalextrusion(base, fp.height.Value, twist_angle, fp.double_helix)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


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
        obj.addProperty("App::PropertyAngle", "pressure_angle", "involute_parameter", "pressure_angle")
        obj.addProperty("App::PropertyLength", "module", "base", "module")
        obj.addProperty("App::PropertyFloat", "clearance", "tolerance", "clearance")
        obj.addProperty("App::PropertyInteger", "numpoints", "precision", "number of points for spline")
        obj.addProperty("App::PropertyBool", "reset_origin", "base", "if value is true the gears outer face will match the z=0 plane")
        obj.addProperty("App::PropertyLength", "backlash", "tolerance",
            "The arc length on the pitch circle by which the tooth thicknes is reduced.")
        obj.addProperty("App::PropertyPythonObject", "gear", "base", "test")
        obj.addProperty("App::PropertyAngle", "beta","helical", "angle used for spiral bevel-gears")
        obj.addProperty("App::PropertyLength", "dw", "computed", "The pitch diameter.")
        obj.setExpression('dw', 'teeth * module') # calculate via expression to ease usage for placement
        obj.setEditorMode('dw', 1) # set read-only after setting the expression, else it won't be visible. bug?
        obj.addProperty("App::PropertyAngle", "angular_backlash", "computed",
            "The angle by which this gear can turn without moving the mating gear.")
        obj.setExpression('angular_backlash', 'backlash / dw * 360° / pi') # calculate via expression to ease usage for placement
        obj.setEditorMode('angular_backlash', 1) # set read-only after setting the expression, else it won't be visible. bug?
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

    def generate_gear_shape(self, fp):
        fp.gear.z = fp.teeth
        fp.gear.module = fp.module.Value
        fp.gear.pressure_angle = (90 - fp.pressure_angle.Value) * np.pi / 180.
        fp.gear.pitch_angle = fp.pitch_angle.Value * np.pi / 180
        max_height = fp.gear.module * fp.teeth / 2 / np.tan(fp.gear.pitch_angle)
        if fp.height >= max_height:
            App.Console.PrintWarning("height must be smaller than {}".format(max_height))
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
        if not "version" in fp.PropertiesList:
            scale_0 = scale - fp.height.Value / 2
            scale_1 = scale + fp.height.Value / 2
        else: # starting with version 0.0.2
            scale_0 = scale - fp.height.Value
            scale_1 = scale
        if fp.beta.Value == 0:
            wires.append(make_bspline_wire([scale_0 * p for p in pts]))
            wires.append(make_bspline_wire([scale_1 * p for p in pts]))
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
                wires.append(make_bspline_wire(points))
        shape = makeLoft(wires, True)
        if fp.reset_origin:
            mat = App.Matrix()
            mat.A33 = -1
            mat.move(fcvec([0, 0, scale_1]))
            shape = shape.transformGeometry(mat)
        return shape
        # return self.create_teeth(pts, pos1, fp.teeth)

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


class WormGear(BaseGear):

    """FreeCAD gear rack"""

    def __init__(self, obj):
        super(WormGear, self).__init__(obj)
        obj.addProperty("App::PropertyInteger", "teeth", "base", "number of teeth")
        obj.addProperty( "App::PropertyLength", "module", "base", "module")
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty("App::PropertyLength", 'diameter', "base", "diameter")
        obj.addProperty("App::PropertyAngle", "beta", "computed", "beta ", 1)
        obj.addProperty("App::PropertyAngle", "pressure_angle", "involute", "pressure angle")
        obj.addProperty("App::PropertyBool", "reverse_pitch", "base", "reverse rotation of helix")
        obj.addProperty("App::PropertyFloat", "head", "tolerance", "head * module = additional length of head")
        obj.addProperty("App::PropertyFloat", "clearance", "tolerance", "clearance * module = additional length of root")
        obj.teeth = 3
        obj.module = '1. mm'
        obj.pressure_angle = '20. deg'
        obj.height = '5. mm'
        obj.diameter = '5. mm'
        obj.clearance = 0.25
        obj.head = 0
        obj.reverse_pitch = False

        self.obj = obj
        obj.Proxy = self

    def generate_gear_shape(self, fp):
        m = fp.module.Value
        d = fp.diameter.Value
        t = fp.teeth
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
            return full_wire
        else:
            shape = helicalextrusion(Face(full_wire),
                                     h,
                                     h * np.tan(beta) * 2 / d)
            return shape

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class TimingGear(BaseGear):

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
                    },
            "htd8":  {
                    'pitch': 8.0,  'u': 0.9144,  'h': 3.088,
                    'H': 6.096,  'r0': 2.304,  'r1': 4.112,
                    'rs': 0.6656,  'offset': 1.648
                    } 
            }

    def __init__(self, obj):
        super(TimingGear, self).__init__(obj)
        obj.addProperty("App::PropertyInteger",
                        "teeth", "base", "number of teeth")
        obj.addProperty( "App::PropertyEnumeration", "type", "base", "type of timing-gear")
        obj.addProperty( "App::PropertyLength", "height", "base", "height")
        obj.addProperty( "App::PropertyLength", "pitch", "computed", "pitch off gear", 1)
        obj.addProperty( "App::PropertyLength", "h", "computed", "radial height of teeth", 1)
        obj.addProperty( "App::PropertyLength", "u", "computed", "radial difference between pitch \
            diameter and head of gear", 1)
        obj.addProperty( "App::PropertyLength", "r0", "computed", "radius of first arc", 1)
        obj.addProperty( "App::PropertyLength", "r1", "computed", "radius of second arc", 1)
        obj.addProperty( "App::PropertyLength", "rs", "computed", "radius of third arc", 1)
        obj.addProperty( "App::PropertyLength", "offset", "computed", "x-offset of second arc-midpoint", 1)
        obj.teeth = 15
        obj.type = ['gt2', 'gt3', 'gt5', 'htd8']
        obj.height = '5. mm'

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
            return wi
        else:
            return Part.Face(wi).extrude(App.Vector(0, 0, fp.height))

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass


class LanternGear(BaseGear):
    def __init__(self, obj):
        super(LanternGear, self).__init__(obj)
        obj.addProperty("App::PropertyInteger", "teeth", "gear_parameter", "number of teeth")
        obj.addProperty("App::PropertyLength", "module", "base", "module")
        obj.addProperty("App::PropertyLength", "bolt_radius", "base", "the bolt radius of the rack/chain")
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty("App::PropertyInteger", "num_profiles", "accuracy", "number of profiles used for loft")
        obj.addProperty("App::PropertyFloat", "head", "tolerance", "head * module = additional length of head")

        obj.teeth = 15
        obj.module = '1. mm'
        obj.bolt_radius = '1 mm'
        
        obj.height = '5. mm'
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
            return r_0*(phi_min**2*r_0 - 2*phi_min*r_0*np.sin(phi_min) - \
                   2*phi_min*r_r - 2*r_0*np.cos(phi_min) + 2*r_0 + 2*r_r*np.sin(phi_min))
        try:
            import scipy.optimize
            phi_min = scipy.optimize.root(find_phi_min, (phi_max + r_r / r_0 * 4) / 5).x[0] # , r_r / r_0, phi_max)
        except ImportError:
            App.Console.PrintWarning("scipy not available. Can't compute numerical root. Leads to a wrong bolt-radius")
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
            return wi
        else:
            return Part.Face(wi).extrude(App.Vector(0, 0, fp.height))

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass

class HypoCycloidGear(BaseGear):

    """parameters:
        pressure_angle:  pressureangle,   10-30°
        pitch_angle:  cone angle,      0 < pitch_angle < pi/4
    """

    def __init__(self, obj):
        super(HypoCycloidGear, self).__init__(obj)
        obj.addProperty("App::PropertyFloat","pin_circle_radius",       "gear_parameter","Pin ball circle radius(overrides Tooth Pitch")
        obj.addProperty("App::PropertyFloat","roller_diameter",         "gear_parameter","Roller Diameter")
        obj.addProperty("App::PropertyFloat","eccentricity",            "gear_parameter","Eccentricity")
        obj.addProperty("App::PropertyAngle","pressure_angle_lim",      "gear_parameter","Pressure angle limit")
        obj.addProperty("App::PropertyFloat","pressure_angle_offset",   "gear_parameter","Offset in pressure angle")
        obj.addProperty("App::PropertyInteger","teeth_number",          "gear_parameter","Number of teeth in Cam")
        obj.addProperty("App::PropertyInteger","segment_count",         "gear_parameter","Number of points used for spline interpolation")
        obj.addProperty("App::PropertyLength","hole_radius",            "gear_parameter","Center hole's radius")


        obj.addProperty("App::PropertyBool", "show_pins", "Pins", "Create pins in place")
        obj.addProperty("App::PropertyLength","pin_height", "Pins", "height")
        obj.addProperty("App::PropertyBool", "center_pins", "Pins", "Center pin Z axis to generated disks")

        obj.addProperty("App::PropertyBool", "show_disk0", "Disks", "Show main cam disk")
        obj.addProperty("App::PropertyBool", "show_disk1", "Disks", "Show another reversed cam disk on top")
        obj.addProperty("App::PropertyLength","disk_height", "Disks", "height")

        obj.pin_circle_radius = 66
        obj.roller_diameter = 3
        obj.eccentricity = 1.5
        obj.pressure_angle_lim = '50.0 deg'
        obj.pressure_angle_offset = 0.01
        obj.teeth_number = 42
        obj.segment_count = 42
        obj.hole_radius = '30. mm'

        obj.show_pins  = True
        obj.pin_height = '20. mm'
        obj.center_pins= True

        obj.show_disk0 = True
        obj.show_disk1 = True
        obj.disk_height= '10. mm'

        self.obj = obj
        obj.Proxy = self

    def to_polar(self,x, y):
        return (x**2 + y**2)**0.5, math.atan2(y, x)

    def to_rect(self,r, a):
        return r*math.cos(a), r*math.sin(a)

    def calcyp(self,p,a,e,n):
        return math.atan(math.sin(n*a)/(math.cos(n*a)+(n*p)/(e*(n+1))))

    def calc_x(self,p,d,e,n,a):
        return (n*p)*math.cos(a)+e*math.cos((n+1)*a)-d/2*math.cos(self.calcyp(p,a,e,n)+a)

    def calc_y(self,p,d,e,n,a):
        return (n*p)*math.sin(a)+e*math.sin((n+1)*a)-d/2*math.sin(self.calcyp(p,a,e,n)+a)

    def calc_pressure_angle(self,p,d,n,a):
        ex = 2**0.5
        r3 = p*n
        rg = r3/ex
        pp = rg * (ex**2 + 1 - 2*ex*math.cos(a))**0.5 - d/2
        return math.asin( (r3*math.cos(a)-rg)/(pp+d/2))*180/math.pi

    def calc_pressure_limit(self,p,d,e,n,a):
        ex = 2**0.5
        r3 = p*n
        rg = r3/ex
        q = (r3**2 + rg**2 - 2*r3*rg*math.cos(a))**0.5
        x = rg - e + (q-d/2)*(r3*math.cos(a)-rg)/q
        y = (q-d/2)*r3*math.sin(a)/q
        return (x**2 + y**2)**0.5

    def check_limit(self,x,y,maxrad,minrad,offset):
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
        p = b/n
        s = fp.segment_count
        ang = fp.pressure_angle_lim
        c = fp.pressure_angle_offset

        q = 2*math.pi/float(s)

        # Find the pressure angle limit circles
        minAngle = -1.0
        maxAngle = -1.0
        for i in range(0, 180):
            x = self.calc_pressure_angle(p, d, n, i * math.pi / 180.)
            if ( x < ang) and (minAngle < 0):
                minAngle = float(i)
            if (x < -ang) and (maxAngle < 0):
                maxAngle = float(i-1)

        minRadius = self.calc_pressure_limit(p, d, e, n, minAngle * math.pi / 180.)
        maxRadius = self.calc_pressure_limit(p, d, e, n, maxAngle * math.pi / 180.)
        # unused
        # Wire(Part.makeCircle(minRadius,App.Vector(-e, 0, 0)))
        # Wire(Part.makeCircle(maxRadius,App.Vector(-e, 0, 0)))

        App.Console.PrintMessage("Generating cam disk\r\n")
        #generate the cam profile - note: shifted in -x by eccentricicy amount
        i=0
        x = self.calc_x(p, d, e, n, q*i / float(n))
        y = self.calc_y(p, d, e, n, q*i / n)
        x, y = self.check_limit(x,y,maxRadius,minRadius,c)
        points = [App.Vector(x-e, y, 0)]
        for i in range(0,s):
            x = self.calc_x(p, d, e, n, q*(i+1) / n)
            y = self.calc_y(p, d, e, n, q*(i+1) / n)
            x, y = self.check_limit(x, y, maxRadius, minRadius, c)
            points.append([x-e, y, 0])

        wi = make_bspline_wire([points])
        wires = []
        mat= App.Matrix()
        mat.move(App.Vector(e, 0., 0.))
        mat.rotateZ(2 * np.pi / n)
        mat.move(App.Vector(-e, 0., 0.))
        for _ in range(n):
            wi = wi.transformGeometry(mat)
            wires.append(wi)

        cam = Face(Wire(wires))
        #add a circle in the center of the cam
        if fp.hole_radius.Value:
            centerCircle = Face(Wire(Part.makeCircle(fp.hole_radius.Value, App.Vector(-e, 0, 0))))
            cam = cam.cut(centerCircle)

        to_be_fused = []
        if fp.show_disk0==True:
            if fp.disk_height.Value==0:
                to_be_fused.append(cam)
            else:
                to_be_fused.append(cam.extrude(App.Vector(0, 0, fp.disk_height.Value)))

        #secondary cam disk
        if fp.show_disk1==True:
            App.Console.PrintMessage("Generating secondary cam disk\r\n")
            second_cam = cam.copy()
            mat= App.Matrix()
            mat.rotateZ(np.pi)
            mat.move(App.Vector(-e, 0, 0))
            if n%2 == 0:
                mat.rotateZ(np.pi/n)
            mat.move(App.Vector(e, 0, 0))
            second_cam = second_cam.transformGeometry(mat)
            if fp.disk_height.Value==0:
                to_be_fused.append(second_cam)
            else:
                to_be_fused.append(second_cam.extrude(App.Vector(0, 0, -fp.disk_height.Value)))

        #pins
        if fp.show_pins==True:
            App.Console.PrintMessage("Generating pins\r\n")
            pins = []
            for i in range(0, n + 1):
                x = p * n * math.cos(2 * math.pi / (n + 1) * i)
                y = p * n * math.sin(2 * math.pi / (n + 1) * i)
                pins.append(Wire(Part.makeCircle(d / 2, App.Vector(x, y, 0))))

            pins = Face(pins)

            z_offset = -fp.pin_height.Value / 2;

            if fp.center_pins==True:
                if fp.show_disk0==True and fp.show_disk1==False:
                    z_offset += fp.disk_height.Value / 2;
                elif fp.show_disk0==False and fp.show_disk1==True:
                    z_offset += -fp.disk_height.Value / 2;
            #extrude
            if z_offset!=0:
                pins.translate(App.Vector(0, 0, z_offset))
            if fp.pin_height!=0:
                pins = pins.extrude(App.Vector(0, 0, fp.pin_height.Value))

            to_be_fused.append(pins);

        if to_be_fused:
            return Part.makeCompound(to_be_fused)

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass

def part_arc_from_points_and_center(p_1, p_2, m):
    p_1, p_12, p_2 = arc_from_points_and_center(p_1, p_2, m)
    return Part.Arc(App.Vector(*p_1, 0.), App.Vector(*p_12, 0.), App.Vector(*p_2, 0.))


def helicalextrusion(face, height, angle, double_helix=False):
    """
    A helical extrusion using the BRepOffsetAPI
    face -- the face to extrude (may contain holes, i.e. more then one wires)
    height -- the height of the extrusion, normal to the face
    angle -- the twist angle of the extrusion in radians

    returns a solid
    """
    pitch = height * 2 * np.pi / abs(angle)
    radius = 10.0 # as we are only interested in the "twist", we take an arbitrary constant here
    cone_angle = 0
    direction = bool(angle < 0)
    if double_helix:
        spine = Part.makeHelix(pitch, height / 2.0, radius, cone_angle, direction)
        spine.translate(App.Vector(0, 0, height / 2.0))
        face = face.translated(App.Vector(0, 0, height / 2.0)) # don't transform our argument
    else:
        spine = Part.makeHelix(pitch, height, radius, cone_angle, direction)
    def make_pipe(path, profile):
        """
        returns (shell, last_wire)
        """
        mkPS = Part.BRepOffsetAPI.MakePipeShell(path)
        mkPS.setFrenetMode(True) # otherwise, the profile's normal would follow the path
        mkPS.add(profile, False, False)
        mkPS.build()
        return (mkPS.shape(), mkPS.lastShape())
    shell_faces = []
    top_wires = []
    for wire in face.Wires:
        pipe_shell, top_wire = make_pipe(spine, wire)
        shell_faces.extend(pipe_shell.Faces)
        top_wires.append(top_wire)
    top_face = Part.Face(top_wires)
    shell_faces.append(top_face)
    if double_helix:
        origin = App.Vector(0, 0, height / 2.0)
        xy_normal = App.Vector(0, 0, 1)
        mirror_xy = lambda f: f.mirror(origin, xy_normal)
        bottom_faces = list(map(mirror_xy, shell_faces))
        shell_faces.extend(bottom_faces)
        # TODO: why the heck is makeShell from this empty after mirroring?
        # ... and why the heck does it work when making an intermediate compound???
        hacky_intermediate_compound = Part.makeCompound(shell_faces)
        shell_faces = hacky_intermediate_compound.Faces
    else:
        shell_faces.append(face) # the bottom is what we extruded
    shell = Part.makeShell(shell_faces)
    #shell.sewShape() # fill gaps that may result from accumulated tolerances. Needed?
    #shell = shell.removeSplitter() # refine. Needed?
    return Part.makeSolid(shell)

def make_face(edge1, edge2):
    v1, v2 = edge1.Vertexes
    v3, v4 = edge2.Vertexes
    e1 = Wire(edge1)
    e2 = LineSegment(v1.Point, v3.Point).toShape().Edges[0]
    e3 = edge2
    e4 = LineSegment(v4.Point, v2.Point).toShape().Edges[0]
    w = Wire([e3, e4, e1, e2])
    return(Face(w))


def make_bspline_wire(pts):
    wi = []
    for i in pts:
        out = BSplineCurve()
        out.interpolate(list(map(fcvec, i)))
        wi.append(out.toShape())
    return Wire(wi)


def points_to_wire(pts):
    wire = []
    for i in pts:
        if len(i) == 2:
            # straight edge
            out = LineSegment(*list(map(fcvec, i)))
        else:
            out = BSplineCurve()
            out.interpolate(list(map(fcvec, i)))
        wire.append(out.toShape())  
    return Wire(wire)

def rotate_tooth(base_tooth, num_teeth):
    rot = App.Matrix()
    rot.rotateZ(2 * np.pi / num_teeth)
    flat_shape = [base_tooth]
    for t in range(num_teeth - 1):
        flat_shape.append(flat_shape[-1].transformGeometry(rot))
    return Wire(flat_shape)




def fillet_between_edges(edge_1, edge_2, radius):
    # assuming edges are in a plane
    # extracting vertices
    try:
        from Part import ChFi2d
    except ImportError:
        App.Console.PrintWarning("Your freecad version has no python bindings for 2d-fillets")
        return [edge_1, edge_2]

    api = ChFi2d.FilletAPI()
    p1 = edge_1.valueAt(edge_1.FirstParameter)
    p2 = edge_1.valueAt(edge_1.LastParameter)
    p3 = edge_2.valueAt(edge_2.FirstParameter)
    p4 = edge_2.valueAt(edge_2.LastParameter)
    t1 = p2 - p1
    t2 = p4 - p3
    n = t1.cross(t2)
    pln = Part.Plane(edge_1.valueAt(edge_1.FirstParameter), n)
    api.init(edge_1, edge_2, pln)
    if api.perform(radius) > 0:
        p0 = (p2 + p3) / 2
        fillet, e1, e2 = api.result(p0)
        return Part.Wire([e1, fillet, e2]).Edges
    else:
        return None


def insert_fillet(edges, pos, radius):
    assert pos < (len(edges) - 1)
    e1 = edges[pos]
    e2 = edges[pos + 1]
    if radius > 0:
        fillet_edges = fillet_between_edges(e1, e2, radius)
        if not fillet_edges:
            raise RuntimeError("fillet not possible")
    else:
        fillet_edges = [e1, None, e2]
    output_edges = []
    for i, edge in enumerate(edges):
        if i == pos:
            output_edges += fillet_edges
        elif i == (pos + 1):
            pass
        else:
            output_edges.append(edge)
    return output_edges
