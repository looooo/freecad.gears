# -*- coding: utf-8 -*-
# ***************************************************************************
# *                                                                         *
# * This program is free software: you can redistribute it and/or modify    *
# * it under the terms of the GNU General Public License as published by    *
# * the Free Software Foundation, either version 3 of the License, or       *
# * (at your option) any later version.                                     *
# *                                                                         *
# * This program is distributed in the hope that it will be useful,         *
# * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           *
# * GNU General Public License for more details.                            *
# *                                                                         *
# * You should have received a copy of the GNU General Public License       *
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.   *
# *                                                                         *
# ***************************************************************************

"""Live 2D preview of a planetary gear set, drawn with Coin3D.

The outlines come straight from ``pygears``, which is pure numpy, so a full
set is generated in a few milliseconds and can follow every keystroke in the
task panel. Building the real Part shapes would take orders of magnitude
longer, which is why the preview never touches OCC.

``build_outlines`` is kept free of any Coin or FreeCAD import so the geometry
can be verified without a running GUI.
"""

import numpy as np

from freecad import app

from pygears._functions import rotation
from pygears.computation import compute_planetary_gears, planetary_phase_angles
from pygears.profile import InvoluteProfile

from .planetarygear import (
    DEFAULT_CLEARANCE,
    DEFAULT_HEAD,
    DEFAULT_HEAD_RING,
    DEFAULT_RING_THICKNESS,
)

# Points per involute flank. The gears are only a few hundred pixels wide while
# the panel is open, so a coarse sampling is indistinguishable from the final
# geometry and keeps a redraw well under the debounce interval.
PREVIEW_POINTS = 6

CIRCLE_SEGMENTS = 160

# Same palette as the toolbar icon: gears in amber, planets in red.
RING_COLOR = (1.00, 0.80, 0.20)
SUN_COLOR = (1.00, 0.80, 0.20)
PLANET_COLOR = (0.92, 0.22, 0.16)
GUIDE_COLOR = (0.45, 0.55, 0.70)


def _circle(radius, segments=CIRCLE_SEGMENTS):
    angles = np.linspace(0.0, 2.0 * np.pi, segments + 1)
    return np.stack([radius * np.cos(angles), radius * np.sin(angles)], axis=1)


def _profile(module, alpha, num_teeth, shift, head, clearance, backlash, numpoints):
    """Return the closed 2D outline of one gear and its pitch radius."""
    gear = InvoluteProfile(
        m=module,
        num_teeth=num_teeth,
        pressure_angle=alpha,
        shift=shift,
        clearance=clearance,
        backlash=backlash,
        head=head,
        beta=0.0,
        undercut=False,
    )
    gear._update()
    return gear.profile(num=numpoints), gear.dw / 2.0


def build_outlines(
    module=1.0,
    pressure_angle=20.0,
    z_sun=24,
    z_planet=18,
    num_planets=3,
    shift_sun=0.0,
    shift_planet=0.0,
    shift_ring=0.0,
    ring_thickness=DEFAULT_RING_THICKNESS,
    backlash=0.0,
    clearance=DEFAULT_CLEARANCE,
    head=DEFAULT_HEAD,
    head_ring=DEFAULT_HEAD_RING,
    carrier_angle=0.0,
    numpoints=PREVIEW_POINTS,
):
    """Return the polylines of a planetary set, ready to be drawn.

    Angles are in degrees. The tooth phases come from the same
    ``planetary_phase_angles`` used to place the real gears, so the preview
    shows the exact mesh that will be created.

    Returns:
        dict: Lists of ``(N, 2)`` arrays under the keys ``ring``, ``sun``,
            ``planets`` and ``guides``, plus the ``result`` dict of
            ``compute_planetary_gears``.
    """
    alpha = np.deg2rad(pressure_angle)
    result = compute_planetary_gears(
        module,
        alpha,
        z_sun,
        z_planet,
        num_planets,
        shift_sun,
        shift_planet,
        shift_ring,
        head,
    )
    z_ring = result["z_ring"]
    distance = result["sun_planet_distance"]
    phases = planetary_phase_angles(
        z_sun, z_planet, z_ring, result["orbit_angles"], carrier_angle
    )

    sun, _ = _profile(
        module, alpha, z_sun, shift_sun, head, clearance, backlash, numpoints
    )
    planet, _ = _profile(
        module, alpha, z_planet, shift_planet, head, clearance, backlash, numpoints
    )
    # An internal gear is the same tooth turned inside out: head and clearance
    # swap roles and the backlash changes sign, exactly as InternalInvoluteGear
    # does before it extrudes.
    ring, ring_pitch_radius = _profile(
        module, alpha, z_ring, shift_ring, clearance, head_ring, -backlash, numpoints
    )

    outlines = {
        "ring": [
            rotation(np.deg2rad(phases["ring_angle"]))(ring),
            _circle(ring_pitch_radius + ring_thickness),
        ],
        "sun": [rotation(np.deg2rad(phases["sun_angle"]))(sun)],
        "planets": [],
        "guides": [_circle(distance)],
        "result": result,
    }

    for orbit, spin in zip(phases["planet_orbits"], phases["planet_angles"]):
        angle = np.deg2rad(orbit)
        center = np.array([distance * np.cos(angle), distance * np.sin(angle)])
        outlines["planets"].append(
            rotation(np.deg2rad(spin))(planet) + center
        )

    return outlines


class PlanetaryPreview:
    """Holds the preview scenegraph and keeps it in sync with the task panel."""

    def __init__(self):
        self._root = None
        self._content = None
        self._scenegraph = None
        self._view = None
        self._framed = False

    @property
    def attached(self):
        return self._root is not None

    def _attach(self):
        """Hook an empty preview node into the active 3D view."""
        if self._root is not None:
            return True
        if not app.GuiUp:
            return False
        try:
            from pivy import coin
            from freecad import gui
        except ImportError:
            return False

        # Headless and non-3D views reach here too, so nothing may be assumed
        # about the module or the view beyond its name.
        document = getattr(gui, "ActiveDocument", None)
        view = getattr(document, "ActiveView", None)
        if view is None or not hasattr(view, "getSceneGraph"):
            return False

        root = coin.SoSeparator()
        root.setName("FCGearPlanetaryPreview")

        # The preview is a drawing aid, so it must never swallow mouse picks
        # or be shaded by the scene lights.
        pick = coin.SoPickStyle()
        pick.style = coin.SoPickStyle.UNPICKABLE
        root.addChild(pick)
        light = coin.SoLightModel()
        light.model = coin.SoLightModel.BASE_COLOR
        root.addChild(light)

        self._content = coin.SoSeparator()
        root.addChild(self._content)

        self._scenegraph = view.getSceneGraph()
        self._scenegraph.addChild(root)
        self._root = root
        self._view = view
        return True

    def _add_group(self, outlines, color, width):
        from pivy import coin

        if not outlines:
            return
        vertices = []
        counts = []
        for points in outlines:
            vertices.extend((float(x), float(y), 0.0) for x, y in points)
            counts.append(len(points))

        separator = coin.SoSeparator()
        base = coin.SoBaseColor()
        base.rgb = color
        style = coin.SoDrawStyle()
        style.lineWidth = width
        coords = coin.SoCoordinate3()
        coords.point.setValues(0, len(vertices), vertices)
        lines = coin.SoLineSet()
        lines.numVertices.setValues(0, len(counts), counts)

        for node in (base, style, coords, lines):
            separator.addChild(node)
        self._content.addChild(separator)

    def update(self, **parameters):
        """Redraw the preview for the given parameters.

        Returns ``True`` when something was drawn. A configuration that cannot
        be turned into geometry clears the preview instead of raising, because
        the user is typing and passes through invalid states all the time.
        """
        if not self._attach():
            return False
        try:
            outlines = build_outlines(**parameters)
        except Exception as error:
            app.Console.PrintLog(
                f"FCGear PlanetaryGear preview: {error}\n"
            )
            self.clear()
            return False

        self._content.removeAllChildren()
        self._add_group(outlines["guides"], GUIDE_COLOR, 1.0)
        self._add_group(outlines["ring"], RING_COLOR, 2.0)
        self._add_group(outlines["sun"], SUN_COLOR, 2.0)
        self._add_group(outlines["planets"], PLANET_COLOR, 2.0)
        self._frame_once()
        return True

    def _frame_once(self):
        """Look at the preview from the top, but only the first time."""
        if self._framed:
            return
        self._framed = True
        try:
            self._view.viewTop()
            self._view.fitAll()
        except Exception:
            pass

    def clear(self):
        if self._content is not None:
            self._content.removeAllChildren()

    def remove(self):
        if self._root is None:
            return
        try:
            self._scenegraph.removeChild(self._root)
        except Exception:
            pass
        self._root = None
        self._content = None
        self._scenegraph = None
        self._view = None
