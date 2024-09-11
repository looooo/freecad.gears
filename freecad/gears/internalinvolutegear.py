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

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP


from .basegear import (
    BaseGear,
    points_to_wire,
    insert_fillet,
    helical_extrusion,
    rotate_tooth,
)


class InternalInvoluteGear(BaseGear):
    """FreeCAD internal involute gear

    Using the same tooth as the external, just turning it inside-out:
    addedum becomes dedendum, clearance becomes head, negate the backslash, ...
    """

    def __init__(self, obj):
        super(InternalInvoluteGear, self).__init__(obj)
        self.involute_tooth = InvoluteTooth()
        obj.addProperty(
            "App::PropertyBool",
            "simple",
            "precision",
            QT_TRANSLATE_NOOP("App::Property", "simple"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "num_teeth",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "number of teeth"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "module",
            "base",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "normal module if properties_from_tool=True, else it's the transverse module.",
            ),
        )
        obj.addProperty(
            "App::PropertyLength",
            "height",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "height"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "thickness",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "thickness"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "numpoints",
            "accuracy",
            QT_TRANSLATE_NOOP("App::Property", "number of points for spline"),
        )
        obj.addProperty(
            "App::PropertyPythonObject",
            "gear",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "test"),
        )

        self.add_involute_properties(obj)
        self.add_tolerance_properties(obj)
        self.add_fillet_properties(obj)
        self.add_computed_properties(obj)
        self.add_limiting_diameter_properties(obj)
        self.add_helical_properties(obj)

        obj.gear = self.involute_tooth
        obj.simple = False
        obj.num_teeth = 15
        obj.module = "1. mm"
        obj.shift = 0.0
        obj.pressure_angle = "20. deg"
        obj.beta = "0. deg"
        obj.height = "5. mm"
        obj.thickness = "5 mm"
        obj.clearance = 0.25
        obj.head = -0.4  # using head=0 and shift=0.5 may be better, but makes placeing the pinion less intuitive
        obj.numpoints = 20
        obj.double_helix = False
        obj.backlash = "0.00 mm"
        obj.reversed_backlash = False
        obj.properties_from_tool = False
        obj.head_fillet = 0
        obj.root_fillet = 0
        self.obj = obj
        obj.Proxy = self

    def add_limiting_diameter_properties(self, obj):
        obj.addProperty(
            "App::PropertyLength",
            "da",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "inside diameter"),
            1,
        )
        obj.addProperty(
            "App::PropertyLength",
            "df",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "root diameter"),
            1,
        )

    def add_computed_properties(self, obj):
        obj.addProperty(
            "App::PropertyLength",
            "dw",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "The pitch diameter."),
        )
        obj.addProperty(
            "App::PropertyAngle",
            "angular_backlash",
            "computed",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "The angle by which this gear can turn without moving the mating gear.",
            ),
        )
        obj.setExpression(
            "angular_backlash", "backlash / dw * 360° / pi"
        )  # calculate via expression to ease usage for placement
        obj.setEditorMode(
            "angular_backlash", 1
        )  # set read-only after setting the expression, else it won't be visible. bug?
        obj.addProperty(
            "App::PropertyLength",
            "transverse_pitch",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "transverse_pitch"),
            1,
        )
        obj.addProperty(
            "App::PropertyLength",
            "outside_diameter",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "Outside diameter"),
            1,
        )

    def add_fillet_properties(self, obj):
        obj.addProperty(
            "App::PropertyFloat",
            "head_fillet",
            "fillets",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "a fillet for the tooth-head, radius = head_fillet x module",
            ),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "root_fillet",
            "fillets",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "a fillet for the tooth-root, radius = root_fillet x module",
            ),
        )

    def add_tolerance_properties(self, obj):
        obj.addProperty(
            "App::PropertyLength",
            "backlash",
            "tolerance",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "The arc length on the pitch circle by which the tooth thicknes is reduced.",
            ),
        )
        obj.addProperty(
            "App::PropertyBool",
            "reversed_backlash",
            "tolerance",
            QT_TRANSLATE_NOOP("App::Property", "backlash direction"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "head",
            "tolerance",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "head_value * module_value = additional length of head",
            ),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "clearance",
            "tolerance",
            QT_TRANSLATE_NOOP("App::Property", "clearance"),
        )

    def add_involute_properties(self, obj):
        obj.addProperty(
            "App::PropertyFloat",
            "shift",
            "involute",
            QT_TRANSLATE_NOOP("App::Property", "shift"),
        )
        obj.addProperty(
            "App::PropertyAngle",
            "pressure_angle",
            "involute",
            QT_TRANSLATE_NOOP("App::Property", "pressure angle"),
        )

    def add_helical_properties(self, obj):
        obj.addProperty(
            "App::PropertyAngle",
            "beta",
            "helical",
            QT_TRANSLATE_NOOP("App::Property", "beta"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "double_helix",
            "helical",
            QT_TRANSLATE_NOOP("App::Property", "double helix"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "properties_from_tool",
            "helical",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "if beta is given and properties_from_tool is enabled, gear parameters are internally recomputed for the rotated gear",
            ),
        )

    def generate_gear_shape(self, fp):
        fp.gear.double_helix = fp.double_helix
        fp.gear.m_n = fp.module.Value
        fp.gear.undercut = False  # no undercut for internal gears
        fp.gear.shift = fp.shift
        fp.gear.pressure_angle = fp.pressure_angle.Value * np.pi / 180.0
        fp.gear.beta = fp.beta.Value * np.pi / 180
        fp.gear.clearance = fp.head  # swap head and clearance to become "internal"
        fp.gear.backlash = (
            fp.backlash.Value * (fp.reversed_backlash - 0.5) * 2.0
        )  # negate "reversed_backslash", for "internal"
        fp.gear.head = fp.clearance  # swap head and clearance to become "internal"
        fp.gear.properties_from_tool = fp.properties_from_tool
        fp.gear._update()

        fp.dw = "{}mm".format(fp.gear.dw)

        # computed properties
        fp.transverse_pitch = "{}mm".format(fp.gear.pitch)
        fp.outside_diameter = fp.dw + 2 * fp.thickness
        # checksbackwardcompatibility:
        if not "da" in fp.PropertiesList:
            self.add_limiting_diameter_properties(fp)
        fp.da = "{}mm".format(fp.gear.df)  # swap addednum and dedendum for "internal"
        fp.df = "{}mm".format(fp.gear.da)  # swap addednum and dedendum for "internal"

        outer_circle = part.Wire(part.makeCircle(fp.outside_diameter / 2.0))
        outer_circle.reverse()
        if not fp.simple:
            # head-fillet:
            pts = fp.gear.points(num=fp.numpoints)
            rot = rotation(fp.gear.phipart)
            rotated_pts = list(map(rot, pts))
            pts.append([pts[-1][-1], rotated_pts[0][0]])
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
            edges = edges[edge_range[0] : edge_range[1]]
            edges = [e for e in edges if e is not None]

            tooth = part.Wire(edges)
            profile = rotate_tooth(tooth, fp.num_teeth)
            if fp.height.Value == 0:
                return part.makeCompound([outer_circle, profile])
            base = part.Face([outer_circle, profile])
            if fp.beta.Value == 0:
                return base.extrude(app.Vector(0, 0, fp.height.Value))
            else:
                twist_angle = fp.height.Value * np.tan(fp.gear.beta) * 2 / fp.gear.d
                return helical_extrusion(
                    base, fp.height.Value, twist_angle, fp.double_helix
                )
        else:
            inner_circle = part.Wire(part.makeCircle(fp.dw / 2.0))
            inner_circle.reverse()
            base = part.Face([outer_circle, inner_circle])
            return base.extrude(app.Vector(0, 0, fp.height.Value))
