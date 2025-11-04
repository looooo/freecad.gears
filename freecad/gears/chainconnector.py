# -*- coding: utf-8 -*-
# ***************************************************************************
# * *
# * This file defines the ChainConnector class for stable multi-gear chains. *
# * *
# * (GNU GPL Header retained)
# * *
# ***************************************************************************

import numpy as np
from freecad import app
from pygears import __version__ # FIX: Import __version__

# Import all gear types the chain might connect
from .involutegear import InvoluteGear
from .internalinvolutegear import InternalInvoluteGear
from .cycloidgear import CycloidGear

# Reuse the standard ViewProvider from the original connector.py
from .connector import ViewProviderGearConnector, GearConnector

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP

class Chain(object):
    def __init__(self, obj, gear_list):
        obj.addProperty("App::PropertyLinkList", "gear_list", "GearChain", "list of gears in the chain")
        obj.addProperty("App::PropertyAngle", "angle", "GearChain", "angle of the first gear")
        obj.gear_list = gear_list
        obj.Proxy = self
        self.obj = obj
        ViewProviderGearConnector(obj.ViewObject)

        # Create connectors
        master_gear = gear_list[0]
        for i, slave_gear in enumerate(gear_list[1:]):
            if i == 0:
                connector = app.ActiveDocument.addObject("Part::FeaturePython", "GearConnector")
                GearConnector(connector, master_gear, slave_gear)
                connector.angle1 = self.obj.angle
                self.obj.addProperty("App::PropertyLink", "connector", "GearChain", "main connector")
                self.obj.connector = connector
            else:
                connector = app.ActiveDocument.addObject("Part::FeaturePython", "ChainConnector")
                ChainConnector(connector, self.obj.connector, slave_gear)
            master_gear = slave_gear

    def onChanged(self, fp, prop):
        if prop == 'angle':
            fp.connector.angle1 = fp.angle


class Chain(object):
    def __init__(self, obj, gear_list):
        obj.addProperty("App::PropertyLinkList", "gear_list", "GearChain", "list of gears in the chain")
        obj.addProperty("App::PropertyAngle", "angle", "GearChain", "angle of the first gear")
        obj.gear_list = gear_list
        obj.Proxy = self
        self.obj = obj
        ViewProviderGearConnector(obj.ViewObject)

        # Create connectors
        master_gear = gear_list[0]
        for i, slave_gear in enumerate(gear_list[1:]):
            if i == 0:
                connector = app.ActiveDocument.addObject("Part::FeaturePython", "GearConnector")
                GearConnector(connector, master_gear, slave_gear)
                connector.angle1 = self.obj.angle
                self.obj.addProperty("App::PropertyLink", "connector", "GearChain", "main connector")
                self.obj.connector = connector
            else:
                connector = app.ActiveDocument.addObject("Part::FeaturePython", "ChainConnector")
                ChainConnector(connector, self.obj.connector, slave_gear)
            master_gear = slave_gear

    def onChanged(self, fp, prop):
        if prop == 'angle':
            fp.connector.angle1 = fp.angle


class ChainConnector(object):
    def __init__(self, obj, master_connector, slave_gear):
        
        # --- PROPERTY DEFINITIONS ---
        obj.addProperty("App::PropertyString", "version", "version",
                        QT_TRANSLATE_NOOP("App::Property", "freecad.gears-version"), 1)
        obj.addProperty("App::PropertyLink", "input_connector", "GearChain",
                        QT_TRANSLATE_NOOP("App::Property", "Previous connector in the chain"), 1)
        obj.addProperty("App::PropertyLink", "master_gear", "GearChain",
                        QT_TRANSLATE_NOOP("App::Property", "The shared master gear (G2)"), 8) # Read-only link to G2
        obj.addProperty("App::PropertyLink", "slave_gear", "GearChain",
                        QT_TRANSLATE_NOOP("App::Property", "The new slave gear (G3)"), 1)
        obj.addProperty("App::PropertyAngle", "input_gear_angle", "GearChain",
                        QT_TRANSLATE_NOOP("App::Property", "Calculated rotation angle of the shared gear (G2)"), 8)
        
        # FIX 2: Add version property assignment
        obj.version = __version__
        obj.input_connector = master_connector
        obj.slave_gear = slave_gear
        obj.Proxy = self
        
        # CRITICAL FIX: Attach the ViewProvider to ensure visibility
        ViewProviderGearConnector(obj.ViewObject)

        # 1. Link master_gear (G2) property to the slave_gear of the previous connector (GC1.slave_gear)
        obj.setExpression('master_gear', f'{master_connector.Name}.slave_gear')

        # 2. Link the input_gear_angle to G2's rotation. This triggers onChanged whenever G2 moves.
        #    We convert radians (from .Angle) to degrees for consistency, though
        #    onChanged will convert it back. Or we can just use the raw Angle.
        obj.setExpression('input_gear_angle', f'{master_connector.Name}.slave_gear.Placement.Rotation.Angle')


    def onChanged(self, fp, prop):
        # Only react when the input angle (G2's rotation) or the final slave gear (G3) link changes
        if prop not in ('input_gear_angle', 'slave_gear'):
            return

        # Ensure we have both gears before proceeding
        if fp.master_gear is None or fp.slave_gear is None:
            return

        # input_gear_angle is linked to Placement.Rotation.Angle, which is in RADIANS
        master_angle_rad = fp.input_gear_angle.Value
        master_angle_deg = np.rad2deg(master_angle_rad) # Convert to degrees
        
        dw_master = fp.master_gear.pitch_diameter.Value
        dw_slave = fp.slave_gear.pitch_diameter.Value
        
        # --- Involute Gear Pair Logic ---
        if isinstance(fp.master_gear.Proxy, InvoluteGear) and isinstance(fp.slave_gear.Proxy, InvoluteGear):
            dist = (dw_master + dw_slave) / 2
            slave_pos = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)

            # Kinematics: Calculate slave rotation (opposite direction)
            angle_slave_deg = -(dw_master / dw_slave) * master_angle_deg
            
            # Apply rotation and position to G3 (slave_gear)
            angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
            rot_slave = app.Rotation(app.Vector(0, 0, 1), angle_slave_deg + angle3)
            
            fp.slave_gear.Placement = app.Placement(slave_pos, rot_slave)
            fp.slave_gear.purgeTouched()

        # --- Internal Involute Gear Logic ---
        elif isinstance(fp.master_gear.Proxy, InternalInvoluteGear) and isinstance(fp.slave_gear.Proxy, InvoluteGear):
            dist = (dw_master - dw_slave) / 2
            slave_pos = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)
            
            # Kinematics: Calculate slave rotation (same direction)
            angle_slave_deg = (dw_master / dw_slave) * master_angle_deg
            
            angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
            rot_slave = app.Rotation(app.Vector(0, 0, 1), angle_slave_deg + angle3)
            
            fp.slave_gear.Placement = app.Placement(slave_pos, rot_slave)
            fp.slave_gear.purgeTouched()

        # --- Cycloid Gear Pair Logic ---
        elif isinstance(fp.master_gear.Proxy, CycloidGear) and isinstance(fp.slave_gear.Proxy, CycloidGear):
            dist = (dw_master + dw_slave) / 2
            slave_pos = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)

            # Kinematics: Calculate slave rotation (opposite direction)
            angle_slave_deg = -(dw_master / dw_slave) * master_angle_deg
            
            # Apply rotation and position to G3 (slave_gear)
            angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
            rot_slave = app.Rotation(app.Vector(0, 0, 1), angle_slave_deg + angle3)
            
            fp.slave_gear.Placement = app.Placement(slave_pos, rot_slave)
            fp.slave_gear.purgeTouched()

        # [Add Rack Logic here if chains need to drive racks]

    def execute(self, fp):
        # When executed, simply trigger the onChanged to use the current expression-linked value
        self.onChanged(fp, 'input_gear_angle')

class GearDev(object):
    def __init__(self, obj, gear_list):
        obj.addProperty("App::PropertyLinkList", "gear_list", "GearChain", "list of gears in the chain")
        obj.addProperty("App::PropertyAngle", "angle", "GearChain", "angle of the first gear")
        obj.gear_list = gear_list
        obj.Proxy = self
        self.obj = obj
        ViewProviderGearConnector(obj.ViewObject)

        # Create connectors
        master_gear = gear_list[0]
        for i, slave_gear in enumerate(gear_list[1:]):
            if i == 0:
                connector = app.ActiveDocument.addObject("Part::FeaturePython", "GearConnector")
                GearConnector(connector, master_gear, slave_gear)
                connector.angle1 = self.obj.angle
                self.obj.addProperty("App::PropertyLink", "connector", "GearChain", "main connector")
                self.obj.connector = connector
            else:
                connector = app.ActiveDocument.addObject("Part::FeaturePython", "ChainConnector")
                ChainConnector(connector, self.obj.connector, slave_gear)
            master_gear = slave_gear

    def onChanged(self, fp, prop):
        if prop == 'angle':
            fp.connector.angle1 = fp.angle

    def __init__(self, obj, master_connector, slave_gear):
        
        # --- PROPERTY DEFINITIONS ---
        obj.addProperty("App::PropertyString", "version", "version",
                        QT_TRANSLATE_NOOP("App::Property", "freecad.gears-version"), 1)
        obj.addProperty("App::PropertyLink", "input_connector", "GearChain",
                        QT_TRANSLATE_NOOP("App::Property", "Previous connector in the chain"), 1)
        obj.addProperty("App::PropertyLink", "master_gear", "GearChain",
                        QT_TRANSLATE_NOOP("App::Property", "The shared master gear (G2)"), 8) # Read-only link to G2
        obj.addProperty("App::PropertyLink", "slave_gear", "GearChain",
                        QT_TRANSLATE_NOOP("App::Property", "The new slave gear (G3)"), 1)
        obj.addProperty("App::PropertyAngle", "input_gear_angle", "GearChain",
                        QT_TRANSLATE_NOOP("App::Property", "Calculated rotation angle of the shared gear (G2)"), 8)
        
        # FIX 2: Add version property assignment
        obj.version = __version__
        obj.input_connector = master_connector
        obj.slave_gear = slave_gear
        obj.Proxy = self
        
        # CRITICAL FIX: Attach the ViewProvider to ensure visibility
        ViewProviderGearConnector(obj.ViewObject)

        # 1. Link master_gear (G2) property to the slave_gear of the previous connector (GC1.slave_gear)
        obj.setExpression('master_gear', f'{master_connector.Name}.slave_gear')

        # 2. Link the input_gear_angle to G2's rotation. This triggers onChanged whenever G2 moves.
        #    We convert radians (from .Angle) to degrees for consistency, though
        #    onChanged will convert it back. Or we can just use the raw Angle.
        obj.setExpression('input_gear_angle', f'{master_connector.Name}.slave_gear.Placement.Rotation.Angle')


    def onChanged(self, fp, prop):
        # Only react when the input angle (G2's rotation) or the final slave gear (G3) link changes
        if prop not in ('input_gear_angle', 'slave_gear'):
            return

        # Ensure we have both gears before proceeding
        if fp.master_gear is None or fp.slave_gear is None:
            return

        # input_gear_angle is linked to Placement.Rotation.Angle, which is in RADIANS
        master_angle_rad = fp.input_gear_angle.Value
        master_angle_deg = np.rad2deg(master_angle_rad) # Convert to degrees
        
        dw_master = fp.master_gear.pitch_diameter.Value
        dw_slave = fp.slave_gear.pitch_diameter.Value
        
        # --- Involute Gear Pair Logic ---
        if isinstance(fp.master_gear.Proxy, InvoluteGear) and isinstance(fp.slave_gear.Proxy, InvoluteGear):
            dist = (dw_master + dw_slave) / 2
            slave_pos = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)

            # Kinematics: Calculate slave rotation (opposite direction)
            angle_slave_deg = -(dw_master / dw_slave) * master_angle_deg
            
            # Apply rotation and position to G3 (slave_gear)
            angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
            rot_slave = app.Rotation(app.Vector(0, 0, 1), angle_slave_deg + angle3)
            
            fp.slave_gear.Placement = app.Placement(slave_pos, rot_slave)
            fp.slave_gear.purgeTouched()

        # --- Internal Involute Gear Logic ---
        elif isinstance(fp.master_gear.Proxy, InternalInvoluteGear) and isinstance(fp.slave_gear.Proxy, InvoluteGear):
            dist = (dw_master - dw_slave) / 2
            slave_pos = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)
            
            # Kinematics: Calculate slave rotation (same direction)
            angle_slave_deg = (dw_master / dw_slave) * master_angle_deg
            
            angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
            rot_slave = app.Rotation(app.Vector(0, 0, 1), angle_slave_deg + angle3)
            
            fp.slave_gear.Placement = app.Placement(slave_pos, rot_slave)
            fp.slave_gear.purgeTouched()

        # --- Cycloid Gear Pair Logic ---
        elif isinstance(fp.master_gear.Proxy, CycloidGear) and isinstance(fp.slave_gear.Proxy, CycloidGear):
            dist = (dw_master + dw_slave) / 2
            slave_pos = fp.master_gear.Placement.Base + app.Vector(dist, 0, 0)

            # Kinematics: Calculate slave rotation (opposite direction)
            angle_slave_deg = -(dw_master / dw_slave) * master_angle_deg
            
            # Apply rotation and position to G3 (slave_gear)
            angle3 = abs(fp.slave_gear.num_teeth % 2 - 1) * 180.0 / fp.slave_gear.num_teeth
            rot_slave = app.Rotation(app.Vector(0, 0, 1), angle_slave_deg + angle3)
            
            fp.slave_gear.Placement = app.Placement(slave_pos, rot_slave)
            fp.slave_gear.purgeTouched()

        # [Add Rack Logic here if chains need to drive racks]

    def execute(self, fp):
        # When executed, simply trigger the onChanged to use the current expression-linked value
        self.onChanged(fp, 'input_gear_angle')

