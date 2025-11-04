# -*- coding: utf-8 -*-
# ***************************************************************************
# * *
# * This program is free software: you can redistribute it and/or modify    *
# * it under the terms of the GNU General Public License as published by    *
# * the Free Software Foundation, either version 3 of the License, or       *
# * (at your option) any later version.                                     *
# * *
# * This program is distributed in the hope that it will be useful,         *
# * but WITHOUT ANY WARRANTY; without even the implied warranty of          *
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           *
# * GNU General Public License for more details.                            *
# * *
# * You should have received a copy of the GNU General Public License       *
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.   *
# * *
# ***************************************************************************

import os
import sys
import numpy as np

from freecad import app

from pygears import __version__
from pygears.computation import compute_shifted_gears

from .involutegear import InvoluteGear
from .internalinvolutegear import InternalInvoluteGear
from .involutegearrack import InvoluteGearRack
from .cycloidgear import CycloidGear
from .cycloidgearrack import CycloidGearRack

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP


class ViewProviderGearConnector(object):
    def __init__(self, vobj, icon_fn=None):
        # Set this object to the proxy object of the actual view provider
        vobj.Proxy = self
        dirname = os.path.dirname(__file__)
        self.icon_fn = icon_fn or os.path.join(dirname, "icons", "gearconnector.svg")

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


class GearConnector(object):
    _recomputing = False

    def __init__(self, obj, master_gear, slave_gear):
        obj.addProperty(
            "App::PropertyString",
            "version",
            "version",
            QT_TRANSLATE_NOOP("App::Property", "freecad.gears-version"),
            1,
        )
        obj.addProperty(
            "App::PropertyLink",
            "master_gear",
            "gear",
            QT_TRANSLATE_NOOP("App::Property", "master gear"),
            1,
        )
        obj.addProperty(
            "App::PropertyLink",
            "slave_gear",
            "gear",
            QT_TRANSLATE_NOOP("App::Property", "slave gear"),
            1,
        )
        obj.addProperty(
            "App::PropertyAngle",
            "angle1",
            "gear",
            QT_TRANSLATE_NOOP("App::Property", "angle at which second gear is placed"),
            0,
        )
        obj.addProperty(
            "App::PropertyAngle",
            "angle2",
            "gear",
            QT_TRANSLATE_NOOP("App::Property", "angle at which second gear is placed"),
            1,
        )
        obj.addProperty(
            "App::PropertyBool",
            "master_gear_stationary",
            "gear",
            QT_TRANSLATE_NOOP("App::Property", "master gear position is fixed (does not orbit)"),
            0,
        )
        obj.addProperty(
            "App::PropertyBool",
            "slave_gear_stationary",
            "gear",
            QT_TRANSLATE_NOOP("App::Property", "slave gear position is fixed (does not orbit)"),
            0,
        )
        obj.version = __version__
        obj.master_gear = master_gear
        obj.slave_gear = slave_gear
        obj.angle1 = 0
        obj.angle2 = 0
        obj.master_gear_stationary = True
        obj.slave_gear_stationary = True
        obj.Proxy = self
        
        # FIX 1: Attach ViewProvider to ensure visibility (fixes grey-out)
        ViewProviderGearConnector(obj.ViewObject)


    def onChanged(self, fp, prop):
        if self._recomputing:
            return
        # Guard: Check if gears are initialized
        if not hasattr(fp, 'master_gear') or not hasattr(fp, 'slave_gear'):
            return
        if fp.master_gear is None or fp.slave_gear is None:
            return

        # FIX 3: This connector is *always* driven by its angle1 property.
        # Removing the 'if prop == angle1' check ensures it runs on
        # manual changes (prop='angle1') AND on document recompute (prop=None).
        # This provides a stable position for G2, which fixes the chain.
        master_angle = fp.angle1.Value # Angle in degrees
            
        # ====================================================================
        # INVOLUTE GEAR TO INVOLUTE GEAR
        # ====================================================================
        if isinstance(fp.master_gear.Proxy, InvoluteGear) and isinstance(
            fp.slave_gear.Proxy, InvoluteGear
        ):
            angle_master = fp.master_gear.Placement.Rotation.Angle * sum(
                fp.master_gear.Placement.Rotation.Axis
            )
            dw_master = fp.master_gear.pitch_diameter.Value
            dw_slave = fp.slave_gear.pitch_diameter.Value
            dist = (dw_master + dw_slave) / 2
            if fp.master_gear.shift != 0 or fp.slave_gear.shift != 0:
                dist, alpha_w = compute_shifted_gears(
                    fp.master_gear.module,
                    np.deg2rad(fp.master_gear.pressure_angle.Value),
                    fp.master_gear.num_teeth,
                    fp.slave_gear.num_teeth,
                    fp.master_gear.shift,
                    fp.slave_gear.shift,
                )

            # Check if we have the stationary properties (for backward compatibility)
            master_stationary = getattr(fp, 'master_gear_stationary', True)
            slave_stationary = getattr(fp, 'slave_gear_stationary', False)

            if master_stationary and slave_stationary:
                # Both gears stay at their positions, only rotate in place
                slave_position = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)

                # 1. Rotate G1 (master)
                rot_master = app.Rotation(app.Vector(0, 0, 1), master_angle)
                fp.master_gear.Placement = app.Placement(fp.master_gear.Placement.Base, rot_master)
                fp.master_gear.purgeTouched()

                # 2. Calculate G2 (slave) rotation
                angle_slave = dw_master / dw_slave * master_angle
                angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
                rot_slave = app.Rotation(app.Vector(0, 0, 1), -angle_slave + angle3)
                
                # 3. Set G2's placement. This triggers the ChainConnector via Expression link.
                fp.slave_gear.Placement = app.Placement(slave_position, rot_slave)
                fp.slave_gear.purgeTouched()

            elif master_stationary and not slave_stationary:
                # Original behavior: slave gear orbits around master
                mat0 = app.Matrix()  # unity matrix
                trans = app.Vector(dist)
                mat0.move(trans)
                rot = app.Rotation(app.Vector(0, 0, 1), fp.angle1).toMatrix()
                angle2 = dw_master / dw_slave * fp.angle1.Value
                angle4 = dw_master / dw_slave * np.rad2deg(angle_master)
                rot2 = app.Rotation(app.Vector(0, 0, 1), angle2).toMatrix()
                angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
                rot3 = app.Rotation(app.Vector(0, 0, 1), angle3).toMatrix()
                rot4 = app.Rotation(app.Vector(0, 0, 1), -angle4).toMatrix()
                mat1 = rot * mat0 * rot2 * rot3 * rot4
                mat1.move(fp.master_gear.Placement.Base)
                fp.slave_gear.Placement = mat1
                fp.slave_gear.purgeTouched()

            elif not master_stationary and slave_stationary:
                # Master orbits around slave (inverse behavior)
                mat0 = app.Matrix()  # unity matrix
                trans = app.Vector(dist)
                mat0.move(trans)
                rot = app.Rotation(app.Vector(0, 0, 1), -fp.angle1).toMatrix()  # negative angle for reverse orbit
                angle2 = -dw_slave / dw_master * fp.angle1.Value  # master's rotation based on orbital motion
                angle_slave = fp.slave_gear.Placement.Rotation.Angle * sum(
                    fp.slave_gear.Placement.Rotation.Axis
                )
                angle4 = -dw_slave / dw_master * np.rad2deg(angle_slave)  # additional rotation from slave's current angle
                rot2 = app.Rotation(app.Vector(0, 0, 1), angle2).toMatrix()
                rot4 = app.Rotation(app.Vector(0, 0, 1), -angle4).toMatrix()
                mat1 = rot * mat0 * rot2 * rot4
                mat1.move(fp.slave_gear.Placement.Base)
                fp.master_gear.Placement = mat1
                fp.master_gear.purgeTouched()

            # else: both not stationary - no action needed

        if isinstance(fp.master_gear.Proxy, InternalInvoluteGear) and isinstance(
            fp.slave_gear.Proxy, InvoluteGear
        ):
            # Internal gear logic remains unchanged
            angle_master = fp.master_gear.Placement.Rotation.Angle * sum(
                fp.master_gear.Placement.Rotation.Axis
            )
            dw_master = fp.master_gear.pitch_diameter.Value
            dw_slave = fp.slave_gear.pitch_diameter.Value
            dist = (dw_master - dw_slave) / 2
            if fp.master_gear.shift != 0 or fp.slave_gear.shift != 0:
                dist, alpha_w = compute_shifted_gears(
                    fp.master_gear.module,
                    np.deg2rad(fp.master_gear.pressure_angle.Value),
                    fp.master_gear.num_teeth,
                    fp.slave_gear.num_teeth,
                    fp.master_gear.shift,
                    fp.slave_gear.shift,
                )

            master_stationary = getattr(fp, 'master_gear_stationary', True)
            slave_stationary = getattr(fp, 'slave_gear_stationary', False)

            if master_stationary and slave_stationary:
                slave_position = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)

                # Master rotates by angle1 
                rot_master = app.Rotation(app.Vector(0, 0, 1), fp.angle1.Value)
                fp.master_gear.Placement = app.Placement(fp.master_gear.Placement.Base, rot_master)
                fp.master_gear.purgeTouched()

                # Slave gets positioned at correct distance and rotates based on gear ratio 
                angle_slave = -dw_master / dw_slave * fp.angle1.Value
                angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
                rot_slave = app.Rotation(app.Vector(0, 0, 1), -angle_slave + angle3)
                fp.slave_gear.Placement = app.Placement(slave_position, rot_slave)
                fp.slave_gear.purgeTouched()

            elif master_stationary and not slave_stationary:
                mat0 = app.Matrix()  # unity matrix
                trans = app.Vector(dist)
                mat0.move(trans)
                rot = app.Rotation(app.Vector(0, 0, 1), fp.angle1).toMatrix()
                angle2 = -dw_master / dw_slave * fp.angle1.Value
                angle4 = -dw_master / dw_slave * np.rad2deg(angle_master)
                rot2 = app.Rotation(app.Vector(0, 0, 1), angle2).toMatrix()
                angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
                rot3 = app.Rotation(app.Vector(0, 0, 1), angle3).toMatrix()
                rot4 = app.Rotation(app.Vector(0, 0, 1), -angle4).toMatrix()
                mat1 = rot * mat0 * rot2 * rot3 * rot4
                mat1.move(fp.master_gear.Placement.Base)
                fp.slave_gear.Placement = mat1
                fp.slave_gear.purgeTouched()

            elif not master_stationary and slave_stationary:
                mat0 = app.Matrix()  # unity matrix
                trans = app.Vector(dist)
                mat0.move(trans)
                rot = app.Rotation(app.Vector(0, 0, 1), -fp.angle1).toMatrix()
                angle2 = -dw_slave / dw_master * fp.angle1.Value
                angle_slave = fp.slave_gear.Placement.Rotation.Angle * sum(
                    fp.slave_gear.Placement.Rotation.Axis
                )
                angle4 = -dw_slave / dw_master * np.rad2deg(angle_slave)
                rot2 = app.Rotation(app.Vector(0, 0, 1), angle2).toMatrix()
                rot4 = app.Rotation(app.Vector(0, 0, 1), -angle4).toMatrix()
                mat1 = rot * mat0 * rot2 * rot4
                mat1.move(fp.slave_gear.Placement.Base)
                fp.master_gear.Placement = mat1
                fp.master_gear.purgeTouched()

        if (
            isinstance(fp.master_gear.Proxy, InvoluteGear)
            and isinstance(fp.slave_gear.Proxy, InvoluteGearRack)
        ) or (
            isinstance(fp.master_gear.Proxy, CycloidGear)
            and isinstance(fp.slave_gear.Proxy, CycloidGearRack)
        ):
            # Rack gear logic remains unchanged
            angle_master = fp.master_gear.Placement.Rotation.Angle * sum(
                fp.master_gear.Placement.Rotation.Axis
            )
            dw_master = fp.master_gear.pitch_diameter.Value
            dw_slave = 0
            dist = -(dw_master + dw_slave) / 2
            mat0 = app.Matrix()  # unity matrix
            mat0.move(app.Vector(dist, 0, 0))
            mat1 = app.Matrix()
            mat1.move(app.Vector(0, np.deg2rad(fp.angle1.Value) * dw_master / 2, 0))
            mat2 = app.Matrix()
            mat2.move(app.Vector(0, -np.deg2rad(fp.angle2.Value) * dw_master / 2, 0))
            rot = app.Rotation(app.Vector(0, 0, 1), fp.angle1).toMatrix()
            mat3 = rot * mat2 * mat1 * mat0
            mat3.move(fp.master_gear.Placement.Base)
            fp.slave_gear.Placement = mat3
            fp.slave_gear.purgeTouched()

        if isinstance(fp.master_gear.Proxy, CycloidGear) and isinstance(
            fp.slave_gear.Proxy, CycloidGear
        ):
            # Cycloid logic remains unchanged
            angle_master = fp.master_gear.Placement.Rotation.Angle * sum(
                fp.master_gear.Placement.Rotation.Axis
            )
            dw_master = fp.master_gear.pitch_diameter.Value
            dw_slave = fp.slave_gear.pitch_diameter.Value
            dist = (dw_master + dw_slave) / 2

            master_stationary = getattr(fp, 'master_gear_stationary', True)
            slave_stationary = getattr(fp, 'slave_gear_stationary', False)

            if master_stationary and slave_stationary:
                slave_position = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)

                # Master rotates by angle1
                rot_master = app.Rotation(app.Vector(0, 0, 1), fp.angle1.Value)
                fp.master_gear.Placement = app.Placement(fp.master_gear.Placement.Base, rot_master)
                fp.master_gear.purgeTouched()

                # Slave gets positioned at correct distance and rotates based on gear ratio
                angle_slave = dw_master / dw_slave * fp.angle1.Value
                angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
                rot_slave = app.Rotation(app.Vector(0, 0, 1), -angle_slave + angle3)
                fp.slave_gear.Placement = app.Placement(slave_position, rot_slave)
                fp.slave_gear.purgeTouched()

            elif master_stationary and not slave_stationary:
                mat0 = app.Matrix()  # unity matrix
                trans = app.Vector(dist, 0, 0)
                mat0.move(trans)
                rot = app.Rotation(app.Vector(0, 0, 1), fp.angle1).toMatrix()
                angle2 = dw_master / dw_slave * fp.angle1.Value
                angle4 = dw_master / dw_slave * np.rad2deg(angle_master)
                rot2 = app.Rotation(app.Vector(0, 0, 1), angle2).toMatrix()
                angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
                rot3 = app.Rotation(app.Vector(0, 0, 1), angle3).toMatrix()
                rot4 = app.Rotation(app.Vector(0, 0, 1), -angle4).toMatrix()
                mat1 = rot * mat0 * rot2 * rot3 * rot4
                mat1.move(fp.master_gear.Placement.Base)
                fp.slave_gear.Placement = mat1
                fp.slave_gear.purgeTouched()

            elif not master_stationary and slave_stationary:
                mat0 = app.Matrix()  # unity matrix
                trans = app.Vector(dist, 0, 0)
                mat0.move(trans)
                rot = app.Rotation(app.Vector(0, 0, 1), -fp.angle1).toMatrix()
                angle2 = -dw_slave / dw_master * fp.angle1.Value  # master's rotation based on orbital motion
                angle_slave = fp.slave_gear.Placement.Rotation.Angle * sum(
                    fp.slave_gear.Placement.Rotation.Axis
                )
                angle4 = -dw_slave / dw_master * np.rad2deg(angle_slave)
                rot2 = app.Rotation(app.Vector(0, 0, 1), angle2).toMatrix()
                rot4 = app.Rotation(app.Vector(0, 0, 1), -angle4).toMatrix()
                mat1 = rot * mat0 * rot2 * rot4
                mat1.move(fp.slave_gear.Placement.Base)
                fp.master_gear.Placement = mat1
                fp.master_gear.purgeTouched()
        self._recomputing = True
        app.ActiveDocument.recompute()
        self._recomputing = False

    def execute(self, fp):
        # We pass 'angle1' here to ensure the logic runs,
        # as the 'prop' check was removed.
        self.onChanged(fp, 'angle1')

