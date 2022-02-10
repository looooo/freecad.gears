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
import FreeCAD
import FreeCADGui as Gui
from .features import ViewProviderGear, InvoluteGear, InternalInvoluteGear, InvoluteGearRack, CycloidGearRack
from .features import CycloidGear, BevelGear, CrownGear, WormGear, TimingGear, LanternGear, HypoCycloidGear, BaseGear
from .connector import GearConnector, ViewProviderGearConnector


class BaseCommand(object):
    NAME = ""
    GEAR_FUNCTION = None
    ICONDIR = os.path.join(os.path.dirname(__file__), "icons")

    def __init__(self):
        pass

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        Gui.doCommandGui("import freecad.gears.commands")
        Gui.doCommandGui("freecad.gears.commands.{}.create()".format(
            self.__class__.__name__))
        FreeCAD.ActiveDocument.recompute()
        Gui.SendMsgToActiveView("ViewFit")

    @classmethod
    def create(cls):
        if FreeCAD.GuiUp:
            # borrowed from threaded profiles
            # puts the gear into an active container
            body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
            part = Gui.ActiveDocument.ActiveView.getActiveObject("part")

            if body:
                obj = FreeCAD.ActiveDocument.addObject("PartDesign::FeaturePython", cls.NAME)
            else:
                obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", cls.NAME)
            ViewProviderGear(obj.ViewObject, cls.Pixmap)
            cls.GEAR_FUNCTION(obj)

            if body:
                body.addObject(obj)
            elif part:
                part.Group += [obj]
        else:
            obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", cls.NAME)
            cls.GEAR_FUNCTION(obj)
        return obj

    def GetResources(self):
        return {'Pixmap': self.Pixmap,
                'MenuText': self.MenuText,
                'ToolTip': self.ToolTip}


class CreateInvoluteGear(BaseCommand):
    NAME = "InvoluteGear"
    GEAR_FUNCTION = InvoluteGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'involutegear.svg')
    MenuText = 'Involute Gear'
    ToolTip = 'Create an external involute gear'


class CreateInternalInvoluteGear(BaseCommand):
    NAME = "InternalInvoluteGear"
    GEAR_FUNCTION = InternalInvoluteGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'internalinvolutegear.svg')
    MenuText = 'Internal Involute Gear'
    ToolTip = 'Create an internal involute gear'


class CreateInvoluteRack(BaseCommand):
    NAME = "InvoluteRack"
    GEAR_FUNCTION = InvoluteGearRack
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'involuterack.svg')
    MenuText = 'Involute Rack'
    ToolTip = 'Create an Involute rack'

class CreateCycloidRack(BaseCommand):
    NAME = "CycloidRack"
    GEAR_FUNCTION = CycloidGearRack
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'cycloidrack.svg')
    MenuText = 'Cycloid Rack'
    ToolTip = 'Create an Cycloid rack'


class CreateCrownGear(BaseCommand):
    NAME = "CrownGear"
    GEAR_FUNCTION = CrownGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'crowngear.svg')
    MenuText = 'Crown Gear'
    ToolTip = 'Create a Crown gear'


class CreateCycloidGear(BaseCommand):
    NAME = "CycloidGear"
    GEAR_FUNCTION = CycloidGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'cycloidgear.svg')
    MenuText = 'Cycloid Gear'
    ToolTip = 'Create a Cycloid gear'


class CreateBevelGear(BaseCommand):
    NAME = "BevelGear"
    GEAR_FUNCTION = BevelGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'bevelgear.svg')
    MenuText = 'Bevel Gear'
    ToolTip = 'Create a Bevel gear'

class CreateHypoCycloidGear(BaseCommand):
    NAME = "HypocycloidGear"
    GEAR_FUNCTION = HypoCycloidGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'hypocycloidgear.svg')
    MenuText = 'HypoCycloid Gear'
    ToolTip = 'Create a HypoCycloid gear with its pins'


class CreateWormGear(BaseCommand):
    NAME = "WormGear"
    GEAR_FUNCTION = WormGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'wormgear.svg')
    MenuText = 'Worm Gear'
    ToolTip = 'Create a Worm gear'


class CreateTimingGear(BaseCommand):
    NAME = "TimingGear"
    GEAR_FUNCTION = TimingGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'timinggear.svg')
    MenuText = 'Timing Gear'
    ToolTip = 'Create a Timing gear'

class CreateLanternGear(BaseCommand):
    NAME = "LanternGear"
    GEAR_FUNCTION = LanternGear
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'lanterngear.svg')
    MenuText = 'Lantern Gear'
    ToolTip = 'Create a Lantern gear'

class CreateGearConnector(BaseCommand):
    NAME = "GearConnector"
    GEAR_FUNCTION = GearConnector
    Pixmap = os.path.join(BaseCommand.ICONDIR, 'gearconnector.svg')
    MenuText = 'Combine two gears'
    ToolTip = 'Combine two gears'

    def Activated(self):
        gear1 = Gui.Selection.getSelection()[0]
        assert isinstance(gear1.Proxy, BaseGear)

        gear2 = Gui.Selection.getSelection()[1]
        assert isinstance(gear2.Proxy, BaseGear)

        # check if selected objects are beams

        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", self.NAME)
        GearConnector(obj, gear1, gear2)
        ViewProviderGearConnector(obj.ViewObject)

        FreeCAD.ActiveDocument.recompute()
        return obj
