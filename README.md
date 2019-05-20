# A Gear module for FreeCAD

## Requirments
FreeCAD > v0.16

# Screenshots
![gear](examples/spiral.png)
![gear1](examples/animated_spiral.gif)

## Supported gear-types

### Cylindric Involute
#### Shifting
#### Helical
#### Double Helical
#### Undercut

### Involute Rack

### Cylindric Cycloid
#### Helical
#### Double Helical

### Spherical Involute Bevel-Gear
#### Spiral

### Crown-Gear

---------------------------

## Installation

`pip install https://github.com/looooo/FCGear/archive/master.tar.gz`

## Usage

### Create a gear manually
* Open freecad
* Switch to the gear workbench
* Create new document
* Create a gear (click on a gear symbol in the toolbar)
* Change the gear parameters

## Scripted gears
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
or repot a bug please use the below threads. Please make sure that the report hasn't been reported already
by browsing this repositories issue queue.   
* "CONTINUED: involute gear generator preview !" ([thread](https://forum.freecadweb.org/viewtopic.php?f=10&t=4829))  
* "Bevel gear - module/script/tutorial" ([thread](https://forum.freecadweb.org/viewtopic.php?f=3&t=12878))  
* "Gears in FreeCAD: FC Gear" ([thread](https://forum.freecadweb.org/viewtopic.php?f=24&t=27381))  
* "FC Gears: Feedback thread" ([thread](https://forum.freecadweb.org/viewtopic.php?f=8&t=27626))  

# License
