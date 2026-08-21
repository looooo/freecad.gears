# -*- coding: utf-8 -*-
"""Tests for GearConnector and ChainConnector kinematics."""

import numpy as np
import pytest

from freecad import app
from freecad.gears.chainconnector import Chain
from freecad.gears.commands import (
    CreateCycloidGear,
    CreateInternalInvoluteGear,
    CreateInvoluteGear,
    CreateInvoluteRack,
)
from freecad.gears.connector import GearConnector


def _connector(master, slave):
    obj = app.ActiveDocument.addObject("Part::FeaturePython", "GearConnector")
    GearConnector(obj, master, slave)
    return obj


def test_involute_pair_centre_distance_and_rotation(doc, headless_viewprovider):
    master = CreateInvoluteGear.create()
    master.num_teeth = 20
    slave = CreateInvoluteGear.create()
    slave.num_teeth = 40
    doc.recompute()
    connector = _connector(master, slave)
    doc.recompute()
    expected = (master.pitch_diameter.Value + slave.pitch_diameter.Value) / 2
    assert (slave.Placement.Base - master.Placement.Base).Length == pytest.approx(expected)
    connector.angle1 = "36 deg"
    doc.recompute()
    assert np.degrees(master.Placement.Rotation.Angle) == pytest.approx(36.0)
    assert slave.Placement.Rotation.Angle != 0.0


def test_shifted_involute_pair_uses_working_centre_distance(doc, headless_viewprovider):
    from pygears.computation import compute_shifted_gears

    master = CreateInvoluteGear.create()
    master.num_teeth = 20
    master.shift = 0.4
    slave = CreateInvoluteGear.create()
    slave.num_teeth = 30
    slave.shift = 0.2
    doc.recompute()
    _connector(master, slave)
    doc.recompute()
    expected, _alpha = compute_shifted_gears(
        master.module.Value,
        np.deg2rad(master.pressure_angle.Value),
        master.num_teeth,
        slave.num_teeth,
        master.shift,
        slave.shift,
    )
    dist = (slave.Placement.Base - master.Placement.Base).Length
    assert dist == pytest.approx(expected, rel=1e-6)
    assert dist > (master.pitch_diameter.Value + slave.pitch_diameter.Value) / 2


def test_internal_involute_meshes_inside(doc, headless_viewprovider):
    ring = CreateInternalInvoluteGear.create()
    ring.num_teeth = 40
    pinion = CreateInvoluteGear.create()
    pinion.num_teeth = 15
    doc.recompute()
    _connector(ring, pinion)
    doc.recompute()
    expected = (ring.pitch_diameter.Value - pinion.pitch_diameter.Value) / 2
    assert (pinion.Placement.Base - ring.Placement.Base).Length == pytest.approx(expected)


def test_involute_drives_rack_along_y(doc, headless_viewprovider):
    gear = CreateInvoluteGear.create()
    rack = CreateInvoluteRack.create()
    doc.recompute()
    connector = _connector(gear, rack)
    doc.recompute()
    assert rack.Placement.Base.x == pytest.approx(-gear.pitch_diameter.Value / 2)
    connector.angle1 = "90 deg"
    doc.recompute()
    dw = gear.pitch_diameter.Value
    # 90° rotation is applied after the meshing offset and rolling translation
    assert rack.Placement.Base.x == pytest.approx(-np.deg2rad(90.0) * dw / 2)
    assert rack.Placement.Base.y == pytest.approx(-dw / 2)


def test_cycloid_pair_centre_distance(doc, headless_viewprovider):
    master = CreateCycloidGear.create()
    master.num_teeth = 14
    slave = CreateCycloidGear.create()
    slave.num_teeth = 21
    doc.recompute()
    _connector(master, slave)
    doc.recompute()
    expected = (master.pitch_diameter.Value + slave.pitch_diameter.Value) / 2
    assert (slave.Placement.Base - master.Placement.Base).Length == pytest.approx(expected)


def test_slave_orbits_when_not_stationary(doc, headless_viewprovider):
    master = CreateInvoluteGear.create()
    slave = CreateInvoluteGear.create()
    slave.num_teeth = 30
    doc.recompute()
    connector = _connector(master, slave)
    connector.slave_gear_stationary = False
    connector.angle1 = "90 deg"
    doc.recompute()
    dist = (master.pitch_diameter.Value + slave.pitch_diameter.Value) / 2
    # slave should sit on the +Y axis after a 90° orbit
    assert slave.Placement.Base.x == pytest.approx(0.0, abs=1e-6)
    assert slave.Placement.Base.y == pytest.approx(dist)


def test_chain_of_three_involute_gears(doc, headless_viewprovider):
    g1 = CreateInvoluteGear.create()
    g1.num_teeth = 15
    g2 = CreateInvoluteGear.create()
    g2.num_teeth = 20
    g3 = CreateInvoluteGear.create()
    g3.num_teeth = 25
    doc.recompute()
    chain_obj = app.ActiveDocument.addObject("Part::FeaturePython", "Chain")
    Chain(chain_obj, [g1, g2, g3])
    doc.recompute()
    d12 = (g1.pitch_diameter.Value + g2.pitch_diameter.Value) / 2
    d23 = (g2.pitch_diameter.Value + g3.pitch_diameter.Value) / 2
    assert chain_obj.gear_list == [g1, g2, g3]
    assert (g2.Placement.Base - g1.Placement.Base).Length == pytest.approx(d12)
    # The chain-connector expression for master_gear is not resolved during
    # the first execute(); set the link and run kinematics explicitly.
    chain_connectors = [
        obj
        for obj in doc.Objects
        if getattr(getattr(obj, "Proxy", None), "__class__", type).__name__
        == "ChainConnector"
    ]
    assert len(chain_connectors) == 1
    extra = chain_connectors[0]
    extra.master_gear = g2
    extra.Proxy.execute(extra)
    assert (g3.Placement.Base - g2.Placement.Base).Length == pytest.approx(d23)
    chain_obj.angle = "20 deg"
    doc.recompute()
    assert np.degrees(g1.Placement.Rotation.Angle) == pytest.approx(20.0)
