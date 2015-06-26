#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************


import os
from PySide import QtGui, QtCore

freecad_found = True

try:
    import FreeCADGui as Gui
    import Part
    import FreeCAD as App
except ImportError:
    freecad_found = False

if freecad_found:

    import freecad_gear as gear
    from freecad_gear.freecad.commands import (createInvoluteGear,
            createCycloidGear, createBevelGear, createInvoluteRack)


class gearToolBox(object):
    def __init__(self):
        mw = Gui.getMainWindow()     
        [
            self.involuteGearAction,
            self.involuteRackAction,
            self.bevelGearAction,
            self.cycloidGearAction,
            self.dropdown_action] = [None, None, None, None, None]
        self.defaultAction = createInvoluteGear
        self.add_gear_wb()
        mw.workbenchActivated.connect(self.add_gear_wb)
        timer = mw.findChild(QtCore.QTimer, "activityTimer")
        timer.connect(timer, QtCore.SIGNAL("timeout()"), self.checkDocument)



    def add_gear_wb(self, *args):
        print("Workbench_changed")
        try:
            wb = Gui.activeWorkbench()
        except Exception as e:
            return

        if "PartWorkbench" in str(wb):

            mainWindow = Gui.getMainWindow()

            # add the module to Freecad
            try:
                if Gui.gear.gear_toolbar:
                    Gui.gear.gear_toolbar.show()
            except:
                pass
            Gui.gear = gear.__class__("gear")
            print(type(gear))

            # create toolbar
            Gui.gear.gear_toolbar = mainWindow.addToolBar("Part: GearToolbar")
            Gui.gear.gear_toolbar.setObjectName("GearToolbar")

            this_path = os.path.dirname(os.path.realpath(__file__))



            self.dropdown = QtGui.QMenu("gear_menu", Gui.gear.gear_toolbar)

            # create commands
            icon = QtGui.QIcon(this_path + "/icons/involutegear.svg")
            self.involuteGearAction = QtGui.QAction(icon, "involute gear", self.dropdown)
            self.involuteGearAction.setObjectName("GearToolbar")
            self.involuteGearAction.triggered.connect(
                self.set_default_action(self.involuteGearAction, createInvoluteGear))

            icon = QtGui.QIcon(this_path + "/icons/involuterack.svg")
            self.involuteRackAction = QtGui.QAction(icon, "involute rack", self.dropdown)
            self.involuteRackAction.setObjectName("GearToolbar")            
            self.involuteRackAction.triggered.connect(
                self.set_default_action(self.involuteRackAction, createInvoluteRack))

            icon = QtGui.QIcon(this_path + "/icons/cycloidegear.svg")
            self.cycloidGearAction = QtGui.QAction(icon, "cycloid gear", self.dropdown)
            self.cycloidGearAction.setObjectName("GearToolbar")
            self.cycloidGearAction.triggered.connect(
                self.set_default_action(self.cycloidGearAction, createCycloidGear))

            icon = QtGui.QIcon(this_path + "/icons/bevelgear.svg")
            self.bevelGearAction = QtGui.QAction(icon, "bevel gear", self.dropdown)
            self.bevelGearAction.setObjectName("GearToolbar")
            self.bevelGearAction.triggered.connect(
                self.set_default_action(self.bevelGearAction, createBevelGear))


            temp1 = self.dropdown.addAction(self.involuteGearAction)
            temp2 = self.dropdown.addAction(self.involuteRackAction)
            temp3 = self.dropdown.addAction(self.cycloidGearAction)
            temp4 = self.dropdown.addAction(self.bevelGearAction)

            self.dropdown.setIcon(self.involuteGearAction.icon())
            temp5 = Gui.gear.gear_toolbar.addAction(self.dropdown.menuAction())
            self.checkDocument()

            self.defaultCommand = createInvoluteGear
            self.dropdown.menuAction().triggered.connect(self.defaultCommand)

    def set_default_action(self, action, command):
        def cb(*args):
            self.dropdown.setIcon(action.icon())
            self.defaultCommand = command
            command()
        return cb

    def checkDocument(self, *args):
        enable = False
        if App.ActiveDocument:
            enable = True
        for action in [self.involuteGearAction, self.involuteRackAction,
                       self.bevelGearAction, self.cycloidGearAction, self.dropdown.menuAction()]:
            if action:
                action.setEnabled(enable)

if freecad_found:
    a = gearToolBox()