## A Gear module for FreeCAD
[![Liberapay](http://img.shields.io/liberapay/patrons/looooo.svg?logo=liberapay)](https://liberapay.com/looooo/donate) [![Total alerts](https://img.shields.io/lgtm/alerts/g/looooo/freecad.gears.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/looooo/freecad.gears/alerts/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/looooo/freecad.gears.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/looooo/freecad.gears/context:python)  

## Requirements
FreeCAD > v0.16  
__python > 3 (for python2 use branch py2)__


## Supported gear-types

### Cylindric Involute
* Shifting
* Helical
* Double Helical
* Undercut  

![involute-gear](examples/involute-double-helical-gear.png)


### Involute Rack
![involute-rack](examples/involute-rack.png)

### Cylindric Cycloid
* Helical
* Double Helical

![cycloid-gear](examples/cycloid-gear.png)

### Cycloid Rack

![cycloid-rack](examples/cycloid-rack.png)

### Spherical Involute Bevel-Gear
* Spiral  

![bevel-gear](examples/bevel-gear.png)

### Crown-Gear
![crown-gear](examples/crown-gear.png)

### Worm-Gear
![worm-gear](examples/worm-gear.png)

### Timing-Gear
![timing-gear](examples/timing-gear.png)

### Lantern-Gear
![lantern-gear](examples/lantern-gear.png)

---------------------------

## Installation

### Addon Manager  
Starting from v0.17 it's possible to use the built-in FreeCAD [Addon Manager](https://github.com/FreeCAD/FreeCAD-addons#1-builtin-addon-manager)
located in the `Tools` > `Addon Manager` dropdown menu.

### pip

`pip install https://github.com/looooo/FCGear/archive/master.tar.gz`

**Important note:** Most systems have multiple versions of python installed. Make sure the `pip` you're using is used by FreeCAD as well.

## Usage

### Create a gear manually
* Open freecad
* Switch to the gear workbench
* Create new document
* Create a gear (click on a gear symbol in the toolbar)
* Change the gear parameters

## Scripted gears
Use the power of python to automate your gear modeling: 

```python
import FreeCAD as App
import freecad.gears.commands
gear = freecad.gears.commands.CreateInvoluteGear.create()
gear.teeth = 20
gear.beta = 20
gear.height = 10
gear.double_helix = True
App.ActiveDocument.recompute()
Gui.SendMsgToActiveView("ViewFit")
```

## References
* Elements of Metric Gear Technology ([PDF](http://qtcgears.com/tools/catalogs/PDF_Q420/Tech.pdf))

### FreeCAD Forum threads
These are forum threads where FreeCAD Gears has been discussed. If you want to give Feedback
or report a bug please use the below threads. Please make sure that the report hasn't been reported already
by browsing this repositories [issue queue](https://github.com/looooo/freecad.gears/issues).   
* "CONTINUED: involute gear generator preview !" ([thread](https://forum.freecadweb.org/viewtopic.php?f=10&t=4829))  
* "Bevel gear - module/script/tutorial" ([thread](https://forum.freecadweb.org/viewtopic.php?f=3&t=12878))  
* "Gears in FreeCAD: FC Gear" ([thread](https://forum.freecadweb.org/viewtopic.php?f=24&t=27381))  
* "FC Gears: Feedback thread" ([thread](https://forum.freecadweb.org/viewtopic.php?f=8&t=27626))  

# License
GNU General Public License v3.0
