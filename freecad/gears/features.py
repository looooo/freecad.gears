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

import FreeCAD as App
import Part

import numpy as np
import math
from pygears import __version__
from pygears.involute_tooth import InvoluteTooth, InvoluteRack
from pygears.cycloid_tooth import CycloidTooth
from pygears.bevel_tooth import BevelTooth
from pygears._functions import (
    rotation3D,
    rotation,
    reflection,
    arc_from_points_and_center,
)



def fcvec(x):
    if len(x) == 2:
        return App.Vector(x[0], x[1], 0)
    else:
        return App.Vector(x[0], x[1], x[2])


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
        if int(App.Version()[1]) >= 19:
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


class LanternGear(BaseGear):
    def __init__(self, obj):
        super(LanternGear, self).__init__(obj)
        obj.addProperty(
            "App::PropertyInteger", "teeth", "gear_parameter", "number of teeth"
        )
        obj.addProperty("App::PropertyLength", "module", "base", "module")
        obj.addProperty(
            "App::PropertyLength",
            "bolt_radius",
            "base",
            "the bolt radius of the rack/chain",
        )
        obj.addProperty("App::PropertyLength", "height", "base", "height")
        obj.addProperty(
            "App::PropertyInteger",
            "num_profiles",
            "accuracy",
            "number of profiles used for loft",
        )
        obj.addProperty(
            "App::PropertyFloat",
            "head",
            "tolerance",
            "head * module = additional length of head",
        )

        obj.teeth = 15
        obj.module = "1. mm"
        obj.bolt_radius = "1 mm"

        obj.height = "5. mm"
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
            return r_0 * (
                phi_min**2 * r_0
                - 2 * phi_min * r_0 * np.sin(phi_min)
                - 2 * phi_min * r_r
                - 2 * r_0 * np.cos(phi_min)
                + 2 * r_0
                + 2 * r_r * np.sin(phi_min)
            )

        try:
            import scipy.optimize

            phi_min = scipy.optimize.root(
                find_phi_min, (phi_max + r_r / r_0 * 4) / 5
            ).x[0]  # , r_r / r_0, phi_max)
        except ImportError:
            App.Console.PrintWarning(
                "scipy not available. Can't compute numerical root. Leads to a wrong bolt-radius"
            )
            phi_min = r_r / r_0

        # phi_min = 0 # r_r / r_0
        phi = np.linspace(phi_min, phi_max, fp.num_profiles)
        x = r_0 * (np.cos(phi) + phi * np.sin(phi)) - r_r * np.sin(phi)
        y = r_0 * (np.sin(phi) - phi * np.cos(phi)) + r_r * np.cos(phi)
        xy1 = np.array([x, y]).T
        p_1 = xy1[0]
        p_1_end = xy1[-1]
        bsp_1 = Part.BSplineCurve()
        bsp_1.interpolate(list(map(fcvec, xy1)))
        w_1 = bsp_1.toShape()

        xy2 = xy1 * np.array([1.0, -1.0])
        p_2 = xy2[0]
        p_2_end = xy2[-1]
        bsp_2 = Part.BSplineCurve()
        bsp_2.interpolate(list(map(fcvec, xy2)))
        w_2 = bsp_2.toShape()

        p_12 = np.array([r_0 - r_r, 0.0])

        arc = Part.Arc(
            App.Vector(*p_1, 0.0), App.Vector(*p_12, 0.0), App.Vector(*p_2, 0.0)
        ).toShape()

        rot = rotation(-np.pi * 2 / teeth)
        p_3 = rot(np.array([p_2_end]))[0]
        # l = Part.LineSegment(fcvec(p_1_end), fcvec(p_3)).toShape()
        l = part_arc_from_points_and_center(
            p_1_end, p_3, np.array([0.0, 0.0])
        ).toShape()
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
            "Pin ball circle radius(overrides Tooth Pitch",
        )
        obj.addProperty(
            "App::PropertyFloat", "roller_diameter", "gear_parameter", "Roller Diameter"
        )
        obj.addProperty(
            "App::PropertyFloat", "eccentricity", "gear_parameter", "Eccentricity"
        )
        obj.addProperty(
            "App::PropertyAngle",
            "pressure_angle_lim",
            "gear_parameter",
            "Pressure angle limit",
        )
        obj.addProperty(
            "App::PropertyFloat",
            "pressure_angle_offset",
            "gear_parameter",
            "Offset in pressure angle",
        )
        obj.addProperty(
            "App::PropertyInteger",
            "teeth_number",
            "gear_parameter",
            "Number of teeth in Cam",
        )
        obj.addProperty(
            "App::PropertyInteger",
            "segment_count",
            "gear_parameter",
            "Number of points used for spline interpolation",
        )
        obj.addProperty(
            "App::PropertyLength",
            "hole_radius",
            "gear_parameter",
            "Center hole's radius",
        )

        obj.addProperty(
            "App::PropertyBool", "show_pins", "Pins", "Create pins in place"
        )
        obj.addProperty("App::PropertyLength", "pin_height", "Pins", "height")
        obj.addProperty(
            "App::PropertyBool",
            "center_pins",
            "Pins",
            "Center pin Z axis to generated disks",
        )

        obj.addProperty(
            "App::PropertyBool", "show_disk0", "Disks", "Show main cam disk"
        )
        obj.addProperty(
            "App::PropertyBool",
            "show_disk1",
            "Disks",
            "Show another reversed cam disk on top",
        )
        obj.addProperty("App::PropertyLength", "disk_height", "Disks", "height")

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
        # Part.Wire(Part.makeCircle(minRadius,App.Vector(-e, 0, 0)))
        # Part.Wire(Part.makeCircle(maxRadius,App.Vector(-e, 0, 0)))

        App.Console.PrintMessage("Generating cam disk\r\n")
        # generate the cam profile - note: shifted in -x by eccentricicy amount
        i = 0
        x = self.calc_x(p, d, e, n, q * i / float(n))
        y = self.calc_y(p, d, e, n, q * i / n)
        x, y = self.check_limit(x, y, maxRadius, minRadius, c)
        points = [App.Vector(x - e, y, 0)]
        for i in range(0, s):
            x = self.calc_x(p, d, e, n, q * (i + 1) / n)
            y = self.calc_y(p, d, e, n, q * (i + 1) / n)
            x, y = self.check_limit(x, y, maxRadius, minRadius, c)
            points.append([x - e, y, 0])

        wi = make_bspline_wire([points])
        wires = []
        mat = App.Matrix()
        mat.move(App.Vector(e, 0.0, 0.0))
        mat.rotateZ(2 * np.pi / n)
        mat.move(App.Vector(-e, 0.0, 0.0))
        for _ in range(n):
            wi = wi.transformGeometry(mat)
            wires.append(wi)

        cam = Part.Face(Part.Wire(wires))
        # add a circle in the center of the cam
        if fp.hole_radius.Value:
            centerCircle = Part.Face(
                Part.Wire(Part.makeCircle(fp.hole_radius.Value, App.Vector(-e, 0, 0)))
            )
            cam = cam.cut(centerCircle)

        to_be_fused = []
        if fp.show_disk0 == True:
            if fp.disk_height.Value == 0:
                to_be_fused.append(cam)
            else:
                to_be_fused.append(cam.extrude(App.Vector(0, 0, fp.disk_height.Value)))

        # secondary cam disk
        if fp.show_disk1 == True:
            App.Console.PrintMessage("Generating secondary cam disk\r\n")
            second_cam = cam.copy()
            mat = App.Matrix()
            mat.rotateZ(np.pi)
            mat.move(App.Vector(-e, 0, 0))
            if n % 2 == 0:
                mat.rotateZ(np.pi / n)
            mat.move(App.Vector(e, 0, 0))
            second_cam = second_cam.transformGeometry(mat)
            if fp.disk_height.Value == 0:
                to_be_fused.append(second_cam)
            else:
                to_be_fused.append(
                    second_cam.extrude(App.Vector(0, 0, -fp.disk_height.Value))
                )

        # pins
        if fp.show_pins == True:
            App.Console.PrintMessage("Generating pins\r\n")
            pins = []
            for i in range(0, n + 1):
                x = p * n * math.cos(2 * math.pi / (n + 1) * i)
                y = p * n * math.sin(2 * math.pi / (n + 1) * i)
                pins.append(Part.Wire(Part.makeCircle(d / 2, App.Vector(x, y, 0))))

            pins = Part.Face(pins)

            z_offset = -fp.pin_height.Value / 2
            if fp.center_pins == True:
                if fp.show_disk0 == True and fp.show_disk1 == False:
                    z_offset += fp.disk_height.Value / 2
                elif fp.show_disk0 == False and fp.show_disk1 == True:
                    z_offset += -fp.disk_height.Value / 2
            # extrude
            if z_offset != 0:
                pins.translate(App.Vector(0, 0, z_offset))
            if fp.pin_height != 0:
                pins = pins.extrude(App.Vector(0, 0, fp.pin_height.Value))

            to_be_fused.append(pins)

        if to_be_fused:
            return Part.makeCompound(to_be_fused)


def part_arc_from_points_and_center(p_1, p_2, m):
    p_1, p_12, p_2 = arc_from_points_and_center(p_1, p_2, m)
    return Part.Arc(
        App.Vector(*p_1, 0.0), App.Vector(*p_12, 0.0), App.Vector(*p_2, 0.0)
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
        spine = Part.makeHelix(pitch, height / 2.0, radius, cone_angle, direction)
        spine.translate(App.Vector(0, 0, height / 2.0))
        face = face.translated(
            App.Vector(0, 0, height / 2.0)
        )  # don't transform our argument
    else:
        spine = Part.makeHelix(pitch, height, radius, cone_angle, direction)

    def make_pipe(path, profile):
        """
        returns (shell, last_wire)
        """
        mkPS = Part.BRepOffsetAPI.MakePipeShell(path)
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
        shell_faces.append(face)  # the bottom is what we extruded
    shell = Part.makeShell(shell_faces)
    # shell.sewShape() # fill gaps that may result from accumulated tolerances. Needed?
    # shell = shell.removeSplitter() # refine. Needed?
    return Part.makeSolid(shell)


def make_face(edge1, edge2):
    v1, v2 = edge1.Vertexes
    v3, v4 = edge2.Vertexes
    e1 = Part.Wire(edge1)
    e2 = Part.LineSegment(v1.Point, v3.Point).toShape().Edges[0]
    e3 = edge2
    e4 = Part.LineSegment(v4.Point, v2.Point).toShape().Edges[0]
    w = Part.Wire([e3, e4, e1, e2])
    return Part.Face(w)


def make_bspline_wire(pts):
    wi = []
    for i in pts:
        out = Part.BSplineCurve()
        out.interpolate(list(map(fcvec, i)))
        wi.append(out.toShape())
    return Part.Wire(wi)


def points_to_wire(pts):
    wire = []
    for i in pts:
        if len(i) == 2:
            # straight edge
            out = Part.LineSegment(*list(map(fcvec, i)))
        else:
            out = Part.BSplineCurve()
            out.interpolate(list(map(fcvec, i)))
        wire.append(out.toShape())
    return Part.Wire(wire)


def rotate_tooth(base_tooth, num_teeth):
    rot = App.Matrix()
    rot.rotateZ(2 * np.pi / num_teeth)
    flat_shape = [base_tooth]
    for t in range(num_teeth - 1):
        flat_shape.append(flat_shape[-1].transformGeometry(rot))
    return Part.Wire(flat_shape)


def fillet_between_edges(edge_1, edge_2, radius):
    # assuming edges are in a plane
    # extracting vertices
    try:
        from Part import ChFi2d
    except ImportError:
        App.Console.PrintWarning(
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
