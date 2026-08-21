# -*- coding: utf-8 -*-
"""Tests for cycloid, bevel, crown, worm, timing, lantern and hypocycloid gears."""

import numpy as np
import pytest

from freecad.gears.commands import (
    CreateBevelGear,
    CreateCrownGear,
    CreateCycloidGear,
    CreateCycloidRack,
    CreateHypoCycloidGear,
    CreateLanternGear,
    CreateTimingGear,
    CreateTimingGearT,
    CreateWormGear,
)
from freecad.gears.timinggear import TimingGear


def test_cycloid_pitch_diameter_and_helical(doc):
    gear = CreateCycloidGear.create()
    gear.num_teeth = 16
    gear.module = "1.5 mm"
    doc.recompute()
    assert gear.pitch_diameter.Value == pytest.approx(24.0)
    assert gear.Shape.isValid()
    gear.helix_angle = "15 deg"
    gear.height = "6 mm"
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.BoundBox.ZLength == pytest.approx(6.0)
    gear.double_helix = True
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.Volume > 0


def test_cycloid_rack_is_a_solid(doc):
    rack = CreateCycloidRack.create()
    rack.num_teeth = 8
    doc.recompute()
    assert rack.Shape.isValid()
    assert rack.Shape.Volume > 0
    assert rack.Shape.BoundBox.ZLength == pytest.approx(rack.height.Value)


def test_bevel_default_and_spiral(doc):
    gear = CreateBevelGear.create()
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.dw.Value == pytest.approx(gear.num_teeth * gear.module.Value)
    assert gear.Shape.BoundBox.ZLength == pytest.approx(gear.height.Value, rel=1e-5)
    spur_volume = gear.Shape.Volume
    gear.beta = "12 deg"
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.Volume == pytest.approx(spur_volume, rel=1e-2)


def test_crown_preview_and_full_cut(doc):
    gear = CreateCrownGear.create()
    gear.num_teeth = 12
    gear.other_teeth = 12
    gear.num_profiles = 3
    gear.preview_mode = True
    doc.recompute()
    assert gear.Shape.isValid()
    preview_faces = len(gear.Shape.Faces)
    preview_volume = gear.Shape.Volume
    gear.preview_mode = False
    doc.recompute()
    assert gear.Shape.isValid()
    assert len(gear.Shape.Faces) > preview_faces
    assert gear.Shape.Volume < preview_volume


def test_worm_profile_wire_and_lead_angle(doc):
    worm = CreateWormGear.create()
    worm.height = "0 mm"
    worm.diameter = "20 mm"
    worm.module = "2 mm"
    worm.num_teeth = 2
    doc.recompute()
    assert worm.Shape.isValid()
    assert len(worm.Shape.Wires) == 1
    expected_beta = np.rad2deg(np.arctan(worm.module.Value * worm.num_teeth / worm.diameter.Value))
    assert worm.beta.Value == pytest.approx(expected_beta, rel=1e-6)


def test_worm_solid_extrusion_is_currently_invalid(doc):
    worm = CreateWormGear.create()
    worm.height = "10 mm"
    worm.diameter = "15 mm"
    doc.recompute()
    with pytest.raises(RuntimeError, match="invalid"):
        _ = worm.Shape.Volume


def test_timing_gear_types_produce_solids(doc):
    volumes = {}
    for tooth_type in TimingGear.data:
        gear = CreateTimingGear.create()
        gear.type = tooth_type
        gear.num_teeth = 16
        doc.recompute()
        assert gear.Shape.isValid(), tooth_type
        assert gear.Shape.Volume > 0
        assert gear.pitch.Value == pytest.approx(TimingGear.data[tooth_type]["pitch"])
        volumes[tooth_type] = gear.Shape.Volume
    assert volumes["gt8"] > volumes["gt2"]


def test_timing_gear_t_shape(doc):
    gear = CreateTimingGearT.create()
    gear.num_teeth = 12
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.Volume > 0
    assert gear.Shape.BoundBox.ZLength == pytest.approx(gear.height.Value)


def test_lantern_gear_solid(doc):
    gear = CreateLanternGear.create()
    gear.num_teeth = 12
    gear.num_profiles = 6
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.Volume > 0
    pitch_radius = gear.module.Value * gear.num_teeth / 2
    assert gear.Shape.BoundBox.XLength == pytest.approx(2 * (pitch_radius + gear.bolt_radius.Value + gear.head * gear.module.Value), rel=0.15)


def test_hypocycloid_cam_disk(doc):
    gear = CreateHypoCycloidGear.create()
    gear.teeth_number = 12
    gear.segment_count = 16
    gear.show_pins = False
    gear.show_disk1 = False
    doc.recompute()
    assert gear.Shape.isValid()
    assert len(gear.Shape.Solids) == 1
    assert gear.Shape.Volume > 0
