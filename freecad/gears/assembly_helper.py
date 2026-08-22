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

"""Optional helpers for the FreeCAD Assembly workbench."""

from freecad import app
from freecad import part

JOINT_PREFIX = "FCGear_"


def assembly_workbench_available():
    """Return True if the Assembly workbench Python modules can be imported."""
    try:
        import Assembly  # pylint: disable=unused-import
        import UtilsAssembly  # pylint: disable=unused-import
        import JointObject  # pylint: disable=unused-import

        return True
    except ImportError:
        return False


def create_assembly_container(doc, label="PlanetaryAssembly"):
    """Create a new Assembly object when the workbench is available.

    Every call yields its own container so that a second gear set never ends
    up inside the assembly of the first one.
    """
    if not assembly_workbench_available():
        return None

    asm = doc.addObject("Assembly::AssemblyObject", label)
    asm.Label = label
    return asm


def _assembly_children(assembly):
    if hasattr(assembly, "Group"):
        return assembly.Group
    return []


def remove_component_links(assembly):
    """Remove legacy App::Link children from an assembly."""
    if assembly is None:
        return
    doc = assembly.Document
    for child in list(_assembly_children(assembly)):
        if child.isDerivedFrom("App::Link"):
            doc.removeObject(child.Name)


def _joint_group(assembly):
    import UtilsAssembly

    return UtilsAssembly.getJointGroup(assembly)


def clear_planetary_joints(assembly):
    """Remove assembly joints created by the planetary gear tool."""
    if assembly is None or not assembly_workbench_available():
        return

    doc = assembly.Document
    for joint in list(_joint_group(assembly).Group):
        if joint.Name.startswith(JOINT_PREFIX):
            doc.removeObject(joint.Name)


def carrier_shape(orbit_angles, sun_planet_distance, height):
    """Build a spider carrier that sits underneath the gear stack.

    The shape is modelled in the carrier's own coordinate system with its
    rotation axis on the global z axis, so that the carrier placement stays a
    pure rotation and can be used directly as a joint coordinate system.
    """
    thickness = max(height * 0.2, 1.0)
    z_base = -(thickness + max(height * 0.1, 0.5))
    arm_radius = max(sun_planet_distance * 0.1, 1.0)
    hub_radius = max(sun_planet_distance * 0.25, arm_radius)

    shape = part.makeCylinder(hub_radius, thickness, app.Vector(0, 0, z_base))
    for angle in orbit_angles:
        direction = app.Rotation(app.Vector(0, 0, 1), angle).multVec(
            app.Vector(sun_planet_distance, 0, 0)
        )
        arm = part.makeBox(
            sun_planet_distance,
            2 * arm_radius,
            thickness,
            app.Vector(0, -arm_radius, z_base),
        )
        arm.rotate(app.Vector(0, 0, 0), app.Vector(0, 0, 1), angle)
        boss = part.makeCylinder(
            arm_radius, thickness, app.Vector(direction.x, direction.y, z_base)
        )
        shape = shape.fuse(arm).fuse(boss)
    return shape.removeSplitter()


def create_carrier(assembly, existing, orbit_angles, sun_planet_distance, height):
    """Create or update the planet carrier inside the assembly."""
    carrier = existing
    if carrier is None or carrier.Document is not assembly.Document:
        carrier = assembly.newObject("Part::Feature", JOINT_PREFIX + "Carrier")
        carrier.Label = "Carrier"

    carrier.Shape = carrier_shape(orbit_angles, sun_planet_distance, height)
    return carrier


def _create_joint(joint_group, name, joint_type, ref1, ref2):
    import JointObject

    joint = joint_group.newObject("App::FeaturePython", name)
    JointObject.Joint(joint, JointObject.JointTypes.index(joint_type))
    if app.GuiUp:
        JointObject.ViewProviderJoint(joint.ViewObject)
    # An empty element and vertex name makes the joint use the placement of the
    # referenced object. Both entries are required, the Assembly workbench
    # always expects a pair.
    joint.Reference1 = (ref1, ["", ""])
    joint.Reference2 = (ref2, ["", ""])
    return joint


def _create_revolute_joint(joint_group, name, ref1, ref2, offset1=None):
    joint = _create_joint(joint_group, name, "Revolute", ref1, ref2)
    if offset1 is not None:
        joint.Offset1 = offset1
    return joint


def _create_mesh_joint(joint_group, name, ref1, ref2, radius1, radius2, internal):
    # An external mesh reverses the direction of rotation ("Gears"), an
    # internal mesh keeps it ("Belt").
    joint = _create_joint(
        joint_group, name, "Belt" if internal else "Gears", ref1, ref2
    )
    joint.Distance = f"{radius1:.6g} mm"
    joint.Distance2 = f"{radius2:.6g} mm"
    return joint


def setup_planetary_constraints(
    assembly,
    ring_gear,
    sun_gear,
    carrier,
    planet_gears,
    module,
    z_sun,
    z_planet,
    z_ring,
    orbit_angles,
    sun_planet_distance,
):
    """Create grounded, revolute, and mesh joints for a planetary set.

    The ring gear is grounded, sun and carrier turn about the global z axis,
    and every planet turns about an axis carried by the carrier. Each planet
    meshes with the sun through a gears joint and with the ring through a belt
    joint, because an internal mesh does not reverse the rotation direction.
    """
    if assembly is None or not assembly_workbench_available():
        return

    import JointObject

    clear_planetary_joints(assembly)
    remove_component_links(assembly)

    joint_group = _joint_group(assembly)
    pitch_r_sun = module * z_sun / 2.0
    pitch_r_planet = module * z_planet / 2.0
    pitch_r_ring = module * z_ring / 2.0

    ground = joint_group.newObject("App::FeaturePython", JOINT_PREFIX + "GroundRing")
    JointObject.GroundedJoint(ground, ring_gear)
    if app.GuiUp:
        JointObject.ViewProviderGroundedJoint(ground.ViewObject)

    _create_revolute_joint(
        joint_group,
        JOINT_PREFIX + "RevoluteCarrier",
        ring_gear,
        carrier,
    )
    _create_revolute_joint(
        joint_group,
        JOINT_PREFIX + "RevoluteSun",
        ring_gear,
        sun_gear,
    )

    for index, planet in enumerate(planet_gears):
        orbit_angle = orbit_angles[index]
        axis = app.Rotation(app.Vector(0, 0, 1), orbit_angle).multVec(
            app.Vector(sun_planet_distance, 0, 0)
        )
        suffix = f"{index + 1:02d}"
        _create_revolute_joint(
            joint_group,
            JOINT_PREFIX + f"RevolutePlanet{suffix}",
            carrier,
            planet,
            offset1=app.Placement(axis, app.Rotation()),
        )
        _create_mesh_joint(
            joint_group,
            JOINT_PREFIX + f"MeshSunPlanet{suffix}",
            sun_gear,
            planet,
            pitch_r_sun,
            pitch_r_planet,
            internal=False,
        )
        _create_mesh_joint(
            joint_group,
            JOINT_PREFIX + f"MeshPlanetRing{suffix}",
            planet,
            ring_gear,
            pitch_r_planet,
            pitch_r_ring,
            internal=True,
        )


def warn_if_no_assembly():
    """Print a console warning when Assembly WB is not available."""
    app.Console.PrintWarning(
        "FCGear PlanetaryGear: Assembly workbench not available. "
        "Gears were positioned with Placement only.\n"
    )
