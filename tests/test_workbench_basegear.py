# -*- coding: utf-8 -*-
"""Tests for shared geometry helpers in freecad.gears.basegear."""

import numpy as np
import pytest

from freecad import app
from freecad import part
from freecad.gears import __version__ as gears_version
from freecad.gears.basegear import (
    BaseGear,
    ViewProviderGear,
    fcvec,
    fillet_between_edges,
    helical_extrusion,
    insert_fillet,
    make_bspline_wire,
    part_arc_from_points_and_center,
    points_to_wire,
)
from pygears import __version__ as pygears_version


def test_workbench_version_matches_pygears():
    assert gears_version == pygears_version


def test_fcvec_pads_2d_and_keeps_3d():
    v2 = fcvec([1.0, 2.0])
    assert (v2.x, v2.y, v2.z) == (1.0, 2.0, 0.0)
    v3 = fcvec([1.0, 2.0, 3.0])
    assert (v3.x, v3.y, v3.z) == (1.0, 2.0, 3.0)


def test_basegear_generate_gear_shape_is_abstract(doc):
    obj = doc.addObject("Part::FeaturePython", "BareGear")
    gear = BaseGear(obj)
    with pytest.raises(NotImplementedError):
        gear.generate_gear_shape(obj)


def test_viewprovider_icon_roundtrip():
    class _DummyView:
        pass

    view = _DummyView()
    provider = ViewProviderGear(view, "custom.svg")
    assert view.Proxy is provider
    assert provider.getIcon() == "custom.svg"
    state = provider.dumps()
    restored = ViewProviderGear.__new__(ViewProviderGear)
    restored.loads(state)
    assert restored.icon_fn == "custom.svg"


def test_helical_extrusion_caps_are_horizontal():
    normal = app.Vector(0, 0, 1)
    circle = part.Circle(app.Vector(0, 0, 0), normal, 10)
    face = part.Face(part.Wire(circle.toShape()))
    height = 10.0
    solid = helical_extrusion(face, height, np.pi / 4)
    assert solid.isValid()
    assert (solid.Faces[1].normalAt(0, 0) - normal).Length == pytest.approx(0.0)
    assert (solid.Faces[2].normalAt(0, 0) + normal).Length == pytest.approx(0.0)
    assert solid.Faces[1].valueAt(0, 0)[2] == pytest.approx(height)
    assert solid.Faces[2].valueAt(0, 0)[2] == pytest.approx(0.0)
    assert solid.BoundBox.ZLength == pytest.approx(height)


def test_helical_extrusion_double_helix_is_symmetric():
    circle = part.Circle(app.Vector(0, 0, 0), app.Vector(0, 0, 1), 10)
    face = part.Face(part.Wire(circle.toShape()))
    height = 10.0
    solid = helical_extrusion(face, height, np.pi / 3, double_helix=True)
    assert solid.isValid()
    assert len(solid.Solids) == 1
    assert solid.BoundBox.ZLength == pytest.approx(height, rel=1e-6)
    assert solid.Volume == pytest.approx(np.pi * 100 * height, rel=1e-4)


def test_points_to_wire_mixes_lines_and_splines():
    wire = points_to_wire(
        [np.array([[0.0, 0.0], [1.0, 0.0]]), np.array([[1.0, 0.0], [1.5, 0.5], [1.0, 1.0]])]
    )
    assert len(wire.Edges) == 2
    assert wire.Edges[0].Length == pytest.approx(1.0)


def test_make_bspline_wire():
    wire = make_bspline_wire([np.array([[0.0, 0.0], [0.5, 0.2], [1.0, 0.0]])])
    assert len(wire.Edges) == 1
    assert wire.Length > 1.0


def test_part_arc_from_points_and_center():
    arc = part_arc_from_points_and_center(
        np.array([1.0, 0.0]), np.array([0.0, 1.0]), np.array([0.0, 0.0])
    )
    edge = arc.toShape()
    assert edge.Length == pytest.approx(np.pi / 2, rel=1e-6)


def test_fillet_between_orthogonal_edges():
    edge_1 = part.makeLine(app.Vector(0, 0, 0), app.Vector(10, 0, 0))
    edge_2 = part.makeLine(app.Vector(10, 0, 0), app.Vector(10, 10, 0))
    result = fillet_between_edges(edge_1, edge_2, 1.0)
    assert result is not None
    assert len(result) == 3
    # quarter-circle fillet of radius 1
    assert result[1].Length == pytest.approx(np.pi / 2, rel=1e-6)


def test_insert_fillet_zero_radius_keeps_placeholder():
    edge_1 = part.makeLine(app.Vector(0, 0, 0), app.Vector(5, 0, 0))
    edge_2 = part.makeLine(app.Vector(5, 0, 0), app.Vector(5, 5, 0))
    out = insert_fillet([edge_1, edge_2], 0, 0.0)
    assert len(out) == 3
    assert out[1] is None
    assert out[0].Length == pytest.approx(5.0)
    assert out[2].Length == pytest.approx(5.0)


def test_insert_fillet_rejects_impossible_radius():
    edge_1 = part.makeLine(app.Vector(0, 0, 0), app.Vector(1, 0, 0))
    edge_2 = part.makeLine(app.Vector(1, 0, 0), app.Vector(1, 1, 0))
    with pytest.raises(RuntimeError, match="fillet not possible"):
        insert_fillet([edge_1, edge_2], 0, 10.0)
