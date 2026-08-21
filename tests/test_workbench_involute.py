# -*- coding: utf-8 -*-
"""Tests for involute, internal involute and involute rack features."""

import os
import tempfile

import numpy as np
import pytest

from freecad.gears.commands import (
    CreateInternalInvoluteGear,
    CreateInvoluteGear,
    CreateInvoluteRack,
)


def test_involute_pitch_diameter_follows_z_times_module(doc):
    gear = CreateInvoluteGear.create()
    gear.num_teeth = 20
    gear.module = "2 mm"
    gear.shift = 0.0
    doc.recompute()
    assert gear.pitch_diameter.Value == pytest.approx(40.0)
    assert gear.addendum_diameter.Value == pytest.approx(44.0)
    assert gear.Shape.isValid()
    assert len(gear.Shape.Solids) == 1
    assert gear.Shape.BoundBox.ZLength == pytest.approx(gear.height.Value)


def test_involute_more_teeth_increases_volume(doc):
    small = CreateInvoluteGear.create()
    small.num_teeth = 12
    large = CreateInvoluteGear.create()
    large.num_teeth = 24
    doc.recompute()
    assert large.Shape.Volume > small.Shape.Volume
    assert large.pitch_diameter.Value == pytest.approx(2 * small.pitch_diameter.Value)


def test_involute_helical_and_double_helix(doc):
    gear = CreateInvoluteGear.create()
    gear.num_teeth = 12
    gear.helix_angle = "15 deg"
    gear.height = "8 mm"
    doc.recompute()
    helical_volume = gear.Shape.Volume
    assert gear.Shape.isValid()
    assert gear.Shape.BoundBox.ZLength == pytest.approx(8.0)
    gear.double_helix = True
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.Volume == pytest.approx(helical_volume, rel=1e-4)


def test_involute_properties_from_tool_changes_pitch_diameter(doc):
    gear = CreateInvoluteGear.create()
    gear.num_teeth = 15
    gear.helix_angle = "20 deg"
    gear.properties_from_tool = False
    doc.recompute()
    transverse = gear.pitch_diameter.Value
    gear.properties_from_tool = True
    doc.recompute()
    assert gear.pitch_diameter.Value == pytest.approx(
        transverse / np.cos(np.deg2rad(20.0)), rel=1e-6
    )
    assert gear.traverse_module.Value == pytest.approx(
        gear.module.Value / np.cos(np.deg2rad(20.0)), rel=1e-6
    )


def test_involute_simple_is_pitch_cylinder(doc):
    gear = CreateInvoluteGear.create()
    gear.simple = True
    doc.recompute()
    radius = gear.pitch_diameter.Value / 2
    expected = np.pi * radius**2 * gear.height.Value
    assert gear.Shape.Volume == pytest.approx(expected, rel=1e-4)


def test_involute_axle_hole_reduces_volume(doc):
    gear = CreateInvoluteGear.create()
    doc.recompute()
    solid_volume = gear.Shape.Volume
    gear.axle_hole = True
    gear.axle_holesize = "6 mm"
    doc.recompute()
    hole_volume = np.pi * 3.0**2 * gear.height.Value
    assert gear.Shape.Volume == pytest.approx(solid_volume - hole_volume, rel=1e-3)
    assert gear.Shape.isValid()


def test_involute_offset_hole_reduces_volume(doc):
    gear = CreateInvoluteGear.create()
    doc.recompute()
    solid_volume = gear.Shape.Volume
    gear.offset_hole = True
    gear.offset_holesize = "4 mm"
    gear.offset_holeoffset = "3 mm"
    doc.recompute()
    assert gear.Shape.Volume < solid_volume
    assert gear.Shape.isValid()


def test_involute_zero_height_is_a_wire(doc):
    gear = CreateInvoluteGear.create()
    gear.height = "0 mm"
    doc.recompute()
    assert gear.Shape.isValid()
    assert len(gear.Shape.Solids) == 0
    assert len(gear.Shape.Wires) == 1
    assert gear.Shape.Wires[0].isClosed()


def test_involute_fillets_keep_a_valid_solid(doc):
    gear = CreateInvoluteGear.create()
    gear.head_fillet = 0.2
    gear.root_fillet = 0.2
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.Volume > 0
    assert len(gear.Shape.Faces) > 90


def test_involute_undercut_is_valid(doc):
    gear = CreateInvoluteGear.create()
    gear.num_teeth = 8
    gear.undercut = True
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.Volume > 0


def test_involute_on_document_restored_renames_beta(doc):
    gear = CreateInvoluteGear.create()
    gear.helix_angle = "12 deg"
    doc.recompute()
    angle = gear.helix_angle
    gear.removeProperty("helix_angle")
    gear.addProperty("App::PropertyAngle", "beta", "helical", "legacy helix angle")
    gear.beta = angle
    gear.Proxy.onDocumentRestored(gear)
    assert hasattr(gear, "helix_angle")
    assert gear.helix_angle.Value == pytest.approx(12.0)
    assert not hasattr(gear, "beta")


def test_involute_save_and_restore_roundtrip():
    from freecad import app
    from freecad.gears.involutegear import InvoluteGear

    document = app.newDocument("involute_roundtrip")
    handle, path = tempfile.mkstemp(suffix=".FCStd")
    os.close(handle)
    try:
        gear = CreateInvoluteGear.create()
        gear.num_teeth = 17
        gear.module = "1.5 mm"
        document.recompute()
        volume = gear.Shape.Volume
        document.saveAs(path)
        app.closeDocument(document.Name)
        document = None
        restored = app.openDocument(path)
        try:
            found = [
                obj for obj in restored.Objects if getattr(obj, "num_teeth", None) == 17
            ]
            assert len(found) == 1
            obj = found[0]
            assert isinstance(obj.Proxy, InvoluteGear)
            assert obj.module.Value == pytest.approx(1.5)
            restored.recompute()
            assert obj.Shape.Volume == pytest.approx(volume, rel=1e-6)
        finally:
            app.closeDocument(restored.Name)
    finally:
        if document is not None:
            try:
                app.closeDocument(document.Name)
            except Exception:
                pass
        os.remove(path)


def test_internal_involute_is_a_ring(doc):
    gear = CreateInternalInvoluteGear.create()
    gear.num_teeth = 30
    gear.module = "1 mm"
    gear.thickness = "6 mm"
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.pitch_diameter.Value == pytest.approx(30.0)
    bbox = gear.Shape.BoundBox
    # outer envelope is pitch plus rim thickness
    assert bbox.XLength > gear.pitch_diameter.Value
    assert gear.Shape.Volume > 0


def test_internal_involute_helical(doc):
    gear = CreateInternalInvoluteGear.create()
    gear.num_teeth = 20
    gear.helix_angle = "12 deg"
    doc.recompute()
    assert gear.Shape.isValid()
    assert gear.Shape.BoundBox.ZLength == pytest.approx(gear.height.Value)


def test_involute_rack_length_scales_with_teeth(doc):
    rack = CreateInvoluteRack.create()
    rack.num_teeth = 10
    rack.add_endings = False
    doc.recompute()
    assert rack.Shape.isValid()
    assert rack.Shape.BoundBox.ZLength == pytest.approx(rack.height.Value)
    # pitch = π m per tooth
    assert rack.Shape.BoundBox.YLength == pytest.approx(10 * np.pi * rack.module.Value, rel=0.15)


def test_involute_rack_simplified_flag_is_forwarded(doc):
    # generate_gear_shape builds every tooth in FreeCAD; `simplified` is only
    # forwarded to the python rack object (used by pygears.InvoluteRack.points).
    rack = CreateInvoluteRack.create()
    rack.num_teeth = 15
    rack.simplified = True
    doc.recompute()
    assert rack.simplified is True
    assert rack.rack.simplified is True
    assert rack.Shape.isValid()
    assert rack.Shape.Volume > 0


def test_involute_rack_helical_keeps_volume(doc):
    rack = CreateInvoluteRack.create()
    doc.recompute()
    spur_volume = rack.Shape.Volume
    rack.helix_angle = "20 deg"
    doc.recompute()
    assert rack.Shape.isValid()
    assert rack.Shape.Volume == pytest.approx(spur_volume, rel=1e-6)
