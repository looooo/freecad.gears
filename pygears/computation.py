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

"""Gear-pair computation helpers (center distance, operating pressure angle)."""

import numpy as np


def compute_shifted_gears(m, alpha, t1, t2, x1, x2):
    """Compute center distance and operating pressure angle for a gear pair.

    Args:
        m (float): Common module of both gears [length].
        alpha (float): Pressure angle [rad].
        t1 (int): Number of teeth of gear 1.
        t2 (int): Number of teeth of gear 2.
        x1 (float): Relative profile shift of gear 1.
        x2 (float): Relative profile shift of gear 2.

    Returns:
        tuple: ``(dist, alpha_w)`` — center distance [length] and operating
            pressure angle [rad] of the assembly.
    """

    def inv(x):
        return np.tan(x) - x

    inv_alpha_w = inv(alpha) + 2 * np.tan(alpha) * (x1 + x2) / (t1 + t2)

    def root_inv(x):
        return inv(x) - inv_alpha_w

    def d_root_inv(x):
        return 1.0 / np.cos(x) - 1

    alpha_w = find_root(alpha, root_inv, d_root_inv)
    dist = m * (t1 + t2) / 2 * np.cos(alpha) / np.cos(alpha_w)
    return dist, alpha_w


def compute_shifted_internal_gears(m, alpha, z_ring, z_pinion, x_ring, x_pinion):
    """Compute center distance and operating pressure angle of an internal pair.

    Args:
        m (float): Common module of both gears [length].
        alpha (float): Pressure angle [rad].
        z_ring (int): Number of teeth of the internal (ring) gear.
        z_pinion (int): Number of teeth of the meshing external gear.
        x_ring (float): Profile shift coefficient of the ring gear.
        x_pinion (float): Profile shift coefficient of the external gear.

    Returns:
        tuple: ``(dist, alpha_w)`` — center distance [length] and operating
            pressure angle [rad].
    """

    def inv(x):
        return np.tan(x) - x

    delta_z = z_ring - z_pinion
    inv_alpha_w = inv(alpha) + 2 * np.tan(alpha) * (x_ring - x_pinion) / delta_z

    def root_inv(x):
        return inv(x) - inv_alpha_w

    def d_root_inv(x):
        return 1.0 / np.cos(x) - 1

    alpha_w = find_root(alpha, root_inv, d_root_inv)
    dist = m * delta_z / 2 * np.cos(alpha) / np.cos(alpha_w)
    return dist, alpha_w


def root_diameter(module, num_teeth, shift=0.0, clearance=0.25):
    """Return the root circle diameter of an external involute gear.

    Args:
        module (float): Module of the gear [length].
        num_teeth (int): Number of teeth.
        shift (float): Profile shift coefficient.
        clearance (float): Clearance between tooth tip and mating root.

    Returns:
        float: Root circle diameter [length].
    """
    return module * (num_teeth - 2.0 * (1.0 + clearance) + 2.0 * shift)


def planetary_orbit_angles(z_sun, z_ring, num_planets):
    """Return orbit angles [deg] at which a planet can mesh with sun and ring.

    A planet only meshes with both the sun and the ring when its orbit angle is
    a multiple of ``360 / (z_sun + z_ring)``. The ideal equally spaced angles
    are therefore snapped onto that grid. They coincide exactly when
    ``(z_sun + z_ring)`` is divisible by ``num_planets``.

    Args:
        z_sun (int): Number of teeth on the sun gear.
        z_ring (int): Number of teeth on the ring gear.
        num_planets (int): Number of planet gears.

    Returns:
        list[float]: One orbit angle per planet, in degrees.
    """
    positions = z_sun + z_ring
    step = 360.0 / positions
    angles = []
    used = set()
    for index in range(num_planets):
        slot = int(round(index * positions / num_planets)) % positions
        while slot in used:
            slot = (slot + 1) % positions
        used.add(slot)
        angles.append(slot * step)
    return angles


def planetary_phase_angles(
    z_sun, z_planet, z_ring, orbit_angles, carrier_angle=0.0
):
    """Return the rotation angles [deg] that make every gear pair mesh.

    Derived from the tooth phase conventions of the generated profiles: an
    external gear carries a tooth centred on its local +x axis, an internal
    gear a tooth space. Angles are exact for any carrier position, so the same
    formulas drive both the initial layout and the animation.

    Args:
        z_sun (int): Number of teeth on the sun gear.
        z_planet (int): Number of teeth on each planet gear.
        z_ring (int): Number of teeth on the ring gear.
        orbit_angles (list[float]): Planet orbit angles [deg] at carrier zero.
        carrier_angle (float): Rotation of the carrier [deg], ring held fixed.

    Returns:
        dict: ``ring_angle``, ``sun_angle``, ``carrier_angle``,
            ``planet_orbits`` and ``planet_angles`` (all in degrees).
    """
    ring_angle = 180.0 * (z_planet + 1) / z_ring
    sun_angle = carrier_angle * (z_sun + z_ring) / z_sun
    spin_per_orbit = 1.0 - z_ring / z_planet
    planet_orbits = [angle + carrier_angle for angle in orbit_angles]
    planet_angles = [
        orbit * spin_per_orbit + 180.0 * (z_planet + 1) / z_planet
        for orbit in planet_orbits
    ]
    return {
        "ring_angle": ring_angle,
        "sun_angle": sun_angle,
        "carrier_angle": carrier_angle,
        "planet_orbits": planet_orbits,
        "planet_angles": planet_angles,
    }


def compute_planetary_gears(
    module,
    alpha,
    z_sun,
    z_planet,
    num_planets=3,
    x_sun=0.0,
    x_planet=0.0,
    x_ring=0.0,
    head=0.0,
):
    """Compute dimensions and validate a planetary gear set.

    The fundamental meshing constraint is ``z_ring = z_sun + 2 * z_planet``.
    For ``num_planets`` equally spaced planet gears, ``(z_sun + z_ring)`` must
    be divisible by ``num_planets``, and adjacent planets must not interfere.

    Args:
        module (float): Normal module [length].
        alpha (float): Pressure angle [rad].
        z_sun (int): Number of teeth on the sun gear.
        z_planet (int): Number of teeth on each planet gear.
        num_planets (int): Number of planet gears (default 3).
        x_sun (float): Profile shift coefficient of the sun gear.
        x_planet (float): Profile shift coefficient of each planet gear.
        x_ring (float): Profile shift coefficient of the ring gear.
        head (float): Addendum coefficient used for clearance check.

    Returns:
        dict: Keys include ``z_ring``, ``sun_planet_distance``,
            ``planet_ring_distance``, ``orbit_angles``, ``ring_angle``,
            ``ratio_ring_fixed``, ``ratio_sun_fixed``, ``valid``, and
            ``messages``.
    """
    messages = []
    z_ring = z_sun + 2 * z_planet

    sun_planet_dist, _ = compute_shifted_gears(
        module, alpha, z_sun, z_planet, x_sun, x_planet
    )
    planet_ring_dist, _ = compute_shifted_internal_gears(
        module, alpha, z_ring, z_planet, x_ring, x_planet
    )

    valid = True

    if z_sun < 6:
        messages.append("Sun gear should have at least 6 teeth.")
        valid = False
    if z_planet < 6:
        messages.append("Planet gear should have at least 6 teeth.")
        valid = False
    if z_ring < z_sun + 6:
        messages.append("Ring gear has too few teeth for this configuration.")
        valid = False
    if num_planets < 1:
        messages.append("At least one planet gear is required.")
        valid = False

    spacing_sum = z_sun + z_ring
    if num_planets > 0 and spacing_sum % num_planets != 0:
        messages.append(
            f"Assembly condition not met: (z_sun + z_ring) = {spacing_sum} "
            f"is not divisible by num_planets = {num_planets}."
        )
        valid = False

    orbit_angles = (
        planetary_orbit_angles(z_sun, z_ring, num_planets)
        if num_planets > 0
        else []
    )

    planet_tip_radius = module * (z_planet / 2.0 + 1.0 + head + x_planet)
    if num_planets > 1 and sun_planet_dist > 0:
        gaps = [
            (b - a) % 360.0
            for a, b in zip(orbit_angles, orbit_angles[1:] + orbit_angles[:1])
        ]
        min_gap = min(gaps)
        clearance = 2.0 * sun_planet_dist * np.sin(np.deg2rad(min_gap) / 2.0)
        if clearance < 2.0 * planet_tip_radius:
            messages.append(
                f"Planet gears interfere: tip-to-tip spacing {clearance:.3f} "
                f"is below the required {2.0 * planet_tip_radius:.3f}."
            )
            valid = False

    if abs(sun_planet_dist - planet_ring_dist) > module * 1e-6:
        messages.append(
            f"Sun-planet centre distance {sun_planet_dist:.4f} and planet-ring "
            f"centre distance {planet_ring_dist:.4f} differ; adjust the profile "
            "shift values."
        )
        valid = False

    ratio_ring_fixed = (z_sun + z_ring) / z_sun
    ratio_sun_fixed = (z_sun + z_ring) / z_ring

    return {
        "z_ring": z_ring,
        "sun_planet_distance": sun_planet_dist,
        "planet_ring_distance": planet_ring_dist,
        "orbit_angles": orbit_angles,
        "ring_angle": 180.0 * (z_planet + 1) / z_ring,
        # ratios are given as driven speed per carrier (or sun) revolution
        "ratio_ring_fixed": ratio_ring_fixed,
        "ratio_sun_fixed": ratio_sun_fixed,
        "ratio_carrier_fixed": -z_ring / z_sun,
        "valid": valid,
        "messages": messages,
    }


class OptimizeResult:
    """Minimal result object compatible with ``scipy.optimize.minimize``."""

    def __init__(self, x, fun=None, success=True):
        self.x = np.atleast_1d(x)
        self.fun = fun
        self.success = success


def minimize(fun, x0, tol=1e-8, maxiter=500):
    """Minimize a scalar function of one variable near ``x0``.

    Args:
        fun (callable): Objective function ``f(x) -> float``.
        x0 (float): Initial guess.
        tol (float): Relative bracket width tolerance.
        maxiter (int): Maximum golden-section iterations.

    Returns:
        OptimizeResult: ``.x`` holds the minimizer (1-element array).
    """
    x0 = float(np.asarray(x0, dtype=float).ravel()[0])
    xmin, fmin = _minimize_scalar(fun, x0, tol=tol, maxiter=maxiter)
    return OptimizeResult(xmin, fmin)


def _expand_bracket(fun, x0, grow=1.618, maxiter=100):
    """Return ``(a, b)`` bracketing a local minimum near ``x0``."""
    step = 1.0
    a = x0
    fa = fun(a)
    b = x0 + step
    fb = fun(b)

    if fb > fa:
        b = x0 - step
        fb = fun(b)
        step = -step
        if fb > fa:
            return x0 - 0.5, x0 + 0.5

    for _ in range(maxiter):
        c = b + step * grow
        fc = fun(c)
        if fc > fb:
            if a > b:
                return b, a
            return a, b
        a, fa = b, fb
        b, fb = c, fc
        step *= grow

    if a > b:
        return b, a
    return a, b


def _minimize_scalar(fun, x0, tol=1e-8, maxiter=500):
    """Golden-section search for a scalar minimum."""
    golden = (1.0 + np.sqrt(5.0)) / 2.0
    a, b = _expand_bracket(fun, x0, maxiter=min(maxiter, 100))

    c = b - (b - a) / golden
    d = a + (b - a) / golden
    fc = fun(c)
    fd = fun(d)

    for _ in range(maxiter):
        if abs(b - a) < tol * (abs(a) + abs(b) + tol):
            x = (a + b) / 2.0
            return x, fun(x)
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - (b - a) / golden
            fc = fun(c)
        else:
            a, c, fc = c, d, fd
            d = a + (b - a) / golden
            fd = fun(d)

    x = (a + b) / 2.0
    return x, fun(x)


def find_root(x0, f, df, epsilon=2e-10, max_iter=100):
    """Find a root of ``f`` near ``x0`` using damped Newton iteration.

    Args:
        x0 (float): Initial guess.
        f (callable): Function whose root is sought.
        df (callable): Derivative of ``f``.
        epsilon (float): Convergence tolerance on ``|f(x)|``.
        max_iter (int): Maximum number of iterations.

    Returns:
        float or None: Root value, or ``None`` if convergence fails.
    """
    x_n = x0
    for _ in range(max_iter):
        f_xn = f(x_n)
        if abs(f_xn) < epsilon:
            return x_n
        df_xn = df(x_n)
        if df_xn == 0:
            return None
        x_n = x_n - f_xn / df_xn / 2  # adding (/ 2) to avoid oscillation
    return None
