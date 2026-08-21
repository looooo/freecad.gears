# -*- coding: utf-8 -*-
"""Unit tests for full-gear profiles in pygears.profile."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pygears.profile import (
    BevelProfile,
    CycloidProfile,
    InvoluteProfile,
    InvoluteRackProfile,
)
from pygears.bevel_tooth import BevelTooth
from pygears.cycloid_tooth import CycloidTooth
from pygears.involute_tooth import InvoluteRack, InvoluteTooth


def test_involute_profile_is_closed_and_has_all_teeth():
    gear = InvoluteProfile(num_teeth=12, m=2.0, shift=0.2)
    profile = gear.profile(num=6)
    assert profile.shape[1] == 2
    assert_allclose(profile[0], profile[-1])
    assert np.all(np.isfinite(profile))
    # one tooth, then (z-1) rotated copies, then the closing duplicate of the first vertex
    tooth = [list(point) for wire in gear.points(num=6) for point in wire]
    expected = len(tooth) * gear.num_teeth + 1
    assert profile.shape[0] == expected


def test_involute_profile_has_rotational_symmetry():
    gear = InvoluteProfile(num_teeth=9)
    profile = gear.profile(num=5)
    # drop the closing point and check z-fold periodicity of radii
    radii = np.linalg.norm(profile[:-1], axis=1)
    tooth_len = len([p for wire in gear.points(num=5) for p in wire])
    first = radii[:tooth_len]
    second = radii[tooth_len : 2 * tooth_len]
    assert_allclose(first, second, atol=1e-10)


def test_cycloid_profile_is_closed():
    gear = CycloidProfile(num_teeth=14, m=3.0)
    profile = gear.profile(num=6)
    assert profile.shape[1] == 2
    assert_allclose(profile[0], profile[-1])
    radii = np.linalg.norm(profile, axis=1)
    assert radii.max() == pytest.approx(gear.da / 2, rel=1e-8)
    assert radii.min() == pytest.approx(gear.di / 2, rel=1e-8)


def test_bevel_profile_is_closed_on_z_one_plane():
    gear = BevelProfile(z=15)
    profile = gear.profile(num=5)
    assert profile.shape[1] == 3
    assert_allclose(profile[0], profile[-1])
    assert_allclose(profile[:, 2], 1.0)
    assert np.all(np.isfinite(profile))


def test_involute_rack_profile_delegates_to_points():
    rack = InvoluteRackProfile(num_teeth=4, add_endings=False)
    profile = rack.profile()
    assert_allclose(profile, rack.points())
    assert_allclose(profile[0], profile[-1])


def test_profile_classes_reuse_tooth_implementations():
    assert issubclass(InvoluteProfile, InvoluteTooth)
    assert issubclass(CycloidProfile, CycloidTooth)
    assert issubclass(BevelProfile, BevelTooth)
    assert issubclass(InvoluteRackProfile, InvoluteRack)


def test_bevel_profile_uses_3d_rotation():
    assert BevelProfile.rot3D is True
    assert InvoluteProfile.rot3D is False
    assert CycloidProfile.rot3D is False
