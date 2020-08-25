# -*- coding: utf-8 -*-
# ***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import os
import FreeCADGui as Gui
import FreeCAD as App
__dirname__ = os.path.dirname(__file__)

try:
    from FreeCADGui import Workbench
except ImportError as e:
    App.Console.PrintWarning(
        "you are using the GearWorkbench with an old version of FreeCAD (<0.16)")
    App.Console.PrintWarning(
        "the class Workbench is loaded, although not imported: magic")


class GearWorkbench(Workbench):
    """glider workbench"""
    MenuText = "Gear"
    ToolTip = "Gear Workbench"
    Icon = os.path.join(__dirname__,  'icons', 'gearworkbench.svg')
    commands = [
        "CreateInvoluteGear",
        "CreateInvoluteRack",
        "CreateCycloideGear",
        "CreateBevelGear",
        "CreateCrownGear",
        "CreateWormGear",
        "CreateTimingGear",
        "CreateLanternGear",
        "CreateHypoCycloidGear"]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        from .commands import CreateCycloideGear, CreateInvoluteGear
        from .commands import CreateBevelGear, CreateInvoluteRack, CreateCrownGear
        from .commands import CreateWormGear, CreateTimingGear, CreateLanternGear
        from .commands import CreateHypoCycloidGear

        self.appendToolbar("Gear", self.commands)
        self.appendMenu("Gear", self.commands)
        # Gui.addIconPath(App.getHomePath()+"Mod/gear/icons/")
        Gui.addCommand('CreateInvoluteGear', CreateInvoluteGear())
        Gui.addCommand('CreateCycloideGear', CreateCycloideGear())
        Gui.addCommand('CreateBevelGear', CreateBevelGear())
        Gui.addCommand('CreateInvoluteRack', CreateInvoluteRack())
        Gui.addCommand('CreateCrownGear', CreateCrownGear())
        Gui.addCommand('CreateWormGear', CreateWormGear())
        Gui.addCommand('CreateTimingGear', CreateTimingGear())
        Gui.addCommand('CreateLanternGear', CreateLanternGear())
        Gui.addCommand('CreateHypoCycloidGear', CreateHypoCycloidGear())

    def Activated(self):
        pass

    def Deactivated(self):
        pass


Gui.addWorkbench(GearWorkbench())
