# -*- coding: utf-8 -*-
"""Tests for helical profile-shift migration helpers."""

import math
from unittest.mock import patch

import pytest

from freecad.gears.commands import CreateInvoluteGear
from freecad.gears.migration import (
    _parse_version,
    convert_shift_to_normal,
    migrate_shift,
    needs_shift_migration,
)
from pygears import __version__


def test_parse_version_strips_non_numeric_suffix():
    assert _parse_version("1.4.0") == (1, 4, 0)
    assert _parse_version("1.3.1rc") == (1, 3, 0)
    assert _parse_version("2") == (2,)


def test_fresh_gear_does_not_need_migration(doc):
    gear = CreateInvoluteGear.create()
    assert gear.version == __version__
    assert needs_shift_migration(gear) is False


def test_needs_migration_only_for_old_normal_system_helical(doc):
    gear = CreateInvoluteGear.create()
    gear.version = "1.0.0"
    gear.properties_from_tool = True
    gear.helix_angle = "20 deg"
    gear.shift = 0.4
    assert needs_shift_migration(gear) is True

    gear.properties_from_tool = False
    assert needs_shift_migration(gear) is False
    gear.properties_from_tool = True
    gear.helix_angle = "0 deg"
    assert needs_shift_migration(gear) is False
    gear.helix_angle = "20 deg"
    gear.shift = 0.0
    assert needs_shift_migration(gear) is False


def test_convert_shift_to_normal(doc):
    gear = CreateInvoluteGear.create()
    gear.helix_angle = "20 deg"
    gear.shift = 0.4
    assert convert_shift_to_normal(gear) is True
    assert gear.shift == pytest.approx(0.4 / math.cos(math.radians(20.0)))


def test_migrate_shift_keep_value_on_eof(doc):
    gear = CreateInvoluteGear.create()
    gear.version = "1.0.0"
    gear.properties_from_tool = True
    gear.helix_angle = "20 deg"
    gear.shift = 0.4
    with patch("builtins.input", side_effect=EOFError):
        migrate_shift(gear)
    assert gear.shift == pytest.approx(0.4)
    assert gear.version == __version__


def test_migrate_shift_converts_when_prompt_accepts(doc):
    gear = CreateInvoluteGear.create()
    gear.version = "1.0.0"
    gear.properties_from_tool = True
    gear.helix_angle = "25 deg"
    gear.shift = 0.3
    with patch("freecad.gears.migration._prompt_convert_cli", return_value=True):
        migrate_shift(gear)
    assert gear.shift == pytest.approx(0.3 / math.cos(math.radians(25.0)))
    assert gear.version == __version__
