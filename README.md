A gear module for FreeCAD > 0.16
---------------------------

![gear](examples/spiral.png)
![gear1](examples/animated_spiral.gif)

## supported gear-types:
- cylindric involute
  - shifting
  - helical
  - double helical
  - undercut

- involute rack

- cylindric cycloid
  - helical
  - double helical

- spherical involute bevel-gear
  - spiral

- crown-gear

---------------------------

## install

`pip install https://github.com/looooo/FCGear/archive/master.tar.gz`

## useage

* create a gear:
  * open freecad
  * go to the gear workbench
  * create new document
  * create a gear (click on gear symbol)
  * change parameters

## scripted gears:
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

## references:

[very good document](http://qtcgears.com/tools/catalogs/PDF_Q420/Tech.pdf)

## forum topics:
- https://forum.freecadweb.org/viewtopic.php?f=10&t=4829
- https://forum.freecadweb.org/viewtopic.php?f=3&t=12878
- https://forum.freecadweb.org/viewtopic.php?f=24&t=27381
- https://forum.freecadweb.org/viewtopic.php?f=8&t=27626
