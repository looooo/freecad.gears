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


import numpy as np
from .involute_tooth import InvoluteTooth, InvoluteRack
from .bevel_tooth import BevelTooth
from .cycloid_tooth import CycloidTooth
from ._functions import rotation, rotation3D


class _GearProfile(object):
    rot3D = False

    def profile(self, num=10):
        tooth = self.points(num=num)
        tooth = [list(point) for wire in tooth for point in wire]
        n_teeth = self.num_teeth if hasattr(self, "num_teeth") else self.z
        if self.rot3D:
            rot = rotation3D(np.pi * 2 / n_teeth)
        else:
            rot = rotation(np.pi * 2 / n_teeth)
        profile = tooth
        for i in range(n_teeth - 1):
            tooth = rot(tooth).tolist()
            profile = profile + tooth
        profile.append(profile[0])
        return np.array(profile)


class InvoluteProfile(InvoluteTooth, _GearProfile):
    pass


class CycloidProfile(CycloidTooth, _GearProfile):
    pass


class BevelProfile(BevelTooth, _GearProfile):
    rot3D = True


class InvoluteRackProfile(InvoluteRack):
    def profile(self):
        return self.points()
