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
    def inv(x): 
        return np.tan(x) - x

    inv_alpha_w = inv(alpha) + 2 * np.tan(alpha) * (x1 + x2) / (t1 + t2)

    def root_inv(x):
        return inv(x) - inv_alpha_w

    def d_root_inv(x):
        return 1. / np.cos(x) - 1

    alpha_w = find_root(alpha, root_inv, d_root_inv)
    dist = m * (t1 + t2) / 2 * np.cos(alpha) / np.cos(alpha_w)
    return dist, alpha_w


def find_root(x0, f, df, epsilon=2e-10, max_iter=100):
    x_n = x0
    for i in range(max_iter):
        f_xn = f(x_n)
        if abs(f_xn) < epsilon:
            return x_n
        else:
            df_xn = df(x_n)
            if df_xn == 0:
                return None
            else:
                x_n = x_n - f_xn / df_xn / 2  # adding (/ 2) to avoid oscillation
    return None