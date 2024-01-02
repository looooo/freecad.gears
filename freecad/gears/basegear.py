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
import math

from pygears import __version__
from pygears._functions import arc_from_points_and_center


def fcvec(x):
    if len(x) == 2:
        return app.Vector(x[0], x[1], 0)
    else:
        return app.Vector(x[0], x[1], x[2])


class ViewProviderGear(object):
    def __init__(self, obj, icon_fn=None):
        # Set this object to the proxy object of the actual view provider
        obj.Proxy = self
        self._check_attr()
        dirname = os.path.dirname(__file__)
        self.icon_fn = icon_fn or os.path.join(dirname, "icons", "involutegear.svg")

    def _check_attr(self):
        """Check for missing attributes."""
        if not hasattr(self, "icon_fn"):
            setattr(
                self,
                "icon_fn",
                os.path.join(os.path.dirname(__file__), "icons", "involutegear.svg"),
            )

    def attach(self, vobj):
        self.vobj = vobj

    def getIcon(self):
        self._check_attr()
        return self.icon_fn

    if sys.version_info[0] == 3 and sys.version_info[1] >= 11:

        def dumps(self):
            self._check_attr()
            return {"icon_fn": self.icon_fn}

        def loads(self, state):
            if state and "icon_fn" in state:
                self.icon_fn = state["icon_fn"]
    else:

        def __getstate__(self):
            self._check_attr()
            return {"icon_fn": self.icon_fn}

        def __setstate__(self, state):
            if state and "icon_fn" in state:
                self.icon_fn = state["icon_fn"]


class BaseGear(object):
    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyString", "version", "version", "freecad.gears-version", 1
        )
        obj.version = __version__
        self.make_attachable(obj)

    def make_attachable(self, obj):
        # Needed to make this object "attachable",
        # aka able to attach parameterically to other objects
        # cf. https://wiki.freecadweb.org/Scripted_objects_with_attachment
        if int(app.Version()[1]) >= 19:
            obj.addExtension("Part::AttachExtensionPython")
        else:
            obj.addExtension("Part::AttachExtensionPython", obj)
        # unveil the "Placement" property, which seems hidden by default in PartDesign
        obj.setEditorMode("Placement", 0)  # non-readonly non-hidden

    def execute(self, fp):
        # checksbackwardcompatibility:
        if not hasattr(fp, "positionBySupport"):
            self.make_attachable(fp)
        fp.positionBySupport()
        gear_shape = self.generate_gear_shape(fp)
        if hasattr(fp, "BaseFeature") and fp.BaseFeature != None:
            # we're inside a PartDesign Body, thus need to fuse with the base feature
            gear_shape.Placement = (
                fp.Placement
            )  # ensure the gear is placed correctly before fusing
            result_shape = fp.BaseFeature.Shape.fuse(gear_shape)
            result_shape.transformShape(
                fp.Placement.inverse().toMatrix(), True
            )  # account for setting fp.Shape below moves the shape to fp.Placement, ignoring its previous placement
            fp.Shape = result_shape
        else:
            fp.Shape = gear_shape

    def generate_gear_shape(self, fp):
        """
        This method has to return the TopoShape of the gear.
        """
        raise NotImplementedError("generate_gear_shape not implemented")

    if sys.version_info[0] == 3 and sys.version_info[1] >= 11:

        def loads(self, state):
            pass

        def dumps(self):
            pass
    else:

        def __setstate__(self, state):
            pass

        def __getstate__(self):
            pass


def part_arc_from_points_and_center(p_1, p_2, m):
    p_1, p_12, p_2 = arc_from_points_and_center(p_1, p_2, m)
    return part.Arc(
        app.Vector(*p_1, 0.0), app.Vector(*p_12, 0.0), app.Vector(*p_2, 0.0)
    )


def helicalextrusion(face, height, angle, double_helix=False):
    """
    A helical extrusion using the BRepOffsetAPI
    face -- the face to extrude (may contain holes, i.e. more then one wires)
    height -- the height of the extrusion, normal to the face
    angle -- the twist angle of the extrusion in radians

    returns a solid
    """
    pitch = height * 2 * np.pi / abs(angle)
    radius = 10.0  # as we are only interested in the "twist", we take an arbitrary constant here
    cone_angle = 0
    direction = bool(angle < 0)
    if double_helix:
        spine = part.makeHelix(pitch, height / 2.0, radius, cone_angle, direction)
        spine.translate(app.Vector(0, 0, height / 2.0))
        face = face.translated(
            app.Vector(0, 0, height / 2.0)
        )  # don't transform our argument
    else:
        spine = part.makeHelix(pitch, height, radius, cone_angle, direction)

    def make_pipe(path, profile):
        """
        returns (shell, last_wire)
        """
        mkPS = part.BRepOffsetAPI.MakePipeShell(path)
        mkPS.setFrenetMode(
            True
        )  # otherwise, the profile's normal would follow the path
        mkPS.add(profile, False, False)
        mkPS.build()
        return (mkPS.shape(), mkPS.lastShape())

    shell_faces = []
    top_wires = []
    for wire in face.Wires:
        pipe_shell, top_wire = make_pipe(spine, wire)
        shell_faces.extend(pipe_shell.Faces)
        top_wires.append(top_wire)
    top_face = part.Face(top_wires)
    shell_faces.append(top_face)
    if double_helix:
        origin = app.Vector(0, 0, height / 2.0)
        xy_normal = app.Vector(0, 0, 1)
        mirror_xy = lambda f: f.mirror(origin, xy_normal)
        bottom_faces = list(map(mirror_xy, shell_faces))
        shell_faces.extend(bottom_faces)
        # TODO: why the heck is makeShell from this empty after mirroring?
        # ... and why the heck does it work when making an intermediate compound???
        hacky_intermediate_compound = part.makeCompound(shell_faces)
        shell_faces = hacky_intermediate_compound.Faces
    else:
        shell_faces.append(face)  # the bottom is what we extruded
    shell = part.makeShell(shell_faces)
    # shell.sewShape() # fill gaps that may result from accumulated tolerances. Needed?
    # shell = shell.removeSplitter() # refine. Needed?
    return part.makeSolid(shell)


def make_face(edge1, edge2):
    v1, v2 = edge1.Vertexes
    v3, v4 = edge2.Vertexes
    e1 = part.Wire(edge1)
    e2 = part.LineSegment(v1.Point, v3.Point).toShape().Edges[0]
    e3 = edge2
    e4 = part.LineSegment(v4.Point, v2.Point).toShape().Edges[0]
    w = part.Wire([e3, e4, e1, e2])
    return part.Face(w)


def make_bspline_wire(pts):
    wi = []
    for i in pts:
        out = part.BSplineCurve()
        out.interpolate(list(map(fcvec, i)))
        wi.append(out.toShape())
    return part.Wire(wi)


def points_to_wire(pts):
    wire = []
    for i in pts:
        if len(i) == 2:
            # straight edge
            out = part.LineSegment(*list(map(fcvec, i)))
        else:
            out = part.BSplineCurve()
            out.interpolate(list(map(fcvec, i)))
        wire.append(out.toShape())
    return part.Wire(wire)


def rotate_tooth(base_tooth, num_teeth):
    rot = app.Matrix()
    rot.rotateZ(2 * np.pi / num_teeth)
    flat_shape = [base_tooth]
    for t in range(num_teeth - 1):
        flat_shape.append(flat_shape[-1].transformGeometry(rot))
    return part.Wire(flat_shape)


def fillet_between_edges(edge_1, edge_2, radius):
    # assuming edges are in a plane
    # extracting vertices
    try:
        from Part import ChFi2d
    except ImportError:
        app.Console.PrintWarning(
            "Your freecad version has no python bindings for 2d-fillets"
        )
        return [edge_1, edge_2]

    api = ChFi2d.FilletAPI()
    p1 = edge_1.valueAt(edge_1.FirstParameter)
    p2 = edge_1.valueAt(edge_1.LastParameter)
    p3 = edge_2.valueAt(edge_2.FirstParameter)
    p4 = edge_2.valueAt(edge_2.LastParameter)
    t1 = p2 - p1
    t2 = p4 - p3
    n = t1.cross(t2)
    pln = part.Plane(edge_1.valueAt(edge_1.FirstParameter), n)
    api.init(edge_1, edge_2, pln)
    if api.perform(radius) > 0:
        p0 = (p2 + p3) / 2
        fillet, e1, e2 = api.result(p0)
        return part.Wire([e1, fillet, e2]).Edges
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
