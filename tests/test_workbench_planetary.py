# -*- coding: utf-8 -*-
"""Tests for planetary gear assembly creation and placement."""

import numpy as np
import pytest

from freecad import app
from freecad.gears.assembly_helper import assembly_workbench_available
from freecad.gears.involutegear import InvoluteGear
from freecad.gears.internalinvolutegear import InternalInvoluteGear
from freecad.gears.planetarygear import (
    PlanetaryGearAssembly,
    ViewProviderPlanetaryGear,
    create_planetary_assembly,
)
from pygears.computation import (
    compute_planetary_gears,
    planetary_orbit_angles,
    planetary_phase_angles,
)


@pytest.fixture
def headless_planetary_viewprovider():
    original = ViewProviderPlanetaryGear.__init__

    def _init(self, vobj, icon_fn=None):
        if vobj is None:
            self.icon_fn = icon_fn or ""
            return None
        return original(self, vobj, icon_fn)

    ViewProviderPlanetaryGear.__init__ = _init
    try:
        yield
    finally:
        ViewProviderPlanetaryGear.__init__ = original


def test_create_planetary_assembly_builds_gears(doc, headless_planetary_viewprovider):
    assembly = create_planetary_assembly(
        num_planets=3,
        z_sun=24,
        z_planet=18,
        use_assembly=False,
    )
    assert isinstance(assembly.Proxy, PlanetaryGearAssembly)
    assert assembly.sun_gear is not None
    assert assembly.ring_gear is not None
    assert len(assembly.planet_gears) == 3
    assert isinstance(assembly.sun_gear.Proxy, InvoluteGear)
    assert isinstance(assembly.ring_gear.Proxy, InternalInvoluteGear)


def test_planetary_planet_spacing(doc, headless_planetary_viewprovider):
    assembly = create_planetary_assembly(
        num_planets=3,
        z_sun=24,
        z_planet=18,
        use_assembly=False,
    )
    doc.recompute()
    result = compute_planetary_gears(
        assembly.module.Value,
        np.deg2rad(assembly.pressure_angle.Value),
        assembly.z_sun,
        assembly.z_planet,
        assembly.num_planets,
    )
    sun_base = assembly.sun_gear.Placement.Base
    for index, planet in enumerate(assembly.planet_gears):
        dist = (planet.Placement.Base - sun_base).Length
        assert dist == pytest.approx(result["sun_planet_distance"], rel=1e-6)
        expected_angle = 360.0 / assembly.num_planets * index
        direction = planet.Placement.Base - sun_base
        angle = np.degrees(np.arctan2(direction.y, direction.x)) % 360.0
        assert angle == pytest.approx(expected_angle, abs=1e-6)


def test_planetary_ring_is_concentric(doc, headless_planetary_viewprovider):
    assembly = create_planetary_assembly(use_assembly=False)
    doc.recompute()
    assert assembly.ring_gear.Placement.Base == assembly.sun_gear.Placement.Base


def _z_angle(placement):
    rotation = placement.Rotation
    sign = 1.0 if rotation.Axis.z >= 0 else -1.0
    return np.degrees(rotation.Angle) * sign


def test_planetary_gears_carry_meshing_phase(doc, headless_planetary_viewprovider):
    assembly = create_planetary_assembly(
        num_planets=3, z_sun=24, z_planet=18, use_assembly=False
    )
    doc.recompute()
    phases = planetary_phase_angles(
        assembly.z_sun,
        assembly.z_planet,
        assembly.z_ring,
        planetary_orbit_angles(assembly.z_sun, assembly.z_ring, assembly.num_planets),
    )
    assert _z_angle(assembly.ring_gear.Placement) == pytest.approx(
        phases["ring_angle"]
    )
    for planet, expected in zip(assembly.planet_gears, phases["planet_angles"]):
        assert _z_angle(planet.Placement) % 360.0 == pytest.approx(
            expected % 360.0, abs=1e-9
        )


def test_planetary_carrier_angle_drives_epicyclic_motion(
    doc, headless_planetary_viewprovider
):
    assembly = create_planetary_assembly(
        num_planets=3, z_sun=24, z_planet=18, use_assembly=False
    )
    doc.recompute()
    carrier_angle = 40.0
    assembly.carrier_angle = f"{carrier_angle} deg"
    doc.recompute()

    ratio = (assembly.z_sun + assembly.z_ring) / assembly.z_sun
    assert _z_angle(assembly.sun_gear.Placement) % 360.0 == pytest.approx(
        carrier_angle * ratio % 360.0
    )
    # The ring stays put while the planets orbit with the carrier.
    assert _z_angle(assembly.ring_gear.Placement) == pytest.approx(
        180.0 * (assembly.z_planet + 1) / assembly.z_ring
    )
    for index, planet in enumerate(assembly.planet_gears):
        base = planet.Placement.Base
        angle = np.degrees(np.arctan2(base.y, base.x)) % 360.0
        expected = (360.0 / assembly.num_planets * index + carrier_angle) % 360.0
        assert angle == pytest.approx(expected)


@pytest.mark.skipif(
    not assembly_workbench_available(), reason="Assembly workbench not available"
)
def test_each_planetary_set_gets_its_own_assembly(
    doc, headless_planetary_viewprovider
):
    first = create_planetary_assembly(num_planets=3, z_sun=24, z_planet=18)
    second = create_planetary_assembly(num_planets=4, z_sun=20, z_planet=16)

    containers = [obj.getParentGeoFeatureGroup() for obj in (first, second)]
    assert all(c is not None for c in containers)
    assert containers[0] is not containers[1]

    for obj, container in zip((first, second), containers):
        parts = [obj.sun_gear, obj.ring_gear, obj.carrier, *obj.planet_gears]
        assert all(part.getParentGeoFeatureGroup() is container for part in parts)


def test_configuration_drives_every_gear(doc, headless_planetary_viewprovider):
    config = create_planetary_assembly(
        num_planets=3,
        z_sun=24,
        z_planet=18,
        use_assembly=False,
        ring_thickness="3 mm",
        hole_sun="6 mm",
        hole_planets="4 mm",
        backlash="0.05 mm",
    )
    doc.recompute()
    gears = [config.sun_gear, config.ring_gear, *config.planet_gears]

    assert all(gear.backlash.Value == pytest.approx(0.05) for gear in gears)
    assert config.ring_gear.thickness.Value == pytest.approx(3.0)
    assert config.ring_gear.outside_diameter.Value == pytest.approx(
        config.module.Value * config.z_ring + 2 * 3.0
    )
    assert config.sun_gear.axle_hole and config.sun_gear.axle_holesize.Value == 6.0
    for planet in config.planet_gears:
        assert planet.axle_hole and planet.axle_holesize.Value == pytest.approx(4.0)
    # The ring gear has no bore to place.
    assert not hasattr(config.ring_gear, "axle_hole")

    config.numpoints = 12
    doc.recompute()
    assert all(gear.numpoints == 12 for gear in gears)


def test_helix_hands_match_the_mesh_type(doc, headless_planetary_viewprovider):
    config = create_planetary_assembly(
        num_planets=3, z_sun=24, z_planet=18, use_assembly=False
    )
    config.helix_angle = "15 deg"
    doc.recompute()

    # An external mesh needs opposite hands, an internal mesh the same hand.
    assert config.sun_gear.helix_angle.Value == pytest.approx(15.0)
    assert config.ring_gear.helix_angle.Value == pytest.approx(-15.0)
    for planet in config.planet_gears:
        assert planet.helix_angle.Value == pytest.approx(-15.0)


def test_oversized_bore_is_reported(doc, headless_planetary_viewprovider):
    config = create_planetary_assembly(
        num_planets=3, z_sun=24, z_planet=18, use_assembly=False
    )
    config.hole_sun = "40 mm"
    doc.recompute()
    assert "bore" in config.validation_message


def test_planetary_planets_stay_on_the_pitch_circle(
    doc, headless_planetary_viewprovider
):
    assembly = create_planetary_assembly(
        num_planets=4, z_sun=20, z_planet=16, use_assembly=False
    )
    assembly.carrier_angle = "17 deg"
    doc.recompute()
    for planet in assembly.planet_gears:
        base = planet.Placement.Base
        assert base.Length == pytest.approx(assembly.sun_planet_distance.Value)
        assert base.z == pytest.approx(0.0)
