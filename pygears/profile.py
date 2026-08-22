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

"""Full gear profile generation from single-tooth geometry.

Combines tooth geometry classes with rotational assembly to produce closed
point arrays representing complete gears or racks.
"""

import numpy as np
from .involute_tooth import InvoluteTooth, InvoluteRack
from .bevel_tooth import BevelTooth
from .cycloid_tooth import CycloidTooth
from ._functions import rotation, rotation3D


class _GearProfile(object):
    """Mixin that assembles a full gear profile from a single tooth."""

    rot3D = False

    def profile(self, num=10):
        """Build a closed gear profile by rotating one tooth around the origin.

        Args:
            num (int): Number of sample points per tooth segment (passed to
                ``points()``).

        Returns:
            numpy.ndarray: Closed profile as ``(N, 2)`` or ``(N, 3)`` array.
                The first and last row are identical.
        """
        tooth = self.points(num=num)
        tooth = [list(point) for wire in tooth for point in wire]
        n_teeth = self.num_teeth if hasattr(self, "num_teeth") else self.z
        if self.rot3D:
            rot = rotation3D(np.pi * 2 / n_teeth)
        else:
            rot = rotation(np.pi * 2 / n_teeth)
        profile = tooth
        for _ in range(n_teeth - 1):
            tooth = rot(tooth).tolist()
            profile = profile + tooth
        profile.append(profile[0])
        return np.array(profile)


class InvoluteProfile(InvoluteTooth, _GearProfile):
    """Closed 2D involute spur or helical gear profile."""


class CycloidProfile(CycloidTooth, _GearProfile):
    """Closed 2D cycloid gear profile."""


class BevelProfile(BevelTooth, _GearProfile):
    """Closed 3D bevel gear profile projected onto the z=1 plane."""

    rot3D = True


class InvoluteRackProfile(InvoluteRack):
    """Involute rack profile (all teeth in a single pass, no rotation)."""

    def profile(self):
        """Return the rack profile as a closed point array.

        Returns:
            numpy.ndarray: Closed profile as ``(N, 2)`` array. The first and
                last row are identical.
        """
        return self.points()
