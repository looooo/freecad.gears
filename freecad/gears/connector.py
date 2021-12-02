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

from pygears import __version__
import os

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

    def claimChildren(self):
    	return [self.vobj.Object.master_gear, self.vobj.Object.slave_gear]

    def __getstate__(self):
        return {"icon_fn": self.icon_fn}

    def __setstate__(self, state):
        self.icon_fn = state["icon_fn"]


class GearConnector(object):
    def __init__(self, obj, master_gear, slave_gear):
        obj.addProperty("App::PropertyString", "version", "version", "freecad.gears-version", 1)
        obj.addProperty("App::PropertyLink","master_gear","gear","master gear", 1)
        obj.addProperty("App::PropertyLink","slave_gear","gear","slave gear", 1)
        obj.version = __version__
        obj.master_gear = master_gear
        obj.slave_gear = slave_gear

    def execute(self, fp):
    	pass