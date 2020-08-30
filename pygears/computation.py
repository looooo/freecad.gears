# -*- coding: utf-8 -*-
# ***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import numpy as np
from scipy import optimize as opt


def compute_shifted_gears(m, alpha, t1, t2, x1, x2):
    """Summary

    Args:
        m (float): common module of both gears [length]
        alpha (float): pressure-angle [rad]
        t1 (int): number of teeth of gear1
        t2 (int): number of teeth of gear2
        x1 (float): relative profile-shift of gear1
        x2 (float): relative profile-shift of gear2

    Returns:
        (float, float): distance between gears [length], pressure angle of the assembly [rad]
    """
    def inv(x): return np.tan(x) - x
    inv_alpha_w = inv(alpha) + 2 * np.tan(alpha) * (x1 + x2) / (t1 + t2)

    def root_inv(x): return inv(x) - inv_alpha_w
    alpha_w = opt.fsolve(root_inv, 0.)
    dist = m * (t1 + t2) / 2 * np.cos(alpha) / np.cos(alpha_w)
    return dist, alpha_w
