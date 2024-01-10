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

from pygears.involute_tooth import InvoluteTooth
from pygears._functions import rotation

from .basegear import (
    BaseGear,
    points_to_wire,
    insert_fillet,
    helical_extrusion,
    rotate_tooth,
)


class InvoluteGear(BaseGear):

    """FreeCAD gear"""

    def __init__(self, obj):
        super(InvoluteGear, self).__init__(obj)
        self.involute_tooth = InvoluteTooth()

        obj.addProperty(
            "App::PropertyPythonObject", "gear", "base", "python gear object"
        )

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
        obj.module = "1. mm"
        obj.shift = 0.0
        obj.pressure_angle = "20. deg"
        obj.beta = "0. deg"
        obj.height = "5. mm"
        obj.clearance = 0.25
        obj.head = 0.0
        obj.numpoints = 20
        obj.double_helix = False
        obj.backlash = "0.00 mm"
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
            "App::PropertyLength",
            "module",
            "base",
            "normal module if properties_from_tool=True, \
                                                                else it's the transverse module.",
        )
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty(
            "App::PropertyAngle", "pressure_angle", "involute", "pressure angle"
        )
        obj.addProperty("App::PropertyFloat", "shift", "involute", "shift")

    def add_fillet_properties(self, obj):
        obj.addProperty("App::PropertyBool", "undercut", "fillets", "undercut")
        obj.addProperty(
            "App::PropertyFloat",
            "head_fillet",
            "fillets",
            "a fillet for the tooth-head, radius = head_fillet x module",
        )
        obj.addProperty(
            "App::PropertyFloat",
            "root_fillet",
            "fillets",
            "a fillet for the tooth-root, radius = root_fillet x module",
        )

    def add_helical_properties(self, obj):
        obj.addProperty(
            "App::PropertyBool",
            "properties_from_tool",
            "helical",
            "if beta is given and properties_from_tool is enabled, \
                         gear parameters are internally recomputed for the rotated gear",
        )
        obj.addProperty("App::PropertyAngle", "beta", "helical", "beta ")
        obj.addProperty("App::PropertyBool", "double_helix", "helical", "double helix")

    def add_computed_properties(self, obj):
        obj.addProperty("App::PropertyLength", "da", "computed", "outside diameter", 1)
        obj.addProperty("App::PropertyLength", "df", "computed", "root diameter", 1)
        self.add_traverse_module_property(obj)
        obj.addProperty(
            "App::PropertyLength", "dw", "computed", "The pitch diameter.", 1
        )
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
        obj.addProperty(
            "App::PropertyLength", "transverse_pitch", "computed", "transverse_pitch", 1
        )

    def add_tolerance_properties(self, obj):
        obj.addProperty(
            "App::PropertyLength",
            "backlash",
            "tolerance",
            "The arc length on the pitch circle by which the tooth thicknes is reduced.",
        )
        obj.addProperty(
            "App::PropertyBool", "reversed_backlash", "tolerance", "backlash direction"
        )
        obj.addProperty("App::PropertyFloat", "clearance", "tolerance", "clearance")
        obj.addProperty(
            "App::PropertyFloat",
            "head",
            "tolerance",
            "head_value * modul_value = additional length of head",
        )

    def add_accuracy_properties(self, obj):
        obj.addProperty("App::PropertyBool", "simple", "accuracy", "simple")
        obj.addProperty(
            "App::PropertyInteger",
            "numpoints",
            "accuracy",
            "number of points for spline",
        )

    def add_traverse_module_property(self, obj):
        obj.addProperty(
            "App::PropertyLength",
            "traverse_module",
            "computed",
            "traverse module of the generated gear",
            1,
        )

    def compute_traverse_properties(self, obj):
        # traverse_module added recently, if old freecad doc is loaded without it, it will not exist when generate_gear_shape() is called
        if not hasattr(obj, "traverse_module"):
            self.add_traverse_module_property(obj)
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
        obj.gear.pressure_angle = obj.pressure_angle.Value * np.pi / 180.0
        obj.gear.beta = obj.beta.Value * np.pi / 180
        obj.gear.clearance = obj.clearance
        obj.gear.backlash = obj.backlash.Value * (-obj.reversed_backlash + 0.5) * 2.0
        obj.gear.head = obj.head
        obj.gear.properties_from_tool = obj.properties_from_tool

        obj.gear._update()
        self.compute_traverse_properties(obj)

        if not obj.simple:
            pts = obj.gear.points(num=obj.numpoints)
            rot = rotation(obj.gear.phipart)
            rotated_pts = list(map(rot, pts))
            pts.append([pts[-1][-1], rotated_pts[0][0]])
            pts += rotated_pts
            tooth = points_to_wire(pts)
            edges = tooth.Edges

            # head-fillet:
            r_head = float(obj.head_fillet * obj.module)
            r_root = float(obj.root_fillet * obj.module)
            if obj.undercut and r_root != 0.0:
                r_root = 0.0
                app.Console.PrintWarning(
                    "root fillet is not allowed if undercut is computed"
                )
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
            edges = edges[edge_range[0] : edge_range[1]]
            edges = [e for e in edges if e is not None]

            tooth = part.Wire(edges)
            profile = rotate_tooth(tooth, obj.teeth)

            if obj.height.Value == 0:
                return profile
            base = part.Face(profile)
            if obj.beta.Value == 0:
                return base.extrude(app.Vector(0, 0, obj.height.Value))
            else:
                twist_angle = obj.height.Value * np.tan(obj.gear.beta) * 2 / obj.gear.d
                return helical_extrusion(
                    base, obj.height.Value, twist_angle, obj.double_helix
                )
        else:
            rw = obj.gear.dw / 2
            return part.makeCylinder(rw, obj.height.Value)
