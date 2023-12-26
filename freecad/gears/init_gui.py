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
import FreeCADGui as Gui
import FreeCAD as App

__dirname__ = os.path.dirname(__file__)

try:
    from FreeCADGui import Workbench
except ImportError as e:
    App.Console.PrintWarning(
        "you are using the GearWorkbench with an old version of FreeCAD (<0.16)"
    )
    App.Console.PrintWarning(
        "the class Workbench is loaded, although not imported: magic"
    )


if sys.version_info[0] == 3 and sys.version_info[1] >= 11:
    # only works with 0.21.2 and above

    FC_MAJOR_VER_REQUIRED = 0
    FC_MINOR_VER_REQUIRED = 21
    FC_PATCH_VER_REQUIRED = 2
    FC_COMMIT_REQUIRED = 33772

    # Check FreeCAD version
    App.Console.PrintLog("Checking FreeCAD version\n")
    ver = App.Version()
    major_ver = int(ver[0])
    minor_vers = ver[1].split(".")
    minor_ver = int(minor_vers[0])
    if minor_vers[1:] and minor_vers[1]:
        patch_ver = int(minor_vers[1])
    else:
        patch_ver = 0
    gitver = ver[2].split()
    if gitver:
        gitver = gitver[0]
    if gitver and gitver != "Unknown":
        gitver = int(gitver)
    else:
        # If we don't have the git version, assume it's OK.
        gitver = FC_COMMIT_REQUIRED

    if major_ver < FC_MAJOR_VER_REQUIRED or (
        major_ver == FC_MAJOR_VER_REQUIRED
        and (
            minor_ver < FC_MINOR_VER_REQUIRED
            or (
                minor_ver == FC_MINOR_VER_REQUIRED
                and (
                    patch_ver < FC_PATCH_VER_REQUIRED
                    or (
                        patch_ver == FC_PATCH_VER_REQUIRED
                        and gitver < FC_COMMIT_REQUIRED
                    )
                )
            )
        )
    ):
        App.Console.PrintWarning(
            "FreeCAD version (currently {}.{}.{} ({})) must be at least {}.{}.{} ({}) in order to work with Python 3.11 and above\n".format(
                int(ver[0]),
                minor_ver,
                patch_ver,
                gitver,
                FC_MAJOR_VER_REQUIRED,
                FC_MINOR_VER_REQUIRED,
                FC_PATCH_VER_REQUIRED,
                FC_COMMIT_REQUIRED,
            )
        )

class GearWorkbench(Workbench):
    """A freecad workbench aiming at gear design"""

    MenuText = "Gear"
    ToolTip = "Gear Workbench"
    Icon = os.path.join(__dirname__, "icons", "gearworkbench.svg")
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
        "CreateGearConnector",
    ]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        from .commands import (
            CreateCycloidGear,
            CreateInvoluteGear,
            CreateInternalInvoluteGear,
        )
        from .commands import CreateBevelGear, CreateInvoluteRack, CreateCrownGear
        from .commands import CreateWormGear, CreateTimingGear, CreateLanternGear
        from .commands import CreateHypoCycloidGear, CreateCycloidRack
        from .commands import CreateGearConnector

        self.appendToolbar("Gear", self.commands)
        self.appendMenu("Gear", self.commands)
        # Gui.addIconPath(App.getHomePath()+"Mod/gear/icons/")
        Gui.addCommand("CreateInvoluteGear", CreateInvoluteGear())
        Gui.addCommand("CreateInternalInvoluteGear", CreateInternalInvoluteGear())
        Gui.addCommand("CreateCycloidGear", CreateCycloidGear())
        Gui.addCommand("CreateCycloidRack", CreateCycloidRack())
        Gui.addCommand("CreateBevelGear", CreateBevelGear())
        Gui.addCommand("CreateInvoluteRack", CreateInvoluteRack())
        Gui.addCommand("CreateCrownGear", CreateCrownGear())
        Gui.addCommand("CreateWormGear", CreateWormGear())
        Gui.addCommand("CreateTimingGear", CreateTimingGear())
        Gui.addCommand("CreateLanternGear", CreateLanternGear())
        Gui.addCommand("CreateHypoCycloidGear", CreateHypoCycloidGear())
        Gui.addCommand("CreateGearConnector", CreateGearConnector())

    def Activated(self):
        pass

    def Deactivated(self):
        pass


Gui.addWorkbench(GearWorkbench())
