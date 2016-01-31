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

import FreeCADGui as Gui
import FreeCAD as App
import gear_rc
import gearfunc

try:
    from FreeCADGui import Workbench
except ImportError as e:
    App.Console.Warning("you are using the GearWorkbench with an old version of FreeCAD (<0.16)")
    App.Console.Warning("the class Workbench is loaded, allthough not imported: magic")

class gearWorkbench(Workbench):
    """glider workbench"""
    MenuText = "gear"
    ToolTip = "gear workbench"
    Icon = "gearworkbench.svg"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):

        from gearfunc import CreateCycloideGear, CreateInvoluteGear, CreateBevelGear, CreateInvoluteRack

        self.appendToolbar("Gear", ["CreateInvoluteGear", "CreateInvoluteRack", "CreateCycloideGear", "CreateBevelGear"])
        self.appendMenu("Gear", ["CreateInvoluteGear", "CreateInvoluteRack", "CreateCycloideGear","CreateBevelGear"])
        Gui.addIconPath(App.getHomePath()+"Mod/gear/icons/")
        Gui.addCommand('CreateInvoluteGear', CreateInvoluteGear())
        Gui.addCommand('CreateCycloideGear', CreateCycloideGear())
        Gui.addCommand('CreateBevelGear', CreateBevelGear())
        Gui.addCommand('CreateInvoluteRack', CreateInvoluteRack())

    def Activated(self):
        pass


    def Deactivated(self):
        pass

Gui.addWorkbench(gearWorkbench())
