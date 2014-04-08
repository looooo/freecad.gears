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
import FreeCAD
import gear_rc


class gearWorkbench(Workbench):
    """glider workbench"""
    MenuText = "gear"
    ToolTip = "gear workbench"
    Icon = "gearworkbench.svg"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):

        from gearfunc import CreateCycloideGear, CreateInvoluteGear, CreateBevelGear

        self.appendToolbar("Gear", ["CreateInvoluteGear", "CreateCycloideGear", "CreateBevelGear"])
        self.appendMenu("Gear", ["CreateInvoluteGear", "CreateCycloideGear","CreateBevelGear"])
        Gui.addIconPath(FreeCAD.getHomePath()+"Mod/gear/icons/")
        Gui.addCommand('CreateInvoluteGear', CreateInvoluteGear())
        Gui.addCommand('CreateCycloideGear', CreateCycloideGear())
        Gui.addCommand('CreateBevelGear', CreateBevelGear())

    def Activated(self):
        pass


    def Deactivated(self):
        pass

Gui.addWorkbench(gearWorkbench())
