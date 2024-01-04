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


# this file is only for backwards compatibility, and will be deleted in the future

from freecad import app

app.Console.PrintWarning(f"{__file__} is deprecated, just saving this file again should fix this warning")

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
from .basegear import ViewProviderGear, BaseGear
