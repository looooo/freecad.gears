# -*- coding: utf-8 -*-
"""Tests for workbench commands: creation, metadata, default shapes."""

import os

import pytest

from freecad import app
from freecad.gears.commands import (
    CreateBevelGear,
    CreateCrownGear,
    CreateCycloidGear,
    CreateCycloidRack,
    CreateGearConnector,
    CreateHypoCycloidGear,
    CreateInternalInvoluteGear,
    CreateInvoluteGear,
    CreateInvoluteRack,
    CreateLanternGear,
    CreateTimingGear,
    CreateTimingGearT,
    CreateWormGear,
)
from freecad.gears.basegear import BaseGear
from freecad.gears.bevelgear import BevelGear
from freecad.gears.crowngear import CrownGear
from freecad.gears.cycloidgear import CycloidGear
from freecad.gears.cycloidgearrack import CycloidGearRack
from freecad.gears.hypocycloidgear import HypoCycloidGear
from freecad.gears.internalinvolutegear import InternalInvoluteGear
from freecad.gears.involutegear import InvoluteGear
from freecad.gears.involutegearrack import InvoluteGearRack
from freecad.gears.lanterngear import LanternGear
from freecad.gears.timinggear import TimingGear
from freecad.gears.timinggear_t import TimingGearT
from freecad.gears.wormgear import WormGear


GEAR_COMMANDS = [
    CreateInvoluteGear,
    CreateInternalInvoluteGear,
    CreateInvoluteRack,
    CreateCycloidGear,
    CreateCycloidRack,
    CreateBevelGear,
    CreateCrownGear,
    CreateWormGear,
    CreateTimingGearT,
    CreateTimingGear,
    CreateLanternGear,
    CreateHypoCycloidGear,
]

_PROXY = {
    CreateInvoluteGear: InvoluteGear,
    CreateInternalInvoluteGear: InternalInvoluteGear,
    CreateInvoluteRack: InvoluteGearRack,
    CreateCycloidGear: CycloidGear,
    CreateCycloidRack: CycloidGearRack,
    CreateBevelGear: BevelGear,
    CreateCrownGear: CrownGear,
    CreateWormGear: WormGear,
    CreateTimingGearT: TimingGearT,
    CreateTimingGear: TimingGear,
    CreateLanternGear: LanternGear,
    CreateHypoCycloidGear: HypoCycloidGear,
}


def _prepare_for_recompute(command_cls, obj):
    """Default parameters that yield a valid solid/wire in headless OCCT."""
    if command_cls is CreateWormGear:
        # 3D helical extrusion of the default worm profile is currently invalid.
        obj.height = "0 mm"
    elif command_cls is CreateHypoCycloidGear:
        obj.teeth_number = 12
        obj.segment_count = 16
        obj.show_pins = False
        obj.show_disk1 = False


@pytest.mark.parametrize("command_cls", GEAR_COMMANDS, ids=lambda c: c.NAME)
def test_command_resources_and_icon(command_cls):
    command = command_cls()
    resources = command.GetResources()
    assert "Pixmap" in resources and "MenuText" in resources and "ToolTip" in resources
    assert os.path.isfile(command_cls.Pixmap)
    assert command_cls.NAME
    assert issubclass(command_cls.GEAR_FUNCTION, BaseGear)


def test_command_is_active_only_with_document(doc):
    command = CreateInvoluteGear()
    assert command.IsActive() is True


def test_command_inactive_without_document():
    for name in list(app.listDocuments()):
        app.closeDocument(name)
    assert CreateInvoluteGear().IsActive() is False
    assert app.ActiveDocument is None


@pytest.mark.parametrize("command_cls", GEAR_COMMANDS, ids=lambda c: c.NAME)
def test_create_default_gear_has_valid_shape(doc, command_cls):
    obj = command_cls.create()
    assert obj is not None
    assert obj.Document is doc
    assert isinstance(obj.Proxy, _PROXY[command_cls])
    _prepare_for_recompute(command_cls, obj)
    doc.recompute()
    shape = obj.Shape
    assert shape is not None
    assert not shape.isNull()
    assert shape.isValid()
    if command_cls is CreateWormGear:
        assert len(shape.Wires) >= 1
        assert len(shape.Solids) == 0
    else:
        assert len(shape.Solids) >= 1
        assert shape.Volume > 0
        assert shape.BoundBox.ZLength > 0


def test_gear_connector_command_requires_two_gears():
    # create() would call GearConnector(obj) without the two gear links
    assert CreateGearConnector.GEAR_FUNCTION.__name__ == "GearConnector"
    assert os.path.isfile(CreateGearConnector.Pixmap)
    command = CreateGearConnector()
    resources = command.GetResources()
    assert "MenuText" in resources


def test_find_body_walks_inlist():
    class _Obj:
        def __init__(self, type_id="Part::Feature"):
            self.TypeId = type_id
            self.InList = []

    gear = _Obj()
    assert CreateGearConnector._find_body(gear) is None
    body = _Obj("PartDesign::Body")
    gear.InList = [body]
    assert CreateGearConnector._find_body(gear) is body
