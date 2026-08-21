# -*- coding: utf-8 -*-
"""Unit tests for involute gear and rack geometry in pygears.involute_tooth."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pygears.involute_tooth import InvoluteRack, InvoluteTooth


def _stack(segments):
    return np.vstack([np.atleast_2d(segment) for segment in segments])


def _radii(segments):
    return np.linalg.norm(_stack(segments), axis=1)


def _segments_connected(segments, atol=1e-10):
    for previous, current in zip(segments, segments[1:]):
        previous = np.atleast_2d(previous)
        current = np.atleast_2d(current)
        if np.linalg.norm(previous[-1] - current[0]) > atol:
            return False
    return True


def _is_symmetric_about_x(points, atol=1e-8):
    mirrored = points * np.array([1.0, -1.0])
    for point in mirrored:
        if np.min(np.linalg.norm(points - point, axis=1)) > atol:
            return False
    return True


def test_default_gear_factors():
    tooth = InvoluteTooth()
    assert tooth.m == tooth.m_n == 5
    assert tooth.pitch == pytest.approx(tooth.m * np.pi)
    assert tooth.d == pytest.approx(tooth.num_teeth * tooth.m)
    assert tooth.dw == pytest.approx(tooth.d)
    assert tooth.phipart == pytest.approx(2 * np.pi / tooth.num_teeth)
    # tip / root diameters (with default shift=0.5, head=0, clearance=0.12)
    assert tooth.da == pytest.approx(
        tooth.dw + 2 * tooth.m_n + 2 * (tooth.shift + tooth.head) * tooth.m_n
    )
    assert tooth.df == pytest.approx(
        tooth.dw - 2 * tooth.m_n - 2 * tooth.c + 2 * tooth.shift * tooth.m_n
    )
    assert tooth.dg == pytest.approx(tooth.d * np.cos(tooth.pressure_angle_t))
    assert tooth.angular_backlash == pytest.approx(0.0)
    assert tooth.involute_start == pytest.approx(0.0)
    assert tooth.dg > tooth.df


def test_involute_start_when_base_circle_inside_root():
    tooth = InvoluteTooth(num_teeth=40, shift=0.0)
    assert tooth.dg <= tooth.df
    assert tooth.involute_start == pytest.approx(
        np.sqrt(tooth.df**2 - tooth.dg**2) / tooth.dg
    )


def test_involute_parametric_radius():
    tooth = InvoluteTooth()
    points = tooth.involute_points(num=25)
    phi = np.linspace(tooth.involute_start, tooth.involute_end, 25)
    expected = (tooth.dg / 2) * np.sqrt(1.0 + phi**2)
    assert_allclose(np.linalg.norm(points, axis=1), expected, atol=1e-12)


def test_involute_functions_start_on_base_circle():
    tooth = InvoluteTooth()
    assert tooth.involute_function_x()(0.0) == pytest.approx(tooth.dg / 2)
    assert tooth.involute_function_y()(0.0) == pytest.approx(0.0)


def test_undercut_functions_start_on_root_circle():
    tooth = InvoluteTooth()
    assert tooth.undercut_function_x()(0.0) == pytest.approx(tooth.df / 2)
    assert tooth.undercut_function_y()(0.0) == pytest.approx(0.0)


@pytest.mark.parametrize("num", [5, 10, 20])
def test_points_without_undercut_are_connected_symmetric_and_in_annulus(num):
    tooth = InvoluteTooth(undercut=False)
    segments = tooth.points(num=num)
    assert _segments_connected(segments)
    points = _stack(segments)
    assert _is_symmetric_about_x(points)
    radii = _radii(segments)
    assert radii.min() == pytest.approx(tooth.df / 2, rel=1e-9)
    assert radii.max() == pytest.approx(tooth.da / 2, rel=1e-9)
    # root stubs + involute + tip + mirrored involute + mirrored root
    assert len(segments) == 5
    assert segments[1].shape == (num, 2)
    assert segments[3].shape == (num, 2)


def test_points_when_base_circle_inside_root_have_no_root_stub():
    tooth = InvoluteTooth(num_teeth=40, shift=0.0, undercut=False)
    segments = tooth.points(num=8)
    assert len(segments) == 3
    assert _segments_connected(segments)
    radii = _radii(segments)
    assert radii.min() == pytest.approx(tooth.df / 2, rel=1e-9)
    assert radii.max() == pytest.approx(tooth.da / 2, rel=1e-9)


def test_points_with_undercut():
    tooth = InvoluteTooth(num_teeth=8, shift=0.0, undercut=True)
    segments = tooth.points(num=12)
    assert len(segments) == 5
    assert _segments_connected(segments)
    points = _stack(segments)
    assert _is_symmetric_about_x(points)
    radii = _radii(segments)
    assert radii.min() == pytest.approx(tooth.df / 2, rel=1e-9)
    assert radii.max() == pytest.approx(tooth.da / 2, rel=1e-9)
    assert np.all(np.isfinite(points))


def test_backlash_rotates_involute_by_half_the_angular_amount():
    plain = InvoluteTooth(backlash=0.0)
    with_backlash = InvoluteTooth(backlash=0.5)
    assert with_backlash.angular_backlash == pytest.approx(0.5 / (with_backlash.d / 2))
    p0 = plain.involute_points(num=6)[0]
    p1 = with_backlash.involute_points(num=6)[0]
    delta = np.arctan2(p1[1], p1[0]) - np.arctan2(p0[1], p0[0])
    assert delta == pytest.approx(with_backlash.angular_backlash / 2, rel=1e-9)


def test_properties_from_tool_uses_transverse_module_and_pressure_angle():
    beta = np.deg2rad(20.0)
    from_tool = InvoluteTooth(beta=beta, properties_from_tool=True)
    transverse = InvoluteTooth(beta=beta, properties_from_tool=False)
    assert from_tool.m == pytest.approx(from_tool.m_n / np.cos(beta))
    assert from_tool.pressure_angle_t == pytest.approx(
        np.arctan(np.tan(from_tool.pressure_angle) / np.cos(beta))
    )
    assert transverse.m == pytest.approx(transverse.m_n)
    assert transverse.pressure_angle_t == pytest.approx(transverse.pressure_angle)
    assert from_tool.d > transverse.d
    # rot2 uses x*cos(β)*tan(αt) which equals x*tan(α) for the tool-system αt
    assert from_tool.involute_rot2 == pytest.approx(transverse.involute_rot2)


def test_head_and_shift_change_tip_and_root_diameters():
    base = InvoluteTooth(shift=0.0, head=0.0)
    shifted = InvoluteTooth(shift=0.4, head=0.2)
    assert shifted.da > base.da
    assert shifted.df > base.df


def test_update_recomputes_factors_and_backfills_properties_from_tool():
    tooth = InvoluteTooth()
    tooth.num_teeth = 21
    tooth.m_n = 2.0
    tooth.shift = 0.1
    del tooth.properties_from_tool
    tooth._update()
    assert tooth.properties_from_tool is True
    assert tooth.d == pytest.approx(21 * tooth.m)


def test_involute_end_matches_tip_radius():
    tooth = InvoluteTooth()
    # r(φ) = rb * sqrt(1+φ²) equals da/2 at involute_end
    rb = tooth.dg / 2
    assert rb * np.sqrt(1.0 + tooth.involute_end**2) == pytest.approx(tooth.da / 2)


@pytest.mark.parametrize(
    "num_teeth,module,pressure_deg,shift",
    [
        (12, 1.0, 20.0, 0.0),
        (18, 2.5, 14.5, 0.3),
        (30, 1.5, 25.0, -0.2),
        (8, 4.0, 20.0, 0.5),
    ],
)
def test_points_stay_finite_for_typical_parameters(
    num_teeth, module, pressure_deg, shift
):
    tooth = InvoluteTooth(
        m=module,
        num_teeth=num_teeth,
        pressure_angle=np.deg2rad(pressure_deg),
        shift=shift,
    )
    points = _stack(tooth.points(num=8))
    assert np.all(np.isfinite(points))
    radii = np.linalg.norm(points, axis=1)
    assert radii.max() == pytest.approx(tooth.da / 2, rel=1e-6)
    assert radii.min() >= tooth.df / 2 - 1e-9


# ---------------------------------------------------------------------------
# rack
# ---------------------------------------------------------------------------


def test_rack_compute_properties_plain_and_from_tool():
    rack = InvoluteRack()
    module, module_n, pitch, pressure_angle_t = rack.compute_properties()
    assert module == module_n == rack.m
    assert pitch == pytest.approx(rack.m * np.pi)
    assert pressure_angle_t == pytest.approx(rack.pressure_angle)

    helical = InvoluteRack(beta=np.deg2rad(20.0), properties_from_tool=True)
    module, module_n, pitch, pressure_angle_t = helical.compute_properties()
    assert module_n == helical.m
    assert module == pytest.approx(helical.m / np.cos(helical.beta))
    assert pressure_angle_t == pytest.approx(
        np.arctan(np.tan(helical.pressure_angle) / np.cos(helical.beta))
    )
    assert pitch == pytest.approx(module * np.pi)


def test_rack_points_form_closed_polygon():
    rack = InvoluteRack(num_teeth=6, add_endings=False)
    points = rack.points()
    assert points.ndim == 2 and points.shape[1] == 2
    assert_allclose(points[0], points[-1])
    assert np.all(np.isfinite(points))
    # thickness is applied to the first and last vertices (x reduced)
    assert points[0, 0] == pytest.approx(points[1, 0] - rack.thickness)


def test_rack_teeth_are_spaced_by_pitch():
    rack = InvoluteRack(num_teeth=4, add_endings=False, simplified=False)
    _module, _module_n, pitch, _alpha = rack.compute_properties()
    points = rack.points()
    # each tooth is 4 vertices; a leading copy of the first vertex is prepended
    first_addendum = points[2]
    next_addendum = points[2 + 4]
    assert next_addendum[0] == pytest.approx(first_addendum[0])
    assert next_addendum[1] == pytest.approx(first_addendum[1] + pitch)


def test_rack_simplified_omits_middle_teeth():
    full = InvoluteRack(num_teeth=15, simplified=False, add_endings=False).points()
    simple = InvoluteRack(num_teeth=15, simplified=True, add_endings=False).points()
    assert simple.shape[0] < full.shape[0]


def test_rack_add_endings_keeps_closed_profile():
    with_endings = InvoluteRack(num_teeth=5, add_endings=True).points()
    without = InvoluteRack(num_teeth=5, add_endings=False).points()
    assert_allclose(with_endings[0], with_endings[-1])
    assert_allclose(without[0], without[-1])
    assert with_endings.shape[0] >= without.shape[0]


def test_rack_update_backfills_legacy_attributes():
    rack = InvoluteRack()
    del rack.add_endings
    del rack.simplified
    rack._update()
    assert rack.add_endings is True
    assert rack.simplified is False
