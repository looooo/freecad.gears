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
from freecad import app
from freecad import gui

from .basegear import ViewProviderGear, BaseGear

from .timinggear_t import TimingGearT
from .involutegear import InvoluteGear
from .internalinvolutegear import InternalInvoluteGear
from .involutegearrack import InvoluteGearRack
from .cycloidgearrack import CycloidGearRack
from .crowngear import CrownGear
from .cycloidgear import CycloidGear
from .bevelgear import BevelGear
from .wormgear import WormGear
from .timinggear import TimingGear
from .lanterngear import LanternGear
from .hypocycloidgear import HypoCycloidGear


from .connector import GearConnector, ViewProviderGearConnector

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP


class BaseCommand(object):
    NAME = ""
    GEAR_FUNCTION = None
    ICONDIR = os.path.join(os.path.dirname(__file__), "icons")

    def __init__(self):
        pass

    def IsActive(self):
        if app.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        gui.doCommandGui("import freecad.gears.commands")
        gui.doCommandGui(
            "freecad.gears.commands.{}.create()".format(self.__class__.__name__)
        )
        app.ActiveDocument.recompute()
        gui.SendMsgToActiveView("ViewFit")

    @classmethod
    def create(cls):
        if app.GuiUp:
            # borrowed from threaded profiles
            # puts the gear into an active container
            body = gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
            part = gui.ActiveDocument.ActiveView.getActiveObject("part")

            if body:
                obj = app.ActiveDocument.addObject(
                    "PartDesign::FeaturePython", cls.NAME
                )
            else:
                obj = app.ActiveDocument.addObject("Part::FeaturePython", cls.NAME)
            ViewProviderGear(obj.ViewObject, cls.Pixmap)
            cls.GEAR_FUNCTION(obj)

            if body:
                body.addObject(obj)
            elif part:
                part.Group += [obj]
        else:
            obj = app.ActiveDocument.addObject("Part::FeaturePython", cls.NAME)
            cls.GEAR_FUNCTION(obj)
        return obj

    def GetResources(self):
        return {
            "Pixmap": self.Pixmap,
            "MenuText": self.MenuText,
            "ToolTip": self.ToolTip,
        }


class CreateInvoluteGear(BaseCommand):
    NAME = "InvoluteGear"
    GEAR_FUNCTION = InvoluteGear
    Pixmap = "FCGear_InvoluteGear"
    MenuText = QT_TRANSLATE_NOOP("FCGear_InvoluteGear", "Involute Gear")
    ToolTip = QT_TRANSLATE_NOOP(
        "FCGear_InvoluteGear", "Create an external involute gear"
    )


class CreateInternalInvoluteGear(BaseCommand):
    NAME = "InternalInvoluteGear"
    GEAR_FUNCTION = InternalInvoluteGear
    Pixmap = "FCGear_InternalInvoluteGear"
    MenuText = QT_TRANSLATE_NOOP(
        "FCGear_InternalInvoluteGear", "Internal Involute Gear"
    )
    ToolTip = QT_TRANSLATE_NOOP(
        "FCGear_InternalInvoluteGear", "Create an internal involute gear"
    )


class CreateInvoluteRack(BaseCommand):
    NAME = "InvoluteRack"
    GEAR_FUNCTION = InvoluteGearRack
    Pixmap = "FCGear_InvoluteRack"
    MenuText = QT_TRANSLATE_NOOP("FCGear_InvoluteRack", "Involute Rack")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_InvoluteRack", "Create an Involute rack")


class CreateCycloidRack(BaseCommand):
    NAME = "CycloidRack"
    GEAR_FUNCTION = CycloidGearRack
    Pixmap = "FCGear_CycloidRack"
    MenuText = QT_TRANSLATE_NOOP("FCGear_CycloidRack", "Cycloid Rack")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_CycloidRack", "Create an Cycloid rack")


class CreateCrownGear(BaseCommand):
    NAME = "CrownGear"
    GEAR_FUNCTION = CrownGear
    Pixmap = "FCGear_CrownGear"
    MenuText = QT_TRANSLATE_NOOP("FCGear_CrownGear", "Crown Gear")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_CrownGear", "Create a Crown gear")


class CreateCycloidGear(BaseCommand):
    NAME = "CycloidGear"
    GEAR_FUNCTION = CycloidGear
    Pixmap = "FCGear_CycloidGear"
    MenuText = QT_TRANSLATE_NOOP("FCGear_CycloidGear", "Cycloid Gear")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_CycloidGear", "Create a Cycloid gear")


class CreateBevelGear(BaseCommand):
    NAME = "BevelGear"
    GEAR_FUNCTION = BevelGear
    Pixmap = "FCGear_BevelGear"
    MenuText = QT_TRANSLATE_NOOP("FCGear_BevelGear", "Bevel Gear")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_BevelGear", "Create a Bevel gear")


class CreateHypoCycloidGear(BaseCommand):
    NAME = "HypocycloidGear"
    GEAR_FUNCTION = HypoCycloidGear
    Pixmap = "FCGear_HypoCycloidGear"
    MenuText = QT_TRANSLATE_NOOP("FCGear_HypoCycloidGear", "HypoCycloid Gear")
    ToolTip = QT_TRANSLATE_NOOP(
        "FCGear_HypoCycloidGear", "Create a HypoCycloid gear with its pins"
    )


class CreateWormGear(BaseCommand):
    NAME = "WormGear"
    GEAR_FUNCTION = WormGear
    Pixmap = "FCGear_WormGear"
    MenuText = QT_TRANSLATE_NOOP("FCGear_WormGear", "Worm Gear")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_WormGear", "Create a Worm gear")


class CreateTimingGearT(BaseCommand):
    NAME = "TimingGearT"
    GEAR_FUNCTION = TimingGearT
    Pixmap = "FCGear_TimingGearT"
    MenuText = QT_TRANSLATE_NOOP("FCGear_TimingGearT", "Timing Gear T-shape")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_TimingGearT", "Create a Timing gear T-shape")


class CreateTimingGear(BaseCommand):
    NAME = "TimingGear"
    GEAR_FUNCTION = TimingGear
    Pixmap = "FCGear_TimingGear"
    MenuText = QT_TRANSLATE_NOOP("FCGear_TimingGear", "Timing Gear")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_TimingGear", "Create a Timing gear")


class CreateLanternGear(BaseCommand):
    NAME = "LanternGear"
    GEAR_FUNCTION = LanternGear
    Pixmap = "FCGear_LanternGear"
    MenuText = QT_TRANSLATE_NOOP("FCGear_LanternGear", "Lantern Gear")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_LanternGear", "Create a Lantern gear")


class CreateGearConnector(BaseCommand):
    NAME = "GearConnector"
    GEAR_FUNCTION = GearConnector
    Pixmap = "FCGear_GearConnector"
    MenuText = QT_TRANSLATE_NOOP("FCGear_GearConnector", "Combine two gears")
    ToolTip = QT_TRANSLATE_NOOP("FCGear_GearConnector", "Combine two gears")

    def Activated(self):
        try:
            selection = gui.Selection.getSelection()

            if len(selection) != 2:
                raise ValueError(
                    app.Qt.translate("Log", "Please select two gear objects.")
                )

            for obj in selection:
                if not isinstance(obj.Proxy, BaseGear):
                    raise TypeError(
                        app.Qt.translate("Log", "Selected object is not a gear.")
                    )

            obj = app.ActiveDocument.addObject("Part::FeaturePython", self.NAME)
            GearConnector(obj, selection[0], selection[1])
            ViewProviderGearConnector(obj.ViewObject)

            app.ActiveDocument.recompute()
            return obj
        except Exception as e:
            app.Console.PrintError(f"Error: {str(e)}\n")
            return None
