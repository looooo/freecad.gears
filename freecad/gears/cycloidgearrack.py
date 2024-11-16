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

import os
import sys

from freecad import app
from freecad import part

import numpy as np

from pygears._functions import reflection
from .basegear import BaseGear, fcvec, points_to_wire, insert_fillet

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP


class CycloidGearRack(BaseGear):
    """FreeCAD gear rack"""

    def __init__(self, obj):
        super(CycloidGearRack, self).__init__(obj)
        obj.addProperty(
            "App::PropertyIntegerConstraint",
            "num_teeth",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "number of teeth"),
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
        obj.addProperty("App::PropertyLength", "module", "involute", "module")
        obj.addProperty(
            "App::PropertyBool",
            "simplified",
            "precision",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "if enabled the rack is drawn with a constant number of teeth to avoid topologic renaming.",
            ),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "numpoints",
            "accuracy",
            QT_TRANSLATE_NOOP("App::Property", "number of points for spline"),
        )
        obj.addProperty(
            "App::PropertyPythonObject",
            "rack",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "test"),
        )

        self.add_helical_properties(obj)
        self.add_computed_properties(obj)
        self.add_tolerance_properties(obj)
        self.add_cycloid_properties(obj)
        self.add_fillet_properties(obj)
        obj.num_teeth = (15, 3, 10000, 1)  # default, min, max, step
        obj.module = "1. mm"
        obj.inner_diameter = 7.5
        obj.outer_diameter = 7.5
        obj.height = "5. mm"
        obj.thickness = "5 mm"
        obj.beta = "0. deg"
        obj.clearance = 0.25
        obj.head = 0.0
        obj.add_endings = True
        obj.simplified = False
        obj.numpoints = 15
        self.obj = obj
        obj.Proxy = self

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

    def add_computed_properties(self, obj):
        obj.addProperty(
            "App::PropertyLength",
            "transverse_pitch",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "pitch in the transverse plane"),
            1,
        )
        obj.addProperty(
            "App::PropertyBool",
            "add_endings",
            "base",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "if enabled the total length of the rack is teeth x pitch, otherwise the rack starts with a tooth-flank",
            ),
        )

    def add_tolerance_properties(self, obj):
        obj.addProperty(
            "App::PropertyFloat",
            "head",
            "tolerance",
            QT_TRANSLATE_NOOP(
                "App::Property", "head * module = additional length of head"
            ),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "clearance",
            "tolerance",
            QT_TRANSLATE_NOOP(
                "App::Property", "clearance * module = additional length of root"
            ),
        )

    def add_cycloid_properties(self, obj):
        obj.addProperty(
            "App::PropertyFloat",
            "inner_diameter",
            "cycloid",
            QT_TRANSLATE_NOOP(
                "App::Property", "inner_diameter divided by module (hypocycloid)"
            ),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "outer_diameter",
            "cycloid",
            QT_TRANSLATE_NOOP(
                "App::Property", "outer_diameter divided by module (epicycloid)"
            ),
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
        line_2 = [points_1[-1], np.array([-(1 + c) * m, m * np.pi / 2])]
        line_0 = [np.array([-(1 + c) * m, -m * np.pi / 2]), points[0]]
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
        tooth = part.Wire(tooth_edges[1:-1] + edge)
        teeth = [tooth]

        for i in range(obj.num_teeth - 1):
            tooth = tooth.copy()
            tooth.translate(app.Vector(0, np.pi * m, 0))
            teeth.append(tooth)

        teeth[-1] = part.Wire(teeth[-1].Edges[:-1])

        if obj.add_endings:
            teeth = [part.Wire(tooth_edges[0])] + teeth
            last_edge = tooth_edges[-1]
            last_edge.translate(app.Vector(0, np.pi * m * (obj.num_teeth - 1), 0))
            teeth = teeth + [part.Wire(last_edge)]

        p_start = np.array(teeth[0].Edges[0].firstVertex().Point[:-1])
        p_end = np.array(teeth[-1].Edges[-1].lastVertex().Point[:-1])
        p_start_1 = p_start - np.array([obj.thickness.Value, 0.0])
        p_end_1 = p_end - np.array([obj.thickness.Value, 0.0])

        line6 = [p_start, p_start_1]
        line7 = [p_start_1, p_end_1]
        line8 = [p_end_1, p_end]

        bottom = points_to_wire([line6, line7, line8])

        pol = part.Wire([bottom] + teeth)

        if obj.height.Value == 0:
            return pol
        elif obj.beta.Value == 0:
            face = part.Face(part.Wire(pol))
            return face.extrude(fcvec([0.0, 0.0, obj.height.Value]))
        elif obj.double_helix:
            beta = obj.beta.Value * np.pi / 180.0
            pol2 = part.Wire(pol)
            pol2.translate(
                fcvec([0.0, np.tan(beta) * obj.height.Value / 2, obj.height.Value / 2])
            )
            pol3 = part.Wire(pol)
            pol3.translate(fcvec([0.0, 0.0, obj.height.Value]))
            return part.makeLoft([pol, pol2, pol3], True, True)
        else:
            beta = obj.beta.Value * np.pi / 180.0
            pol2 = part.Wire(pol)
            pol2.translate(
                fcvec([0.0, np.tan(beta) * obj.height.Value, obj.height.Value])
            )
            return part.makeLoft([pol, pol2], True)
