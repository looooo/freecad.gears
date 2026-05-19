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
from freecad import gui

import numpy as np

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
    QLineEdit
)

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP

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
        self.header_other_teeth = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Number of Teeth"
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
        self.tool_tip_preview = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Toggles between normal and preview mode"
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
        self.option_enabled = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Enabled"
        )
        self.option_disabled = QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Disabled"
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

    def addUpdateCrownWidgets(self, grid):
        '''Provides an update button'''

        self.button_apply = QPushButton(self.apply)
        self.button_apply.setToolTip(self.tool_tip_apply)
        self.button_apply.setEnabled(False)
        self.button_apply.clicked.connect(self.onButtonApplyCrown)
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

    def addOtherGearWidgets(self, grid):
        '''
        The number of teeth of the other gear influences the shape of
        this crown gear's teeth
        '''
        self.label_other_teeth = QLabel(self.header_other_teeth)
        grid.addWidget(self.label_other_teeth, 1, 0)

        self.ds_box_other_teeth = QDoubleSpinBox()
        self.ds_box_other_teeth.setMaximum(10000)
        self.ds_box_other_teeth.setValue(self.other_teeth)
        self.ds_box_other_teeth.valueChanged.connect(
            self.onDoubleSpinBoxOtherTeethChanged
        )
        grid.addWidget(self.ds_box_other_teeth, 1, 1)

    def addPreviewModeWidgets(self, grid):
        '''
        Toggles between normal and preview mode
        '''
        self.button_preview = QPushButton(self.option_enabled)
        self.button_preview.setToolTip(self.tool_tip_preview)
        self.button_preview.setEnabled(True)
        self.button_preview.clicked.connect(self.onButtonPreview)
        grid.addWidget(self.button_preview, 1, 0)

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

    def onDoubleSpinBoxOtherTeethChanged(self, value):
        '''Updates the number of teeth of a meshing gear'''
        self.other_teeth = value
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

    # Preview:
    def onButtonPreview(self, value):
        '''
        Toggles between enabled and disabled
        '''
        if self.button_preview.text() == self.option_enabled:
            self.button_preview.setText(self.option_disabled)
            self.preview_mode = False
        else:
            self.button_preview.setText(self.option_enabled)
            self.preview_mode = True
        self.button_apply.setEnabled(True)

        if self.auto_recompute:
            self.onButtonApplyBevel()

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

    def onButtonApplyCrown(self, value = None):
        '''
        Updates the object parameters with the task panel settings
        and runs a recompute
        '''
        self.obj.num_teeth = int(self.num_teeth)
        self.obj.module = self.module
        self.obj.other_teeth = int(self.other_teeth)
        self.obj.height = self.height
        self.obj.thickness = self.thickness
        self.obj.preview_mode = self.preview_mode

        app.ActiveDocument.recompute()
        self.button_apply.setEnabled(False)


    def accept(self):
        '''
        This is triggered by the panel's OK button.
        '''
        gui.Control.closeDialog()
        app.ActiveDocument.recompute()
        gui.ActiveDocument.resetEdit()

    def reject(self):
        '''
        This is triggered by the panel's Cancel button.
        '''
        gui.Control.closeDialog()
        app.ActiveDocument.recompute()
        gui.ActiveDocument.resetEdit()

class InvoluteGearTaskPanel(GearsBaseTaskPanel):
    """Control panel for Involute Gears"""

    def __init__(self, obj):

        self.obj = obj

        #obj.gear
        #obj.simple
        #obj.undercut
        self.num_teeth = obj.num_teeth
        self.module = obj.module
        #obj.shift
        #obj.pressure_angle
        self.helix_angle = obj.helix_angle
        self.height = obj.height
        #obj.clearance
        #obj.head
        #obj.numpoints
        self.double_helix = obj.double_helix
        #obj.backlash
        #obj.reversed_backlash
        #obj.properties_from_tool
        #obj.head_fillet
        #obj.root_fillet
        #obj.axle_hole
        #obj.axle_holesize
        #obj.offset_hole
        #obj.offset_holesize
        #obj.offset_holeoffset

        self.pitch_diameter = obj.pitch_diameter.Value
        self.auto_recompute = False

        self.translateTaskPanel()

        #- Add a QGroupBox container with a QGridLayout to group widgets
        self.group_box_0, self.grid_0 = self.groupBoxWithGrid()
        self.group_box_0.setWindowTitle(QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Involute Gear Parameters")
        )
        #- Add sub-boxes
        self.group_box_1, self.grid_1 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Size")
        )
        self.group_box_1.setStyleSheet("background-color:#dec")
        self.grid_0.addWidget(self.group_box_1, 0, 0)

        self.group_box_2, self.grid_2 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Helix Angle")
        )
        self.group_box_2.setStyleSheet("background-color:#def")
        self.grid_0.addWidget(self.group_box_2, 1, 0)

        self.group_box_3, self.grid_3 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Gear Width")
        )
        self.group_box_3.setStyleSheet("background-color:#fed")
        self.grid_0.addWidget(self.group_box_3, 2, 0)

        self.group_box_4, self.grid_4 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Update")
        )
        self.group_box_4.setStyleSheet("background-color:#ddd")
        self.grid_0.addWidget(self.group_box_4, 10, 0)

        #- Add some widgets to the grids
        self.addSizeWidgetsInvolute(self.grid_1)

        self.addHelixAngleWidgets(self.grid_2)

        self.addTransverseHightWidgets(self.grid_3)

        self.addUpdateWidgets(self.grid_4)

        self.form = self.group_box_0
        return

class InternalInvoluteGearTaskPanel(GearsBaseTaskPanel):
    """Control panel for Involute Gears"""

    def __init__(self, obj):

        self.obj = obj

        #obj.gear
        #obj.simple
        self.num_teeth = obj.num_teeth
        self.module = obj.module
        #obj.shift
        #obj.pressure_angle
        self.helix_angle = obj.helix_angle
        self.height = obj.height
        self.thickness = obj.thickness
        #obj.clearance
        #obj.head
        #obj.numpoints
        self.double_helix = obj.double_helix
        #obj.backlash
        #obj.reversed_backlash
        #obj.properties_from_tool
        #obj.head_fillet
        #obj.root_fillet

        self.pitch_diameter = obj.pitch_diameter.Value
        self.auto_recompute = False

        self.translateTaskPanel()

        #- Add a QGroupBox container with a QGridLayout to group widgets
        self.group_box_0, self.grid_0 = self.groupBoxWithGrid()
        self.group_box_0.setWindowTitle(QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Internal Involute Gear Parameters"
        ))
        #- Add sub-boxes
        self.group_box_1, self.grid_1 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Size")
        )
        self.group_box_1.setStyleSheet("background-color:#dec")
        self.grid_0.addWidget(self.group_box_1, 0, 0)

        self.group_box_2, self.grid_2 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Helix Angle")
        )
        self.group_box_2.setStyleSheet("background-color:#def")
        self.grid_0.addWidget(self.group_box_2, 1, 0)

        self.group_box_3, self.grid_3 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Gear Width")
        )
        self.group_box_3.setStyleSheet("background-color:#fed")
        self.grid_0.addWidget(self.group_box_3, 2, 0)

        self.group_box_4, self.grid_4 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Thickness")
        )
        self.group_box_4.setStyleSheet("background-color:#ffe")
        self.grid_0.addWidget(self.group_box_4, 3, 0)

        self.group_box_5, self.grid_5 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Update")
        )
        self.group_box_5.setStyleSheet("background-color:#ddd")
        self.grid_0.addWidget(self.group_box_5, 10, 0)

        #- Add some widgets to the grids
        self.addSizeWidgetsInvolute(self.grid_1)

        self.addHelixAngleWidgets(self.grid_2)

        self.addTransverseHightWidgets(self.grid_3)

        self.addThicknessWidgets(self.grid_4)

        self.addUpdateWidgets(self.grid_5)

        self.form = self.group_box_0
        return

class InvoluteGearRackTaskPanel(GearsBaseTaskPanel):
        """Control panel for Involute Gears"""

        def __init__(self, obj):

            self.obj = obj

            #obj.rack
            self.num_teeth = obj.num_teeth
            self.module = obj.module
            #obj.pressure_angle
            self.height = obj.height
            self.thickness = obj.thickness
            self.helix_angle = obj.helix_angle
            self.double_helix = obj.double_helix
            #obj.clearance
            #obj.head
            #obj.properties_from_tool
            #obj.add_endings
            #obj.simplified

            self.transverse_pitch = obj.transverse_pitch.Value  # uses existing logic
            self.auto_recompute = False

            self.translateTaskPanel()

            #- Add a QGroupBox container with a QGridLayout to group widgets
            self.group_box_0, self.grid_0 = self.groupBoxWithGrid()
            self.group_box_0.setWindowTitle(QT_TRANSLATE_NOOP(
                "Gear_TaskPanel",
                "Involute Gear Rack Parameters"
            ))
            #- Add sub-boxes
            self.group_box_1, self.grid_1 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Size")
            )
            self.group_box_1.setStyleSheet("background-color:#dec")
            self.grid_0.addWidget(self.group_box_1, 0, 0)

            self.group_box_2, self.grid_2 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Helix Angle")
            )
            self.group_box_2.setStyleSheet("background-color:#def")
            self.grid_0.addWidget(self.group_box_2, 1, 0)

            self.group_box_3, self.grid_3 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Gear Width")
            )
            self.group_box_3.setStyleSheet("background-color:#fed")
            self.grid_0.addWidget(self.group_box_3, 2, 0)

            self.group_box_4, self.grid_4 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Thickness")
            )
            self.group_box_4.setStyleSheet("background-color:#ffe")
            self.grid_0.addWidget(self.group_box_4, 3, 0)

            self.group_box_5, self.grid_5 = self.groupBoxWithGrid(
                QT_TRANSLATE_NOOP("Gear_TaskPanel", "Update")
            )
            self.group_box_5.setStyleSheet("background-color:#ddd")
            self.grid_0.addWidget(self.group_box_5, 10, 0)

            #- Add some widgets to the grids
            self.addSizeWidgetsInvoluteRack(self.grid_1)

            self.addHelixAngleWidgets(self.grid_2)

            self.addTransverseHightWidgets(self.grid_3)

            self.addThicknessWidgets(self.grid_4)

            self.addUpdateWidgets(self.grid_5)

            self.form = self.group_box_0
            return

class CycloidGearTaskPanel(GearsBaseTaskPanel):
    """Control panel for Cycloid Gears"""

    def __init__(self, obj):

        self.obj = obj

        #obj.gear = self.cycloid_tooth
        self.num_teeth = obj.num_teeth
        self.module = obj.module
        #obj.outer_diameter
        self.helix_angle = obj.helix_angle
        self.height = obj.height
        #obj.clearance
        #obj.numpoints
        #obj.backlash
        self.double_helix = obj.double_helix
        #obj.head
        #obj.head_fillet
        #obj.root_fillet

        self.pitch_diameter = obj.pitch_diameter.Value
        self.auto_recompute = False

        self.translateTaskPanel()

        #- Add a QGroupBox container with a QGridLayout to group widgets
        self.group_box_0, self.grid_0 = self.groupBoxWithGrid()
        self.group_box_0.setWindowTitle(QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Cycloid Gear Parameters"
        ))
        #- Add sub-boxes
        self.group_box_1, self.grid_1 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Size")
        )
        self.group_box_1.setStyleSheet("background-color:#dec")
        self.grid_0.addWidget(self.group_box_1, 0, 0)

        self.group_box_2, self.grid_2 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Helix Angle")
        )
        self.group_box_2.setStyleSheet("background-color:#def")
        self.grid_0.addWidget(self.group_box_2, 1, 0)

        self.group_box_3, self.grid_3 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Gear Width")
        )
        self.group_box_3.setStyleSheet("background-color:#fed")
        self.grid_0.addWidget(self.group_box_3, 2, 0)

        self.group_box_4, self.grid_4 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Update")
        )
        self.group_box_4.setStyleSheet("background-color:#ddd")
        self.grid_0.addWidget(self.group_box_4, 10, 0)

        #- Add some widgets to the grids
        self.addSizeWidgetsInvolute(self.grid_1)

        self.addHelixAngleWidgets(self.grid_2)

        self.addTransverseHightWidgets(self.grid_3)

        self.addUpdateWidgets(self.grid_4)

        self.form = self.group_box_0
        return

class CycloidGearRackTaskPanel(GearsBaseTaskPanel):
    """Control panel for Involute Gears"""

    def __init__(self, obj):

        self.obj = obj

        self.num_teeth = obj.num_teeth
        self.module = obj.module
        #obj.inner_diameter
        #obj.outer_diameter
        self.height = obj.height
        self.thickness = obj.thickness
        self.helix_angle = obj.helix_angle
        #obj.clearance
        #obj.head
        #obj.add_endings
        #obj.simplified
        #obj.numpoints

        self.transverse_pitch = obj.transverse_pitch.Value  # uses existing logic
        self.auto_recompute = False

        self.translateTaskPanel()

        #- Add a QGroupBox container with a QGridLayout to group widgets
        self.group_box_0, self.grid_0 = self.groupBoxWithGrid()
        self.group_box_0.setWindowTitle(QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Cycloid Gear Rack Parameters"
        ))
        #- Add sub-boxes
        self.group_box_1, self.grid_1 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Size")
        )
        self.group_box_1.setStyleSheet("background-color:#dec")
        self.grid_0.addWidget(self.group_box_1, 0, 0)

        self.group_box_2, self.grid_2 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Helix Angle")
        )
        self.group_box_2.setStyleSheet("background-color:#def")
        self.grid_0.addWidget(self.group_box_2, 1, 0)

        self.group_box_3, self.grid_3 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Gear Width")
        )
        self.group_box_3.setStyleSheet("background-color:#fed")
        self.grid_0.addWidget(self.group_box_3, 2, 0)

        self.group_box_4, self.grid_4 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Thickness")
        )
        self.group_box_4.setStyleSheet("background-color:#ffe")
        self.grid_0.addWidget(self.group_box_4, 3, 0)

        self.group_box_5, self.grid_5 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Update")
        )
        self.group_box_5.setStyleSheet("background-color:#ddd")
        self.grid_0.addWidget(self.group_box_5, 10, 0)

        #- Add some widgets to the grids
        self.addSizeWidgetsInvoluteRack(self.grid_1)

        self.addHelixAngleWidgets(self.grid_2)

        self.addTransverseHightWidgets(self.grid_3)

        self.addThicknessWidgets(self.grid_4)

        self.addUpdateWidgets(self.grid_5)

        self.form = self.group_box_0
        return

class BevelGearTaskPanel(GearsBaseTaskPanel):
    """Control panel for Involute Gears"""

    def __init__(self, obj):

        self.obj = obj
        #- Input values
        #obj.gear
        self.module = obj.module
        self.num_teeth = obj.num_teeth
        #obj.pressure_angle
        #obj.pitch_angle
        self.height = obj.height
        #obj.numpoints
        #obj.backlash
        #obj.clearance
        self.beta = obj.beta
        #obj.reset_origin
        #- Default values for computed properties
        self.pitch_diameter = obj.dw.Value
        self.auto_recompute = False

        self.translateTaskPanel()

        #- Add a QGroupBox container with a QGridLayout to group widgets
        self.group_box_0, self.grid_0 = self.groupBoxWithGrid()
        self.group_box_0.setWindowTitle(QT_TRANSLATE_NOOP(
            "Gear_TaskPanel",
            "Bevel Gear Parameters"
        ))
        #- Add sub-boxes
        self.group_box_1, self.grid_1 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Size")
        )
        self.group_box_1.setStyleSheet("background-color:#dec")
        self.grid_0.addWidget(self.group_box_1, 0, 0)

        self.group_box_2, self.grid_2 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Spiral Angle")
        )
        self.group_box_2.setStyleSheet("background-color:#def")
        self.grid_0.addWidget(self.group_box_2, 1, 0)

        self.group_box_3, self.grid_3 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Gear Width")
        )
        self.group_box_3.setStyleSheet("background-color:#fed")
        self.grid_0.addWidget(self.group_box_3, 2, 0)

        self.group_box_4, self.grid_4 = self.groupBoxWithGrid(
            QT_TRANSLATE_NOOP("Gear_TaskPanel", "Update")
        )
        self.group_box_4.setStyleSheet("background-color:#ddd")
        self.grid_0.addWidget(self.group_box_4, 10, 0)

        #- Add some widgets to the grids
        self.addSizeWidgetsBevel(self.grid_1)

        self.addBetaAngleWidgets(self.grid_2)

        self.addTransverseHightWidgets(self.grid_3)

        self.addUpdateBevelWidgets(self.grid_4)

        self.form = self.group_box_0
        return

class CrownGearTaskPanel(GearsBaseTaskPanel):
        """Control panel for Crown Gears"""

        def __init__(self, obj):

            self.obj = obj

            self.num_teeth = obj.num_teeth
            self.module = obj.module
            self.other_teeth = obj.other_teeth
            #obj.pressure_angle = "20. deg"
            self.height = obj.height
            self.thickness = obj.thickness
            #obj.num_profiles = 4
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
