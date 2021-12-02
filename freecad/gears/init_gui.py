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
        "CreateInternalInvoluteGear",
        "CreateInvoluteRack",
        "CreateCycloidGear",
        "CreateCycloidRack",
        "CreateBevelGear",
        "CreateCrownGear",
        "CreateWormGear",
        "CreateTimingGear",
        "CreateLanternGear",
        "CreateHypoCycloidGear",
        "CreateGearConnector"]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        from .commands import CreateCycloidGear, CreateInvoluteGear, CreateInternalInvoluteGear
        from .commands import CreateBevelGear, CreateInvoluteRack, CreateCrownGear
        from .commands import CreateWormGear, CreateTimingGear, CreateLanternGear
        from .commands import CreateHypoCycloidGear, CreateCycloidRack
        from .commands import CreateGearConnector

        self.appendToolbar("Gear", self.commands)
        self.appendMenu("Gear", self.commands)
        # Gui.addIconPath(App.getHomePath()+"Mod/gear/icons/")
        Gui.addCommand('CreateInvoluteGear', CreateInvoluteGear())
        Gui.addCommand('CreateInternalInvoluteGear', CreateInternalInvoluteGear())
        Gui.addCommand('CreateCycloidGear', CreateCycloidGear())
        Gui.addCommand('CreateCycloidRack', CreateCycloidRack())
        Gui.addCommand('CreateBevelGear', CreateBevelGear())
        Gui.addCommand('CreateInvoluteRack', CreateInvoluteRack())
        Gui.addCommand('CreateCrownGear', CreateCrownGear())
        Gui.addCommand('CreateWormGear', CreateWormGear())
        Gui.addCommand('CreateTimingGear', CreateTimingGear())
        Gui.addCommand('CreateLanternGear', CreateLanternGear())
        Gui.addCommand('CreateHypoCycloidGear', CreateHypoCycloidGear())
        Gui.addCommand('CreateGearConnector', CreateGearConnector())

    def Activated(self):
        pass

    def Deactivated(self):
        pass


Gui.addWorkbench(GearWorkbench())
