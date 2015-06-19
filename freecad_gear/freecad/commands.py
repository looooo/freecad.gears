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

import FreeCAD as App
import FreeCADGui as Gui
from freecad_gear.gearfunc._Classes import involute_gear, cycloide_gear, bevel_gear, involute_gear_rack


def createInvoluteGear(*args):
    a = App.ActiveDocument.addObject("Part::FeaturePython", "involute_gear")
    involute_gear(a)
    a.ViewObject.Proxy = 0.
    App.ActiveDocument.recompute()
    Gui.SendMsgToActiveView("ViewFit")

def createInvoluteRack(*args):
    a = App.ActiveDocument.addObject("Part::FeaturePython", "involute_gear")
    involute_gear_rack(a)
    a.ViewObject.Proxy = 0.
    App.ActiveDocument.recompute()
    Gui.SendMsgToActiveView("ViewFit")

def createBevelGear(*args):
    a = App.ActiveDocument.addObject("Part::FeaturePython", "bevel_gear")
    bevel_gear(a)
    a.ViewObject.Proxy = 0.
    App.ActiveDocument.recompute()
    Gui.SendMsgToActiveView("ViewFit")

def createCycloidGear(*args):
    a = App.ActiveDocument.addObject("Part::FeaturePython", "cycloide_gear")
    cycloide_gear(a)
    a.ViewObject.Proxy = 0.
    App.ActiveDocument.recompute()
    Gui.SendMsgToActiveView("ViewFit")
