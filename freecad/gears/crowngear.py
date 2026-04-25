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
import os

from freecad import app
from freecad import gui
from freecad import part

from .basegear import (
    BaseGear,
    fcvec,
    updateTaskTitleIcon,
    GearsBaseTaskPanel,
    ViewProviderGear,
)

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP


class CrownGear(BaseGear):
    """
    A crown gear (also known as a face gear or a contrate gear) is a gear
    which has teeth that project at right angles to the face of the wheel.
    In particular, a crown gear is a type of bevel gear where the pitch cone
    angle is 90 degrees. https://en.wikipedia.org/wiki/Crown_gear
    """

    def __init__(self, obj):
        super(CrownGear, self).__init__(obj)
        obj.addProperty(
            "App::PropertyIntegerConstraint",
            "num_teeth",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "number of teeth"),
        )
        obj.addProperty(
            "App::PropertyIntegerConstraint",
            "other_teeth",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "number of teeth of other gear"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "module",
            "base",
            QT_TRANSLATE_NOOP("App::Property", "module"),
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
            "App::PropertyAngle",
            "pressure_angle",
            "involute",
            QT_TRANSLATE_NOOP("App::Property", "pressure angle"),
        )
        self.add_accuracy_properties(obj)
        obj.num_teeth = (15, 3, 10000, 1)  # default, min, max, step
        obj.other_teeth = (15, 3, 10000, 1)  # default, min, max, step
        obj.module = "1. mm"
        obj.pressure_angle = "20. deg"
        obj.height = "2. mm"
        obj.thickness = "5 mm"
        obj.num_profiles = 4
        obj.preview_mode = True
        self.obj = obj
        obj.Proxy = self

        app.Console.PrintMessage(
            app.Qt.translate(
                "Log",
                "Gear module: Crown gear created, preview_mode = true for improved performance. "
                "Set preview_mode property to false when ready to cut teeth.",
            )
        )


    def add_accuracy_properties(self, obj):
        obj.addProperty(
            "App::PropertyInteger",
            "num_profiles",
            "accuracy",
            QT_TRANSLATE_NOOP("App::Property", "number of profiles used for loft"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "preview_mode",
            "accuracy",
            QT_TRANSLATE_NOOP("App::Property", "if true no boolean operation is done"),
        )

    def profile(self, m, r, r0, t_c, t_i, alpha_w, y0, y1, y2):
        r_ew = m * t_i / 2

        # 1: modifizierter Waelzkreisdurchmesser:
        r_e = r / r0 * r_ew

        # 2: modifizierter Schraegungswinkel:
        alpha = np.arccos(r0 / r * np.cos(alpha_w))

        # 3: winkel phi bei senkrechter stellung eines zahns:
        phi = np.pi / t_i / 2 + (alpha - alpha_w) + (np.tan(alpha_w) - np.tan(alpha))

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
        pts = [[-x1, r, y0], [-x2, r, y0 - y1 - y2], [x2, r, y0 - y1 - y2], [x1, r, y0]]
        pts.append(pts[0])
        return pts

    def generate_gear_shape(self, fp):
        inner_diameter = fp.module.Value * fp.num_teeth
        outer_diameter = inner_diameter + fp.height.Value * 2
        inner_circle = part.Wire(part.makeCircle(inner_diameter / 2.0))
        outer_circle = part.Wire(part.makeCircle(outer_diameter / 2.0))
        inner_circle.reverse()
        face = part.Face([outer_circle, inner_circle])
        solid = face.extrude(app.Vector([0.0, 0.0, -fp.thickness.Value]))
        if fp.preview_mode:
            return solid

        # cutting obj
        alpha_w = np.deg2rad(fp.pressure_angle.Value)
        m = fp.module.Value
        t = fp.num_teeth
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
            poly = part.Wire(part.makePolygon(list(map(fcvec, pts))))
            polies.append(poly)
        loft = part.makeLoft(polies, True)
        rot = app.Matrix()
        rot.rotateZ(2 * np.pi / t)
        cut_shapes = []
        for _ in range(t):
            loft = loft.transformGeometry(rot)
            cut_shapes.append(loft)
        return solid.cut(cut_shapes)

if app.GuiUp:

    class CrownGearViewProvider(ViewProviderGear):

        def __init__(self, obj, icon_fn=None):
            # Set this object to the proxy object of the actual view provider
            obj.Proxy = self
            self._check_attr()
            dirname = os.path.dirname(__file__)
            self.icon_fn = icon_fn or os.path.join(dirname, "icons", "crowngear.svg")

        def _check_attr(self):
            """
            Check for missing attributes.
            """
            if not hasattr(self, "icon_fn"):
                setattr(
                    self,
                    "icon_fn",
                    os.path.join(os.path.dirname(__file__), "icons", "crowngear.svg"),
                )

        def getTaskPanel(self, obj):
            return CrownGearTaskPanel(obj)

    class CrownGearTaskPanel(GearsBaseTaskPanel):
        """Control panel for Crown Gears"""

        def __init__(self, obj):

            self.obj = obj

            self.num_teeth = obj.num_teeth
            self.module = obj.module
            self.other_teeth = obj.other_teeth
            obj.pressure_angle = "20. deg"
            self.height = obj.height
            self.thickness = obj.thickness
            obj.num_profiles = 4
            self.preview_mode = obj.preview_mode

            self.auto_recompute = False

            self.translateTaskPanel()

            #- Add a QGroupBox container with a QGridLayout to group widgets
            self.group_box_0, self.grid_0 = self.groupBoxWithGrid()
            self.group_box_0.setWindowTitle(QT_TRANSLATE_NOOP(
                "Gear_TaskPanel",
                "Crown Gear Parameters"
            ))
            #- Add sub-boxes
            self.group_box_1, self.grid_1 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Size")
            )
            self.group_box_1.setStyleSheet("background-color:#dec")
            self.grid_0.addWidget(self.group_box_1, 0, 0, 1, -1)

            self.group_box_2, self.grid_2 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Other Gear")
            )
            self.group_box_2.setStyleSheet("background-color:#def")
            self.grid_0.addWidget(self.group_box_2, 1, 0, 1, 1)

            self.group_box_3, self.grid_3 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Preview Mode")
            )
            self.group_box_3.setStyleSheet("background-color:#def")
            self.grid_0.addWidget(self.group_box_3, 1, 2)

            self.group_box_4, self.grid_4 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Gear Width")
            )
            self.group_box_4.setStyleSheet("background-color:#fed")
            self.grid_0.addWidget(self.group_box_4, 2, 0, 1, -1)

            self.group_box_5, self.grid_5 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Thickness")
            )
            self.group_box_5.setStyleSheet("background-color:#ffe")
            self.grid_0.addWidget(self.group_box_5, 3, 0, 1, -1)

            self.group_box_6, self.grid_6 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Update")
            )
            self.group_box_6.setStyleSheet("background-color:#ddd")
            self.grid_0.addWidget(self.group_box_6, 10, 0, 1, -1)

            #- Add some widgets to the grids
            self.addSizeWidgetsBevel(self.grid_1)

            self.addOtherGearWidgets(self.grid_2)

            self.addPreviewModeWidgets(self.grid_3)

            self.addTransverseHightWidgets(self.grid_4)

            self.addThicknessWidgets(self.grid_5)

            self.addUpdateCrownWidgets(self.grid_6)

            self.form = self.group_box_0
            return
