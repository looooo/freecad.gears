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
import numpy as np

from freecad import app
from freecad import gui
from freecad import part

from pygears import __version__
from pygears._functions import arc_from_points_and_center

from PySide import QtCore
from PySide import QtGui
from PySide import QtWidgets
from PySide.QtGui import (QGroupBox, QMessageBox, QIcon)
from PySide.QtWidgets import (
    QGridLayout,
    QLabel,
    QCheckBox,
    QDoubleSpinBox,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QLineEdit
)

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP


def fcvec(x):
    """tranforms a list or numpy array to a FreeCAD Vector which is
    always 3d

    Args:
        x (iterable): either a 2d or 3d vector

    Returns:
        freecad.app.Vector: _description_
    """
    if len(x) == 2:
        return app.Vector(x[0], x[1], 0)
    else:
        return app.Vector(x[0], x[1], x[2])

def updateTaskTitleIcon(task):
    from PySide import QtGui
    if hasattr(task, "form"):
        if hasattr(task.obj.ViewObject.Proxy, "getIcon"):
            task.form.setWindowIcon(
                QtGui.QIcon(task.obj.ViewObject.Proxy.getIcon())
            )
    return

def isPartDesign(obj):
    if isSketchObject(obj):
        parent = getParentBody(obj)
        if parent is None:
            return False
        return isinstance(parent, Part.BodyBase)
    return obj.TypeId.startswith("PartDesign::")

def isSketchObject(obj):
    return obj.TypeId.startswith("Sketcher::")

def getParentBody(obj):
    if hasattr(obj, "getParent"):
        return obj.getParent()
    if hasattr(obj, "getParents"):  # Probably FreeCadLink version.
        if len(obj.getParents()) == 0:
            return None
        return obj.getParents()[0][0]
    return None


class ViewProviderGear:
    """
    The base Viewprovider for the gears
    """

    def __init__(self, obj, icon_fn=None):
        # Set this object to the proxy object of the actual view provider
        obj.Proxy = self
        self.Object = obj.Object
        self._check_attr()
        dirname = os.path.dirname(__file__)
        self.icon_fn = icon_fn or os.path.join(dirname, "icons", "involutegear.svg")

    def _check_attr(self):
        """
        Check for missing attributes.
        """
        if not hasattr(self, "icon_fn"):
            setattr(
                self,
                "icon_fn",
                os.path.join(os.path.dirname(__file__), "icons", "involutegear.svg"),
            )

    def attach(self, obj):
        self.Object = obj.Object  # borrowed from SheetMetal
        #self.vobj = vobj

    def getIcon(self):
        self._check_attr()
        return self.icon_fn

    def dumps(self):
        self._check_attr()
        return {"icon_fn": self.icon_fn}

    def loads(self, state):
        if state and "icon_fn" in state:
            self.icon_fn = state["icon_fn"]

    def __getstate__(self):
        self._check_attr()
        return {"icon_fn": self.icon_fn}

    def __setstate__(self, state):
        if state and "icon_fn" in state:
            self.icon_fn = state["icon_fn"]


class BaseGear:
    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyString",
            "version",
            "version",
            QT_TRANSLATE_NOOP("App::Property", "freecad.gears-version"),
            1,
        )
        obj.version = __version__
        self.make_attachable(obj)

    def make_attachable(self, obj):
        """
        Needed to make this object "attachable",
        aka able to attach parameterically to other objects
        cf. https://wiki.freecadweb.org/Scripted_objects_with_attachment
        """
        if int(app.Version()[0]) == 0 and int(app.Version()[1]) >= 19 or int(app.Version()[0]) == 1:
            obj.addExtension("Part::AttachExtensionPython")
        else:
            obj.addExtension("Part::AttachExtensionPython", obj)
        # unveil the "Placement" property, which seems hidden by default in PartDesign
        obj.setEditorMode("Placement", 0)  # non-readonly non-hidden

    def execute(self, obj):
        # checksbackwardcompatibility:
        if not hasattr(obj, "positionBySupport"):
            self.make_attachable(obj)
        obj.positionBySupport()

        # Backward compatibility for old files
        if hasattr(obj, "teeth"):
            obj.addProperty(
                "App::PropertyIntegerConstraint",
                "num_teeth",
                "base",
                "number of teeth",
            ).num_teeth = (15, 3, 10000, 1)
            app.Console.PrintLog(
                app.Qt.translate(
                    "Log", "Migrating 'teeth' property to 'num_teeth' on {} part\n"
                ).format(obj.Name)
            )
            obj.num_teeth = obj.teeth  # Copy old value to new property
            obj.removeProperty("teeth")  # Remove the old property

        gear_shape = self.generate_gear_shape(obj)
        if hasattr(obj, "BaseFeature") and obj.BaseFeature != None:
            # we're inside a PartDesign Body, thus need to fuse with the base feature
            gear_shape.Placement = (
                obj.Placement
            )  # ensure the gear is placed correctly before fusing
            result_shape = obj.BaseFeature.Shape.fuse(gear_shape)
            result_shape.transformShape(
                obj.Placement.inverse().toMatrix(), True
            )  # account for setting obj.Shape below moves the shape to obj.Placement, ignoring its previous placement
            obj.Shape = result_shape
        else:
            obj.Shape = gear_shape

    def generate_gear_shape(self, obj):
        """
        This method has to return the TopoShape of the gear.
        """
        raise NotImplementedError("generate_gear_shape not implemented")


    def loads(self, state):
        pass

    def dumps(self):
        pass

    def __setstate__(self, state):
        pass

    def __getstate__(self):
        pass


def part_arc_from_points_and_center(point_1, point_2, center):
    """_summary_

    Args:
        point_1 (list, np.array with 2 values): 2d point start of arc
        point_1 (list, np.array with 2 values): 2d point end of arc
        center (list, np.array with 2 values): the 2d center of the arc

    Returns:
        freecad.part.Arc: a arc with
    """
    p_1, p_12, p_2 = arc_from_points_and_center(point_1, point_2, center)
    return part.Arc(fcvec(p_1), fcvec(p_12), fcvec(p_2))


def helical_extrusion(face, height, angle, double_helix=False):
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


def fillet_between_edges(edge_1, edge_2, radius, reversed=False):
    # assuming edges are in a plane
    # extracting vertices
    fillet2d_api = part.ChFi2d.FilletAPI()
    p1 = edge_1.valueAt(edge_1.FirstParameter)
    p2 = edge_1.valueAt(edge_1.LastParameter)
    p3 = edge_2.valueAt(edge_2.FirstParameter)
    p4 = edge_2.valueAt(edge_2.LastParameter)
    t1 = p2 - p1
    t2 = p4 - p3
    n = t1.cross(t2) * (-reversed * 2 + 1)
    pln = part.Plane(edge_1.valueAt(edge_1.FirstParameter), n)
    fillet2d_api.init(edge_1, edge_2, pln)
    if fillet2d_api.perform(radius) > 0:
        p0 = (p2 + p3) / 2
        fillet, e1, e2 = fillet2d_api.result(p0)
        return part.Wire([e1, fillet, e2]).Edges
    else:
        return None


def insert_fillet(edges, pos, radius, reversed=False):
    assert pos < (len(edges) - 1)
    e1 = edges[pos]
    e2 = edges[pos + 1]
    if radius > 0:
        fillet_edges = fillet_between_edges(e1, e2, radius, reversed)
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


class GearsBaseTaskPanel(object):
    '''
    Root class for all Gears task panels.
    Provides shared methods for all task panels.
    '''

    def __init__(self, obj):

        self.obj = obj
        return

    def translateTaskPanel(self):
        self.header_module = QT_TRANSLATE_NOOP("Gear_TaskPanel", "Module")
        self.header_number_of_teeth = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Number of Teeth"
        )
        self.header_transverse_pitch = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Transverse Pitch"
        )
        self.header_pitch_diameter = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Pitch Diameter"
        )
        self.header_helix_angle = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Helix Angle"
        )
        self.header_spiral_angle = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Spiral Angle"
        )
        self.header_transverse_height = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Transverse Height"
        )
        self.header_thickness = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Thickness"
        )
        self.tool_tip_module = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Sets the module for the gear's teeth"
        )
        self.tool_tip_number_of_teeth = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Sets the number of teeth"
        )
        self.tool_tip_toggle_helical = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Toggles between spur gearig and helical gearig"
        )
        self.tool_tip_reverse_helix = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Toggles between positive and negative helix angle"
        )
        self.tool_tip_double_helix = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Toggles between single and double helix"
        )
        self.tool_tip_toggle_spiral = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Toggles between spur gearig and spiral gearig"
        )
        self.tool_tip_reverse_spiral = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Toggles between positive and negative spiral angle"
        )
        self.tool_tip_toggle_update = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Toggles between manual and automatic update"
        )
        self.tool_tip_apply = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Applies changes and updates the shape"
        )
        self.multyply_mm = QT_TRANSLATE_NOOP("Gear_TaskPanel", "mm *")
        self.multyply_mm_pi = QT_TRANSLATE_NOOP("Gear_TaskPanel", "mm * Pi =")
        self.equals = QT_TRANSLATE_NOOP("Gear_TaskPanel", "=")
        self.apply = QT_TRANSLATE_NOOP("Gear_TaskPanel", "Apply")
        self.option_spur_gearing = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Spur Gearing"
        )
        self.option_helical_gearing = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Helical Gearing"
        )
        self.option_spiral_gearing = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Spiral Gearing"
        )
        self.option_single_helix = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Singel Helix"
        )
        self.option_double_helix = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Double Helix"
        )
        self.option_forward_angle = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Forward Angle"
        )
        self.option_reverse_angle = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Reverse Angle"
        )
        self.option_manual_update = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Manual Update -->"
        )
        self.option_auto_update = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Automatic Update"
        )
        
    #---------------------------------------------------------------------------
    # Group boxes and sub-boxes including widgets
    #---------------------------------------------------------------------------

    def groupBoxWithGrid(self, title = "", icon = None):
        '''Creates an empty instance of a QGroupBox providing a QGridLayout'''
        groupBox = QGroupBox(title)
        grid = QGridLayout()
        groupBox.setLayout(grid)
        return groupBox, grid

    def addSizeWidgetsInvolute(self, grid):
        '''Provides widgets to control the size of the Gear'''

        self.label_module = QLabel(self.header_module)
        grid.addWidget(self.label_module, 1, 0)

        self.label_num_teeth = QLabel(self.header_number_of_teeth)
        grid.addWidget(self.label_num_teeth, 1, 2)

        self.label_pitch_dia = QLabel(self.header_pitch_diameter)
        grid.addWidget(self.label_pitch_dia, 1, 4)

        self.ds_box_module = QDoubleSpinBox()
        self.ds_box_module.setValue(self.module)
        #self.ds_box_module.setValue("{} mm".format(self.module))
        self.ds_box_module.setToolTip(self.tool_tip_module)
        self.ds_box_module.valueChanged.connect(
            self.onDoubleSpinBoxModuleChanged
        )
        grid.addWidget(self.ds_box_module, 2, 0)  #, 0, -1)

        self.label_multiply = QLabel(self.multyply_mm)
        grid.addWidget(self.label_multiply, 2, 1)  #, -1, 1)

        self.ds_box_num_teeth = QDoubleSpinBox()
        self.ds_box_num_teeth.setValue(self.num_teeth)
        self.ds_box_num_teeth.setToolTip(self.tool_tip_number_of_teeth)
        self.ds_box_num_teeth.valueChanged.connect(
            self.onDoubleSpinBoxNumTeethChanged
        )
        grid.addWidget(self.ds_box_num_teeth, 2, 2)  #, 1, -1)

        self.label_equals = QLabel(self.equals)
        grid.addWidget(self.label_equals, 2, 3)  #, -1, 1)

        self.label_pitch_diameter = QLabel(str(self.module * self.num_teeth))
        grid.addWidget(self.label_pitch_diameter, 2, 4)

    def addSizeWidgetsInvoluteRack(self, grid):
        '''Provides widgets to controll the size of the Gear'''

        self.label_module = QLabel(self.header_module)
        grid.addWidget(self.label_module, 1, 0)

        self.label_transverse_pitch = QLabel(self.header_transverse_pitch)
        grid.addWidget(self.label_transverse_pitch, 1, 2)

        self.ds_box_module = QDoubleSpinBox()
        self.ds_box_module.setValue(self.module)
        self.ds_box_module.setToolTip(self.tool_tip_module)
        self.ds_box_module.valueChanged.connect(
            self.onDoubleSpinBoxRackModuleChanged
        )
        grid.addWidget(self.ds_box_module, 2, 0)  #, 0, -1)

        self.label_multiply = QLabel(self.multyply_mm_pi)
        grid.addWidget(self.label_multiply, 2, 1)  #, -1, 1)

        self.label_transverse_pitch_value = QLabel(
            str(round(self.module * np.pi, 2))
        )
        grid.addWidget(self.label_transverse_pitch_value, 2, 2)

    def addSizeWidgetsBevel(self, grid):
        '''Provides widgets to controll the size of the Gear'''

        self.label_module = QLabel(self.header_module)
        grid.addWidget(self.label_module, 1, 0)

        self.label_num_teeth = QLabel(self.header_number_of_teeth)
        grid.addWidget(self.label_num_teeth, 1, 2)

        self.label_pitch_dia = QLabel(self.header_pitch_diameter)
        grid.addWidget(self.label_pitch_dia, 1, 4)

        self.ds_box_module = QDoubleSpinBox()
        self.ds_box_module.setValue(self.module)
        #self.ds_box_module.setValue("{} mm".format(self.module))
        self.ds_box_module.setToolTip(self.tool_tip_module)
        self.ds_box_module.valueChanged.connect(
            self.onDoubleSpinBoxModuleChanged
        )
        grid.addWidget(self.ds_box_module, 2, 0)  #, 0, -1)

        self.label_multiply = QLabel(self.multyply_mm)
        grid.addWidget(self.label_multiply, 2, 1)  #, -1, 1)

        self.ds_box_num_teeth = QDoubleSpinBox()
        self.ds_box_num_teeth.setValue(self.num_teeth)
        self.ds_box_num_teeth.setToolTip(self.tool_tip_number_of_teeth)
        self.ds_box_num_teeth.valueChanged.connect(
            self.onDoubleSpinBoxNumTeethChanged
        )
        grid.addWidget(self.ds_box_num_teeth, 2, 2)  #, 1, -1)

        self.label_equals = QLabel(self.equals)
        grid.addWidget(self.label_equals, 2, 3)  #, -1, 1)

        self.label_pitch_diameter = QLabel(str(self.module * self.num_teeth))

        grid.addWidget(self.label_pitch_diameter, 2, 4)


    def addHelixAngleWidgets(self, grid):
        '''Provides widgets to control helix parameters'''

        self.button_helical = QPushButton(self.option_spur_gearing)
        self.button_helical.setToolTip(self.tool_tip_toggle_helical)
        self.button_helical.clicked.connect(self.onButtonHelical)
        grid.addWidget(self.button_helical, 1, 0)

        self.label_helix_angle = QLabel(self.header_helix_angle)
        self.label_helix_angle.hide()
        grid.addWidget(self.label_helix_angle, 1, 1)

        self.button_double = QPushButton(self.option_single_helix)
        self.button_double.setToolTip(self.tool_tip_double_helix)
        self.button_double.hide()
        self.button_double.clicked.connect(self.onButtonDouble)
        grid.addWidget(self.button_double, 1, 2)

        self.ds_box_helix_angle = QDoubleSpinBox()
        self.ds_box_helix_angle.setMaximum(60)
        self.ds_box_helix_angle.setMinimum(-60)
        self.ds_box_helix_angle.setValue(self.helix_angle)
        self.ds_box_helix_angle.hide()
        self.ds_box_helix_angle.valueChanged.connect(
            self.onDoubleSpinBoxHelixAngelChanged
        )
        grid.addWidget(self.ds_box_helix_angle, 2, 1)

        self.button_reverse_angle = QPushButton(self.option_forward_angle)
        self.button_reverse_angle.setToolTip(self.tool_tip_reverse_helix)
        self.button_reverse_angle.hide()
        self.button_reverse_angle.clicked.connect(self.onButtonReverseAngle)
        grid.addWidget(self.button_reverse_angle, 2, 2)

    def addBetaAngleWidgets(self, grid):
        '''Provides widgets to control spiral parameters'''

        self.button_spiral = QPushButton(self.option_spur_gearing)
        self.button_spiral.setToolTip(self.tool_tip_toggle_spiral)
        self.button_spiral.clicked.connect(self.onButtonSpiral)
        grid.addWidget(self.button_spiral, 1, 0)

        self.label_beta_angle = QLabel(self.header_spiral_angle)
        self.label_beta_angle.hide()
        grid.addWidget(self.label_beta_angle, 1, 1)

        self.button_reverse_spiral = QPushButton(self.option_forward_angle)
        self.button_reverse_spiral.setToolTip(self.tool_tip_reverse_spiral)
        self.button_reverse_spiral.hide()
        self.button_reverse_spiral.clicked.connect(self.onButtonReverseSpiral)
        grid.addWidget(self.button_reverse_spiral, 2, 0)

        self.ds_box_beta = QDoubleSpinBox()
        self.ds_box_beta.setMaximum(60)
        self.ds_box_beta.setMinimum(-60)
        self.ds_box_beta.setValue(self.beta)
        self.ds_box_beta.hide()
        self.ds_box_beta.valueChanged.connect(
            self.onDoubleSpinBoxBetaChanged
        )
        grid.addWidget(self.ds_box_beta, 2, 1)


    def addUpdateWidgets(self, grid):
        '''Provides widgets to choose manual update'''

        self.button_update = QPushButton(self.option_manual_update)
        self.button_update.setToolTip(self.tool_tip_toggle_update)
        self.button_update.setEnabled(True)
        self.button_update.clicked.connect(self.onButtonUpdate)
        grid.addWidget(self.button_update, 1, 0)

        self.button_apply = QPushButton(self.apply)
        self.button_apply.setToolTip(self.tool_tip_apply)
        self.button_apply.setEnabled(False)
        self.button_apply.clicked.connect(self.onButtonApply)
        grid.addWidget(self.button_apply, 1, 1)

    def addUpdateBevelWidgets(self, grid):
        '''Provides widgets to choose manual update'''

        self.button_update = QPushButton(self.option_manual_update)
        self.button_update.setToolTip(self.tool_tip_toggle_update)
        self.button_update.setEnabled(True)
        self.button_update.clicked.connect(self.onButtonUpdate)
        grid.addWidget(self.button_update, 1, 0)

        self.button_apply = QPushButton(self.apply)
        self.button_apply.setToolTip(self.tool_tip_apply)
        self.button_apply.setEnabled(False)
        self.button_apply.clicked.connect(self.onButtonApplyBevel)
        grid.addWidget(self.button_apply, 1, 1)


    def addTransverseHightWidgets(self, grid):
        '''Sets the transverse height'''

        self.label_height = QLabel(self.header_transverse_height)
        grid.addWidget(self.label_height, 1, 0)

        self.ds_box_height = QDoubleSpinBox()
        self.ds_box_height.setMaximum(10000)
        self.ds_box_height.setValue(self.height)
        self.ds_box_height.valueChanged.connect(
            self.onDoubleSpinBoxHeightChanged
        )
        grid.addWidget(self.ds_box_height, 1, 1)

    def addThicknessWidgets(self, grid):
        '''
        Sets the outer thickness of internal gears
        or the bottom thickness of racks
        '''
        self.label_thickness = QLabel(self.header_thickness)
        grid.addWidget(self.label_thickness, 1, 0)

        self.ds_box_thickness = QDoubleSpinBox()
        self.ds_box_thickness.setMaximum(10000)
        self.ds_box_thickness.setValue(self.thickness)
        self.ds_box_thickness.valueChanged.connect(
            self.onDoubleSpinBoxThicknessChanged
        )
        grid.addWidget(self.ds_box_thickness, 1, 1)

    #---------------------------------------------------------------------------
    # Logic blocks controlling the interaction of widgets
    #---------------------------------------------------------------------------
    # Size:
    def onDoubleSpinBoxModuleChanged(self, value):
        '''Updates the module value'''
        self.module = value
        self.pitch_diameter = self.module * self.num_teeth
        self.label_pitch_diameter.setText("{} mm".format(self.pitch_diameter))
        self.button_apply.setEnabled(True)

    def onDoubleSpinBoxRackModuleChanged(self, value):
        '''Updates the module value'''
        self.module = value
        self.transverse_pitch = self.module * np.pi
        self.label_transverse_pitch_value.setText(
            "{} mm".format(round(self.transverse_pitch, 2))
        )
        self.button_apply.setEnabled(True)

    def onDoubleSpinBoxNumTeethChanged(self, value):
        '''Updates the number of teeth'''
        self.num_teeth = value
        self.pitch_diameter = self.module * self.num_teeth
        self.label_pitch_diameter.setText(str(self.pitch_diameter))
        self.button_apply.setEnabled(True)

    # Helix:
    def onButtonHelical(self, value):
        '''
        Toggles if open/hollow profiles are automatically filletd
        '''
        if self.button_helical.text() == self.option_spur_gearing:
            self.button_helical.setText(self.option_helical_gearing)
            self.label_helix_angle.show()
            self.button_double.show()
            self.button_reverse_angle.show()
            self.ds_box_helix_angle.show()
            self.ds_box_helix_angle.setValue(10)  # default reset angle
            self.button_apply.setEnabled(True)
        else:
            self.button_helical.setText(self.option_spur_gearing)
            self.label_helix_angle.hide()
            self.button_double.hide()
            self.button_reverse_angle.hide()
            self.ds_box_helix_angle.hide()
            self.ds_box_helix_angle.setValue(0)
            self.button_apply.setEnabled(True)

        if self.auto_recompute:
            self.onButtonApply()

    def onButtonDouble(self, value):
        '''
        Toggles betwen single and double helix
        '''
        if self.button_double.text() == self.option_single_helix:
            self.button_double.setText(self.option_double_helix)
            self.double_helix = True
            self.button_apply.setEnabled(True)
        else:
            self.button_double.setText(self.option_single_helix)
            self.double_helix = False
            self.button_apply.setEnabled(True)

        if self.auto_recompute:
            self.onButtonApply()

    def onButtonReverseAngle(self, value):
        '''
        Toggles between positive and negative helix angle
        '''
        if self.button_reverse_angle.text() == self.option_forward_angle:
            self.button_reverse_angle.setText(self.option_reverse_angle)
            #self.button_apply.setEnabled(True)
        else:
            self.button_reverse_angle.setText(self.option_forward_angle)
        self.helix_angle *= -1
        self.ds_box_helix_angle.setValue(self.helix_angle)
        self.button_apply.setEnabled(True)

        if self.auto_recompute:
            self.onButtonApply()

    def onDoubleSpinBoxHelixAngelChanged(self, value):
        '''
        Sets the helix angle
        '''
        self.helix_angle = value
        self.ds_box_helix_angle.setValue(self.helix_angle)
        self.button_apply.setEnabled(True)

    def onDoubleSpinBoxBetaChanged(self, value):
        '''
        Sets the beta angle
        '''
        self.beta = value
        self.ds_box_beta_angle.setValue(self.beta)
        self.button_apply.setEnabled(True)

    # Spiral:
    def onButtonSpiral(self, value):
        '''
        Toggles between spur gearing and spiral gearing
        '''
        if self.button_spiral.text() == self.option_spur_gearing:
            self.button_spiral.setText(self.option_spiral_gearing)
            self.label_beta_angle.show()
            self.button_reverse_spiral.show()
            self.ds_box_beta.show()
            self.ds_box_beta.setValue(10)  # default reset angle
        else:
            self.button_spiral.setText(self.option_spur_gearing)
            self.label_beta_angle.hide()
            self.button_reverse_spiral.hide()
            self.ds_box_beta.hide()
            self.ds_box_beta.setValue(0)
        self.button_apply.setEnabled(True)

        if self.auto_recompute:
            self.onButtonApplyBevel()

    def onButtonReverseSpiral(self, value):
        '''
        Toggles between positive and negative spiral angle
        '''
        if self.button_reverse_spiral.text() == self.option_forward_angle:
            self.button_reverse_spiral.setText(self.option_reverse_angle)
            #self.button_apply.setEnabled(True)
        else:
            self.button_reverse_spiral.setText(self.option_forward_angle)
        self.beta *= -1
        self.ds_box_beta.setValue(self.beta)
        self.button_apply.setEnabled(True)

        if self.auto_recompute:
            self.onButtonApplyBevel()

    def onDoubleSpinBoxBetaChanged(self, value):
        '''
        Sets the beta angle
        '''
        self.beta = value
        self.ds_box_beta.setValue(self.beta)
        self.button_apply.setEnabled(True)

    # Height:
    def onDoubleSpinBoxHeightChanged(self, value):
        '''
        Sets the transverse height
        '''
        self.height = value
        self.ds_box_height.setValue(self.height)
        self.button_apply.setEnabled(True)

    def onDoubleSpinBoxThicknessChanged(self, value):
        '''
        Sets the transverse height
        '''
        self.thickness = value
        self.ds_box_thickness.setValue(self.thickness)
        self.button_apply.setEnabled(True)

    # Update:
    def onButtonUpdate(self, value):
        '''Toggles the automatic update'''
        if self.button_update.text() == self.option_auto_update:
            self.button_update.setText(self.option_manual_update)
            self.auto_recompute = False
        else:
            self.button_update.setText(self.option_auto_update)
            self.auto_recompute = True

    def onButtonApply(self, value = None):
        '''
        Updates the object parameters with the task panel settings
        and runs a recompute
        '''
        self.obj.num_teeth = int(self.num_teeth)
        self.obj.module = self.module
        self.obj.helix_angle = self.helix_angle
        try:
            self.obj.double_helix = self.double_helix
        except:
            pass
        try:
            self.obj.pitch_diameter = self.pitch_diameter
        except:
            pass
        try:
            self.obj.transverse_pitch = self.pitch_diameter
        except:
            pass
        try:
            self.obj.thickness = self.thickness
        except:
            pass
        self.obj.height = self.height

        app.ActiveDocument.recompute()
        self.button_apply.setEnabled(False)

    def onButtonApplyBevel(self, value = None):
        '''
        Updates the object parameters with the task panel settings
        and runs a recompute
        '''
        self.obj.num_teeth = int(self.num_teeth)
        self.obj.module = self.module
        self.obj.beta = self.beta
        #self.obj.dw = self.pitch_diameter
        self.obj.height = self.height

        app.ActiveDocument.recompute()
        self.button_apply.setEnabled(False)


    def accept(self):
        '''
        This is triggered by the panel's OK button.
        '''
        gui.Control.closeDialog()
        print("Accepted. ")

    def reject(self):
        '''
        This is triggered by the panel's Cancel button.
        '''
        gui.Control.closeDialog()
        print("Canceled, there is nothing left to do!")
