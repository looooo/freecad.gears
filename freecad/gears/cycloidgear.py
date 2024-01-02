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
import Part

import numpy as np
from pygears.cycloid_tooth import CycloidTooth
from pygears._functions import rotation

from .basegear import (
    BaseGear,
    points_to_wire,
    insert_fillet,
    helicalextrusion,
    rotate_tooth,
)


class CycloidGear(BaseGear):
    """FreeCAD gear"""

    def __init__(self, obj):
        super(CycloidGear, self).__init__(obj)
        self.cycloid_tooth = CycloidTooth()
        obj.addProperty("App::PropertyInteger", "teeth", "base", "number of teeth")
        obj.addProperty("App::PropertyLength", "module", "base", "module")
        obj.addProperty("App::PropertyLength", "height", "base", "height")

        obj.addProperty(
            "App::PropertyInteger",
            "numpoints",
            "accuracy",
            "number of points for spline",
        )
        obj.addProperty(
            "App::PropertyPythonObject", "gear", "base", "the python object"
        )

        self.add_helical_properties(obj)
        self.add_fillet_properties(obj)
        self.add_tolerance_properties(obj)
        self.add_cycloid_properties(obj)
        self.add_computed_properties(obj)
        obj.gear = self.cycloid_tooth
        obj.teeth = 15
        obj.module = "1. mm"
        obj.setExpression(
            "inner_diameter", "teeth / 2"
        )  # teeth/2 makes the hypocycloid a straight line to the center
        obj.outer_diameter = 7.5  # we don't know the mating gear, so we just set the default to mesh with our default
        obj.beta = "0. deg"
        obj.height = "5. mm"
        obj.clearance = 0.25
        obj.numpoints = 15
        obj.backlash = "0.00 mm"
        obj.double_helix = False
        obj.head = 0
        obj.head_fillet = 0
        obj.root_fillet = 0
        obj.Proxy = self

    def add_helical_properties(self, obj):
        obj.addProperty("App::PropertyBool", "double_helix", "helical", "double helix")
        obj.addProperty("App::PropertyAngle", "beta", "helical", "beta")

    def add_fillet_properties(self, obj):
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

    def add_tolerance_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "clearance", "tolerance", "clearance")
        obj.addProperty(
            "App::PropertyLength",
            "backlash",
            "tolerance",
            "The arc length on the pitch circle by which the tooth thicknes is reduced.",
        )
        obj.addProperty(
            "App::PropertyFloat",
            "head",
            "tolerance",
            "head_value * modul_value = additional length of head",
        )

    def add_cycloid_properties(self, obj):
        obj.addProperty(
            "App::PropertyFloat",
            "inner_diameter",
            "cycloid",
            "inner_diameter divided by module (hypocycloid)",
        )
        obj.addProperty(
            "App::PropertyFloat",
            "outer_diameter",
            "cycloid",
            "outer_diameter divided by module (epicycloid)",
        )

    def add_computed_properties(self, obj):
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
        pts.append([pts[-1][-1], rotated_pts[0][0]])
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

        edges = edges[edge_range[0] : edge_range[1]]
        edges = [e for e in edges if e is not None]

        tooth = Part.Wire(edges)

        profile = rotate_tooth(tooth, fp.teeth)
        if fp.height.Value == 0:
            return profile
        base = Part.Face(profile)
        if fp.beta.Value == 0:
            return base.extrude(app.Vector(0, 0, fp.height.Value))
        else:
            twist_angle = (
                fp.height.Value * np.tan(fp.beta.Value * np.pi / 180) * 2 / fp.gear.d
            )
            return helicalextrusion(base, fp.height.Value, twist_angle, fp.double_helix)
