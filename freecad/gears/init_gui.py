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
from freecad import gui

__dirname__ = os.path.dirname(__file__)


if sys.version_info[0] == 3 and sys.version_info[1] >= 11:
    # only works with 0.21.2 and above

    FC_MAJOR_VER_REQUIRED = 0
    FC_MINOR_VER_REQUIRED = 21
    FC_PATCH_VER_REQUIRED = 2
    FC_COMMIT_REQUIRED = 33772

    # Check FreeCAD version
    app.Console.PrintLog("Checking FreeCAD version\n")
    ver = app.Version()
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
        app.Console.PrintWarning(
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


class GearWorkbench(gui.Workbench):
    """A freecad workbench aiming at gear design"""

    MenuText = "Gear"
    ToolTip = "Gear Workbench"
    Icon = os.path.join(__dirname__, "icons", "gearworkbench.svg")
    commands = [
        "FCGear_InvoluteGear",
        "FCGear_InternalInvoluteGear",
        "FCGear_InvoluteRack",
        "FCGear_CycloidGear",
        "FCGear_CycloidRack",
        "FCGear_BevelGear",
        "FCGear_CrownGear",
        "FCGear_WormGear",
        "FCGear_TimingGearT",
        "FCGear_TimingGear",
        "FCGear_LanternGear",
        "FCGear_HypoCycloidGear",
        "FCGear_GearConnector",
    ]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        # Add translations path
        gui.addLanguagePath(os.path.join(os.path.dirname(__file__), "translations"))
        gui.updateLocale()

        from .commands import (
            CreateCycloidGear,
            CreateInvoluteGear,
            CreateInternalInvoluteGear,
            CreateBevelGear,
            CreateInvoluteRack,
            CreateCrownGear,
            CreateWormGear,
            CreateTimingGearT,
            CreateTimingGear,
            CreateLanternGear,
            CreateHypoCycloidGear,
            CreateCycloidRack,
            CreateGearConnector,
        )

        self.appendToolbar("Gear", self.commands)
        self.appendMenu("Gear", self.commands)
        gui.addCommand("FCGear_InvoluteGear", CreateInvoluteGear())
        gui.addCommand("FCGear_InternalInvoluteGear", CreateInternalInvoluteGear())
        gui.addCommand("FCGear_CycloidGear", CreateCycloidGear())
        gui.addCommand("FCGear_CycloidRack", CreateCycloidRack())
        gui.addCommand("FCGear_BevelGear", CreateBevelGear())
        gui.addCommand("FCGear_InvoluteRack", CreateInvoluteRack())
        gui.addCommand("FCGear_CrownGear", CreateCrownGear())
        gui.addCommand("FCGear_WormGear", CreateWormGear())
        gui.addCommand("FCGear_TimingGearT", CreateTimingGearT())
        gui.addCommand("FCGear_TimingGear", CreateTimingGear())
        gui.addCommand("FCGear_LanternGear", CreateLanternGear())
        gui.addCommand("FCGear_HypoCycloidGear", CreateHypoCycloidGear())
        gui.addCommand("FCGear_GearConnector", CreateGearConnector())

    def Activated(self):
        pass

    def Deactivated(self):
        pass


gui.addWorkbench(GearWorkbench())
