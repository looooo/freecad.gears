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

import os
import sys
import numpy as np

from freecad import app

from pygears import __version__
from pygears.computation import (
    compute_planetary_gears,
    planetary_phase_angles,
    root_diameter,
)

from .assembly_helper import (
    assembly_workbench_available,
    create_assembly_container,
    create_carrier,
    setup_planetary_constraints,
    warn_if_no_assembly,
)
from .basegear import ViewProviderGear
from .involutegear import InvoluteGear
from .internalinvolutegear import InternalInvoluteGear

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP

Z_AXIS = app.Vector(0, 0, 1)

# Tolerance defaults shared by every gear of a set. The live preview reads them
# too, so that what is drawn matches the gears that will be created.
DEFAULT_CLEARANCE = 0.25
DEFAULT_HEAD = 0.0
DEFAULT_HEAD_RING = -0.4
DEFAULT_RING_THICKNESS = 5.0


def _spin(angle_deg):
    return app.Placement(app.Vector(), app.Rotation(Z_AXIS, angle_deg))


def _planet_placement(orbit_angle_deg, spin_angle_deg, center_distance):
    position = app.Rotation(Z_AXIS, orbit_angle_deg).multVec(
        app.Vector(center_distance, 0, 0)
    )
    return app.Placement(position, app.Rotation(Z_AXIS, spin_angle_deg))


class ViewProviderPlanetaryGear(object):
    def __init__(self, vobj, icon_fn=None):
        vobj.Proxy = self
        dirname = os.path.dirname(__file__)
        self.icon_fn = icon_fn or os.path.join(dirname, "icons", "planetarygear.svg")

    def attach(self, vobj):
        self.vobj = vobj

    def getIcon(self):
        return self.icon_fn

    if sys.version_info[0] == 3 and sys.version_info[1] >= 11:

        def dumps(self):
            return {"icon_fn": self.icon_fn}

        def loads(self, state):
            self.icon_fn = state["icon_fn"]
    else:

        def __getstate__(self):
            return {"icon_fn": self.icon_fn}

        def __setstate__(self, state):
            self.icon_fn = state["icon_fn"]


class PlanetaryGearAssembly(object):
    """Container that calculates, creates, and positions a planetary gear set."""

    # Changing these alters the layout or the joint set, so the whole assembly
    # has to be rebuilt.
    LAYOUT_PROPERTIES = (
        "module",
        "pressure_angle",
        "height",
        "num_planets",
        "z_sun",
        "z_planet",
        "shift_sun",
        "shift_planet",
        "shift_ring",
        "use_assembly",
    )

    # These only change the gear bodies; positions and joints stay valid.
    SHAPE_PROPERTIES = (
        "ring_thickness",
        "hole_sun",
        "hole_planets",
        "backlash",
        "clearance",
        "head",
        "head_ring",
        "head_fillet",
        "root_fillet",
        "helix_angle",
        "double_helix",
        "numpoints",
        "simple",
    )

    def _add_shared_properties(self, obj):
        """Add the properties shared by every gear of the set.

        Split out from ``__init__`` so that documents saved by an older
        version pick the properties up on restore.
        """
        definitions = [
            (
                "App::PropertyLength",
                "ring_thickness",
                "parameters",
                "Wall thickness of the ring gear rim",
                DEFAULT_RING_THICKNESS,
            ),
            (
                "App::PropertyLength",
                "hole_sun",
                "hole",
                "Bore diameter of the sun gear (0 for no bore)",
                0.0,
            ),
            (
                "App::PropertyLength",
                "hole_planets",
                "hole",
                "Bore diameter of the planet gears (0 for no bore)",
                0.0,
            ),
            (
                "App::PropertyLength",
                "backlash",
                "tolerance",
                "Backlash of every mesh",
                0.0,
            ),
            (
                "App::PropertyFloat",
                "clearance",
                "tolerance",
                "Clearance between tooth tip and root",
                DEFAULT_CLEARANCE,
            ),
            (
                "App::PropertyFloat",
                "head",
                "tolerance",
                "Addendum factor of sun and planet gears",
                DEFAULT_HEAD,
            ),
            (
                "App::PropertyFloat",
                "head_ring",
                "tolerance",
                "Addendum factor of the ring gear",
                DEFAULT_HEAD_RING,
            ),
            (
                "App::PropertyFloat",
                "head_fillet",
                "fillets",
                "Fillet radius at the tooth tip, as a fraction of the module",
                0.0,
            ),
            (
                "App::PropertyFloat",
                "root_fillet",
                "fillets",
                "Fillet radius at the tooth root, as a fraction of the module",
                0.0,
            ),
            (
                "App::PropertyAngle",
                "helix_angle",
                "helical",
                "Helix angle of every gear",
                0.0,
            ),
            (
                "App::PropertyBool",
                "double_helix",
                "helical",
                "Make every gear a herringbone gear",
                False,
            ),
            (
                "App::PropertyInteger",
                "numpoints",
                "accuracy",
                "Number of points used per involute flank",
                20,
            ),
            (
                "App::PropertyBool",
                "simple",
                "accuracy",
                "Draw simplified cylinders instead of real teeth",
                False,
            ),
        ]
        for prop_type, name, group, doc, default in definitions:
            if hasattr(obj, name):
                continue
            obj.addProperty(
                prop_type, name, group, QT_TRANSLATE_NOOP("App::Property", doc)
            )
            setattr(obj, name, default)

    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyString",
            "version",
            "version",
            QT_TRANSLATE_NOOP("App::Property", "freecad.gears-version"),
            1,
        )
        obj.addProperty(
            "App::PropertyLength",
            "module",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Module"),
        )
        obj.addProperty(
            "App::PropertyAngle",
            "pressure_angle",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Pressure angle"),
        )
        obj.addProperty(
            "App::PropertyLength",
            "height",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Gear height"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "num_planets",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Number of planet gears"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "z_sun",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Sun gear teeth"),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "z_planet",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Planet gear teeth"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "shift_sun",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Sun profile shift"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "shift_planet",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Planet profile shift"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "shift_ring",
            "parameters",
            QT_TRANSLATE_NOOP("App::Property", "Ring profile shift"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "use_assembly",
            "assembly",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Insert gears into an Assembly container and ground the ring gear",
            ),
        )
        obj.addProperty(
            "App::PropertyInteger",
            "z_ring",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "Ring gear teeth"),
            8,
        )
        obj.addProperty(
            "App::PropertyLength",
            "sun_planet_distance",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "Sun-planet centre distance"),
            8,
        )
        obj.addProperty(
            "App::PropertyFloat",
            "ratio_ring_fixed",
            "computed",
            QT_TRANSLATE_NOOP(
                "App::Property", "Ratio (carrier / sun) with ring fixed"
            ),
            8,
        )
        obj.addProperty(
            "App::PropertyString",
            "validation_message",
            "computed",
            QT_TRANSLATE_NOOP("App::Property", "Validation messages"),
            8,
        )
        obj.addProperty(
            "App::PropertyLink",
            "sun_gear",
            "gears",
            QT_TRANSLATE_NOOP("App::Property", "Sun gear"),
            8,
        )
        obj.addProperty(
            "App::PropertyLink",
            "ring_gear",
            "gears",
            QT_TRANSLATE_NOOP("App::Property", "Ring gear"),
            8,
        )
        obj.addProperty(
            "App::PropertyLinkList",
            "planet_gears",
            "gears",
            QT_TRANSLATE_NOOP("App::Property", "Planet gears"),
            8,
        )
        obj.addProperty(
            "App::PropertyLink",
            "carrier",
            "assembly",
            QT_TRANSLATE_NOOP("App::Property", "Planet carrier"),
            8,
        )
        obj.addProperty(
            "App::PropertyLink",
            "assembly",
            "assembly",
            QT_TRANSLATE_NOOP("App::Property", "Assembly container"),
            8,
        )
        obj.addProperty(
            "App::PropertyAngle",
            "carrier_angle",
            "kinematics",
            QT_TRANSLATE_NOOP("App::Property", "Carrier rotation angle"),
        )

        self._add_shared_properties(obj)

        obj.version = __version__
        obj.module = "1. mm"
        obj.pressure_angle = "20. deg"
        obj.height = "5. mm"
        obj.num_planets = 3
        obj.z_sun = 24
        obj.z_planet = 18
        obj.shift_sun = 0.0
        obj.shift_planet = 0.0
        obj.shift_ring = 0.0
        obj.use_assembly = True
        obj.carrier_angle = "0 deg"
        obj.planet_gears = []
        obj.Proxy = self
        self._building = False
        self.update_computed(obj)

    def _check_bores(self, obj):
        """Warn about bores that would eat into the tooth roots."""
        messages = []
        checks = (
            ("Sun", obj.hole_sun.Value, obj.z_sun, obj.shift_sun),
            ("Planet", obj.hole_planets.Value, obj.z_planet, obj.shift_planet),
        )
        for name, diameter, num_teeth, shift in checks:
            if diameter <= 0.0:
                continue
            root = root_diameter(
                obj.module.Value, num_teeth, shift, obj.clearance
            )
            if diameter >= root:
                messages.append(
                    f"{name} bore {diameter:.3f} reaches the root diameter "
                    f"{root:.3f}."
                )
        return messages

    def update_computed(self, obj):
        result = compute_planetary_gears(
            obj.module.Value,
            np.deg2rad(obj.pressure_angle.Value),
            obj.z_sun,
            obj.z_planet,
            obj.num_planets,
            obj.shift_sun,
            obj.shift_planet,
            obj.shift_ring,
            obj.head,
        )
        bore_messages = self._check_bores(obj)
        if bore_messages:
            result["messages"] = result["messages"] + bore_messages
            result["valid"] = False
        obj.z_ring = result["z_ring"]
        obj.sun_planet_distance = f"{result['sun_planet_distance']:.6g} mm"
        obj.ratio_ring_fixed = result["ratio_ring_fixed"]
        if result["messages"]:
            obj.validation_message = "; ".join(result["messages"])
        elif result["valid"]:
            obj.validation_message = "OK"
        else:
            obj.validation_message = "Invalid configuration"
        return result

    def _ensure_assembly(self, obj):
        if not obj.use_assembly:
            return None
        parent = obj.getParentGeoFeatureGroup()
        if parent is not None and parent.isDerivedFrom("Assembly::AssemblyObject"):
            return parent
        if obj.assembly is not None:
            return obj.assembly
        obj.assembly = create_assembly_container(
            obj.Document, obj.Label + "_Assembly"
        )
        if obj.assembly is None:
            warn_if_no_assembly()
        return obj.assembly

    def _gear_container(self, obj):
        assembly = self._ensure_assembly(obj)
        if obj.use_assembly and assembly is not None:
            return assembly
        return obj.Document

    def _gear_in_container(self, obj, gear):
        if gear is None:
            return False
        container = self._gear_container(obj)
        if container is obj.Document:
            return gear.getParentGeoFeatureGroup() is None
        return gear.getParentGeoFeatureGroup() == container

    def _discard_gear(self, doc, gear):
        if gear is None:
            return
        name = gear.Name
        doc.removeObject(name)

    def _create_gear(self, container, doc, name, gear_class, icon_name):
        if container.isDerivedFrom("Assembly::AssemblyObject"):
            obj = container.newObject("Part::FeaturePython", name)
        else:
            obj = doc.addObject("Part::FeaturePython", name)
        if app.GuiUp:
            icon = os.path.join(os.path.dirname(__file__), "icons", icon_name)
            ViewProviderGear(obj.ViewObject, icon)
        gear_class(obj)
        return obj

    def _configure_gear(
        self, obj, gear, num_teeth, shift, hole_diameter=None, helix_sign=1.0
    ):
        """Apply the shared configuration to one gear of the set.

        ``helix_sign`` flips the hand of the helix. An external mesh needs
        opposite hands, an internal mesh the same hand, so the sun runs against
        the planets while the planets and the ring run together.
        """
        gear.module = obj.module
        gear.pressure_angle = obj.pressure_angle
        gear.height = obj.height
        gear.num_teeth = num_teeth
        gear.shift = shift
        gear.backlash = obj.backlash
        gear.clearance = obj.clearance
        gear.head_fillet = obj.head_fillet
        gear.root_fillet = obj.root_fillet
        gear.helix_angle = obj.helix_angle.Value * helix_sign
        gear.double_helix = obj.double_helix
        gear.numpoints = obj.numpoints
        gear.simple = obj.simple

        if hasattr(gear, "thickness"):
            # Internal gear: the rim wall is independent of the gear height and
            # the addendum has to stay below the reference profile.
            gear.thickness = obj.ring_thickness
            gear.head = obj.head_ring
        else:
            gear.head = obj.head

        if hasattr(gear, "axle_hole"):
            diameter = 0.0 if hole_diameter is None else hole_diameter.Value
            gear.axle_hole = diameter > 0.0
            if gear.axle_hole:
                gear.axle_holesize = diameter

    def build_gears(self, obj):
        """Create sun, ring, and planet gears if they do not exist yet."""
        doc = obj.Document
        container = self._gear_container(obj)

        if obj.sun_gear is None or not self._gear_in_container(obj, obj.sun_gear):
            if obj.sun_gear is not None:
                self._discard_gear(doc, obj.sun_gear)
            obj.sun_gear = self._create_gear(
                container, doc, "SunGear", InvoluteGear, "involutegear.svg"
            )
        self._configure_gear(
            obj, obj.sun_gear, obj.z_sun, obj.shift_sun, obj.hole_sun, helix_sign=1.0
        )

        if obj.ring_gear is None or not self._gear_in_container(obj, obj.ring_gear):
            if obj.ring_gear is not None:
                self._discard_gear(doc, obj.ring_gear)
            obj.ring_gear = self._create_gear(
                container,
                doc,
                "RingGear",
                InternalInvoluteGear,
                "internalinvolutegear.svg",
            )
        self._configure_gear(
            obj, obj.ring_gear, obj.z_ring, obj.shift_ring, helix_sign=-1.0
        )

        planets = list(obj.planet_gears or [])
        valid_planets = [planet for planet in planets if self._gear_in_container(obj, planet)]
        for planet in planets:
            if planet not in valid_planets:
                self._discard_gear(doc, planet)
        planets = valid_planets

        while len(planets) < obj.num_planets:
            index = len(planets) + 1
            planet = self._create_gear(
                container,
                doc,
                f"PlanetGear{index:02d}",
                InvoluteGear,
                "involutegear.svg",
            )
            planets.append(planet)
        while len(planets) > obj.num_planets:
            extra = planets.pop()
            self._discard_gear(doc, extra)
        for planet in planets:
            self._configure_gear(
                obj,
                planet,
                obj.z_planet,
                obj.shift_planet,
                obj.hole_planets,
                helix_sign=-1.0,
            )
        obj.planet_gears = planets

    def position_gears(self, obj, result):
        """Place every gear so that all tooth flanks mesh exactly.

        The ring gear stays fixed; the carrier angle drives sun, planet orbit
        and planet spin through the exact epicyclic relations.
        """
        if obj.sun_gear is None or obj.ring_gear is None:
            return

        phases = planetary_phase_angles(
            obj.z_sun,
            obj.z_planet,
            obj.z_ring,
            result["orbit_angles"],
            obj.carrier_angle.Value,
        )
        center_distance = result["sun_planet_distance"]

        obj.ring_gear.Placement = _spin(phases["ring_angle"])
        obj.sun_gear.Placement = _spin(phases["sun_angle"])
        for planet, orbit, spin in zip(
            obj.planet_gears, phases["planet_orbits"], phases["planet_angles"]
        ):
            planet.Placement = _planet_placement(orbit, spin, center_distance)
        if obj.carrier is not None:
            obj.carrier.Placement = _spin(phases["carrier_angle"])

        for part_obj in [obj.sun_gear, obj.ring_gear, obj.carrier, *obj.planet_gears]:
            if part_obj is not None:
                part_obj.purgeTouched()

    def build_assembly(self, obj, result):
        """Create carrier and assembly joints for planetary kinematics."""
        if not obj.use_assembly:
            if obj.carrier is not None:
                obj.Document.removeObject(obj.carrier.Name)
                obj.carrier = None
            return None

        assembly = self._ensure_assembly(obj)
        if assembly is None:
            return None

        if obj.ring_gear is None or obj.sun_gear is None:
            return None

        obj.carrier = create_carrier(
            assembly,
            obj.carrier,
            result["orbit_angles"],
            result["sun_planet_distance"],
            obj.height.Value,
        )
        setup_planetary_constraints(
            assembly,
            obj.ring_gear,
            obj.sun_gear,
            obj.carrier,
            obj.planet_gears,
            obj.module.Value,
            obj.z_sun,
            obj.z_planet,
            obj.z_ring,
            result["orbit_angles"],
            result["sun_planet_distance"],
        )
        return assembly

    def rebuild(self, obj):
        result = self.update_computed(obj)
        if not result["valid"]:
            app.Console.PrintWarning(
                "FCGear PlanetaryGear: "
                + "; ".join(result["messages"])
                + "\n"
            )
        self._building = True
        try:
            self.build_gears(obj)
            obj.Document.recompute()
            assembly = self.build_assembly(obj, result)
            # Position after the joints exist so that the solver starts from
            # the exact analytic configuration instead of moving parts itself.
            self.position_gears(obj, result)
            if assembly is not None:
                assembly.solve()
        finally:
            self._building = False

    def reposition(self, obj):
        """Move the existing gears to the current carrier angle."""
        if obj.sun_gear is None or obj.ring_gear is None:
            return
        self._building = True
        try:
            self.position_gears(obj, self.update_computed(obj))
        finally:
            self._building = False

    def reconfigure(self, obj):
        """Rebuild the gear bodies without touching layout or joints."""
        if obj.sun_gear is None or obj.ring_gear is None:
            return
        result = self.update_computed(obj)
        self._building = True
        try:
            self.build_gears(obj)
            obj.Document.recompute()
            self.position_gears(obj, result)
        finally:
            self._building = False

    def onDocumentRestored(self, obj):
        # Adding the properties assigns their defaults, which must not kick off
        # a rebuild while the document is still being restored.
        self._building = True
        try:
            self._add_shared_properties(obj)
            self._add_legacy_properties(obj)
        finally:
            self._building = False

    def _add_legacy_properties(self, obj):
        if not hasattr(obj, "carrier"):
            obj.addProperty(
                "App::PropertyLink",
                "carrier",
                "assembly",
                QT_TRANSLATE_NOOP("App::Property", "Planet carrier"),
                8,
            )
        if not hasattr(obj, "carrier_angle"):
            obj.addProperty(
                "App::PropertyAngle",
                "carrier_angle",
                "kinematics",
                QT_TRANSLATE_NOOP("App::Property", "Carrier rotation angle"),
            )

    def onChanged(self, fp, prop):
        if getattr(self, "_building", False):
            return
        # While a document is loaded the properties arrive one by one, so
        # nothing may be rebuilt before onDocumentRestored has run.
        document = fp.Document
        if document is None or getattr(document, "Restoring", False):
            return
        if "Restore" in fp.State:
            return
        if prop in self.LAYOUT_PROPERTIES:
            self.rebuild(fp)
        elif prop in self.SHAPE_PROPERTIES:
            self.reconfigure(fp)
        elif prop == "carrier_angle":
            self.reposition(fp)

    def execute(self, fp):
        self.update_computed(fp)


def create_planetary_assembly(
    module="1. mm",
    pressure_angle="20. deg",
    height="5. mm",
    num_planets=3,
    z_sun=24,
    z_planet=18,
    shift_sun=0.0,
    shift_planet=0.0,
    shift_ring=0.0,
    use_assembly=True,
    label="PlanetaryGear",
    ring_thickness=None,
    hole_sun=None,
    hole_planets=None,
    backlash=None,
):
    """Create and populate a planetary gear assembly in the active document.

    The returned object is the configuration node of the set. It lives inside
    the assembly container and holds the parameters shared by all gears.
    """
    doc = app.ActiveDocument
    assembly = None
    if use_assembly and assembly_workbench_available():
        assembly = create_assembly_container(doc, label)

    if assembly is not None:
        obj = assembly.newObject("App::FeaturePython", label + "_Configuration")
        obj.Label = "Configuration"
    else:
        use_assembly = False
        obj = doc.addObject("App::FeaturePython", label)

    if app.GuiUp:
        ViewProviderPlanetaryGear(obj.ViewObject)
    proxy = PlanetaryGearAssembly(obj)
    proxy._building = True
    try:
        obj.module = module
        obj.pressure_angle = pressure_angle
        obj.height = height
        obj.num_planets = num_planets
        obj.z_sun = z_sun
        obj.z_planet = z_planet
        obj.shift_sun = shift_sun
        obj.shift_planet = shift_planet
        obj.shift_ring = shift_ring
        obj.use_assembly = use_assembly
        for name, value in (
            ("ring_thickness", ring_thickness),
            ("hole_sun", hole_sun),
            ("hole_planets", hole_planets),
            ("backlash", backlash),
        ):
            if value is not None:
                setattr(obj, name, value)
    finally:
        proxy._building = False
    proxy.rebuild(obj)
    doc.recompute()
    return obj
