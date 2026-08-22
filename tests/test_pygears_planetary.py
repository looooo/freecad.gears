# -*- coding: utf-8 -*-
"""Unit tests for planetary gear computation."""

import numpy as np
import pytest

from pygears.computation import (
    compute_planetary_gears,
    compute_shifted_internal_gears,
    planetary_orbit_angles,
    planetary_phase_angles,
)


def assert_meshes(z_sun, z_planet, num_planets, carrier_angle=0.0):
    """Assert the tooth phase conditions hold for sun-planet and planet-ring.

    An external gear carries a tooth on its local +x axis, an internal gear a
    tooth space. Measured along the line of centres, a tooth of one gear must
    land on the space of the other, which gives the two congruences below.
    """
    z_ring = z_sun + 2 * z_planet
    orbits = planetary_orbit_angles(z_sun, z_ring, num_planets)
    phases = planetary_phase_angles(
        z_sun, z_planet, z_ring, orbits, carrier_angle
    )

    def residual(value):
        return abs((value + 180.0) % 360.0 - 180.0)

    for orbit, planet in zip(phases["planet_orbits"], phases["planet_angles"]):
        sun_terms = z_sun * (phases["sun_angle"] - orbit) + z_planet * (
            planet - orbit - 180.0
        )
        assert residual(sun_terms - 180.0) < 1e-9
        ring_terms = z_ring * (phases["ring_angle"] - orbit) - z_planet * (
            planet - orbit
        )
        assert residual(ring_terms) < 1e-9


def test_planetary_ring_teeth_constraint():
    result = compute_planetary_gears(1.0, np.deg2rad(20.0), 24, 18, 3)
    assert result["z_ring"] == 60
    assert result["valid"] is True


def test_planetary_assembly_condition_fails():
    result = compute_planetary_gears(1.0, np.deg2rad(20.0), 17, 18, 3)
    assert result["valid"] is False
    assert any("Assembly condition" in msg for msg in result["messages"])


def test_planetary_distances_match_for_unshifted_gears():
    result = compute_planetary_gears(2.5, np.deg2rad(20.0), 24, 18, 3)
    expected = 2.5 * (24 + 18) / 2.0
    assert result["sun_planet_distance"] == pytest.approx(expected)
    assert result["planet_ring_distance"] == pytest.approx(expected)
    assert result["valid"] is True


def test_planetary_ratio_with_ring_fixed():
    result = compute_planetary_gears(1.0, np.deg2rad(20.0), 24, 18, 3)
    assert result["ratio_ring_fixed"] == pytest.approx(1.0 + 60 / 24)


def test_planetary_too_few_sun_teeth():
    result = compute_planetary_gears(1.0, np.deg2rad(20.0), 4, 20, 3)
    assert result["valid"] is False
    assert any("Sun gear" in msg for msg in result["messages"])


def test_planetary_ratio_with_sun_fixed():
    result = compute_planetary_gears(1.0, np.deg2rad(20.0), 24, 18, 3)
    assert result["ratio_sun_fixed"] == pytest.approx((24 + 60) / 60)


def test_internal_pair_distance_matches_external_for_equal_shift():
    dist, _ = compute_shifted_internal_gears(2.0, np.deg2rad(20.0), 60, 18, 0.3, 0.3)
    assert dist == pytest.approx(2.0 * (60 - 18) / 2.0)


@pytest.mark.parametrize("num_planets", [1, 2, 3, 4, 6])
def test_orbit_angles_are_equally_spaced_when_condition_holds(num_planets):
    angles = planetary_orbit_angles(24, 60, num_planets)
    assert angles == pytest.approx(
        [360.0 / num_planets * i for i in range(num_planets)]
    )


def test_orbit_angles_snap_to_meshable_positions():
    # 24 + 60 = 84 is not divisible by 5, so equal spacing is impossible.
    angles = planetary_orbit_angles(24, 60, 5)
    step = 360.0 / 84
    assert len(set(angles)) == 5
    for angle in angles:
        assert angle / step == pytest.approx(round(angle / step))


@pytest.mark.parametrize(
    "z_sun, z_planet, num_planets",
    [(24, 18, 3), (21, 15, 3), (25, 17, 3), (20, 16, 4), (24, 12, 6)],
)
@pytest.mark.parametrize("carrier_angle", [0.0, 37.0, -113.5])
def test_phase_angles_mesh(z_sun, z_planet, num_planets, carrier_angle):
    assert_meshes(z_sun, z_planet, num_planets, carrier_angle)


def test_phase_angles_follow_epicyclic_ratios():
    phases_0 = planetary_phase_angles(24, 18, 60, [0.0], 0.0)
    phases_1 = planetary_phase_angles(24, 18, 60, [0.0], 90.0)
    assert phases_1["sun_angle"] - phases_0["sun_angle"] == pytest.approx(
        90.0 * (24 + 60) / 24
    )
    assert phases_1["planet_angles"][0] - phases_0["planet_angles"][0] == (
        pytest.approx(90.0 * (1 - 60 / 18))
    )
    assert phases_1["ring_angle"] == pytest.approx(phases_0["ring_angle"])


def test_planet_interference_uses_tip_radius():
    # Four planets of 30 teeth cannot fit around a 12 tooth sun.
    result = compute_planetary_gears(1.0, np.deg2rad(20.0), 12, 30, 4)
    assert result["valid"] is False
    assert any("interfere" in msg for msg in result["messages"])
