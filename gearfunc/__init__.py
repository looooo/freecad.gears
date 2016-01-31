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


import FreeCAD
import FreeCADGui as Gui
from ._Classes import *


class CreateInvoluteGear():
    """create an involute gear"""
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': 'involutegear.svg', 'MenuText': 'involute gear', 'ToolTip': 'involute gear'}

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "InvoluteGear")
        involute_gear(a)
        ViewProviderGear(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        Gui.SendMsgToActiveView("ViewFit")


class CreateInvoluteRack():
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': 'involuterack.svg', 'MenuText': 'involute rack', 'ToolTip': 'involute rack'}

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "InvoluteRack")
        involute_gear_rack(a)
        ViewProviderGear(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        Gui.SendMsgToActiveView("ViewFit")


class CreateCycloideGear():
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': 'cycloidegear.svg', 'MenuText': 'cycloide gear', 'ToolTip': 'cycloide gear'}

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "CycloideGear")
        cycloide_gear(a)
        ViewProviderGear(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        Gui.SendMsgToActiveView("ViewFit")

class CreateBevelGear():
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': 'bevelgear.svg', 'MenuText': 'bevel gear', 'ToolTip': 'bevel gear'}

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "BevelGear")
        bevel_gear(a)
        ViewProviderGear(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        Gui.SendMsgToActiveView("ViewFit")