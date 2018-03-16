A gear module for FreeCAD
---------------------------

![gear](examples/spiral.png)

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


Use only with FreeCAD version > 0.16

* install on Linux:
  * git clone https://github.com/looooo/FCGear.git
  * link or copy the folder into /freecad/Mod (sudo ln -s (path_to_FCGear) (path_to_freecad)/Mod

* install on Windows (7/8/8.1/10):
  * download ZIP-archive by clicking on button in top right corner
  * go to FreeCAD-Mod-Folder (eg.: C:\Program Files\FreeCAD 0.16\Mod\)
  * create a sub-folder called "FCGear"
  * make sure to copy files and folders EXACTLY as shown above to the just created sub-folder
  * restart FreeCAD and the workbench should appear in the pull-down menu
  * within FreeCAD you can choose "Tools > Customize > Workbenches" to enable/disable workbenches
  * as ALTERNATIVE method you can use FreeCAD-Addon-Installer macro from https://github.com/FreeCAD/FreeCAD-addons

* install on MAC (not tested):
  * Copy or unzip the FCgear-folder to the directory FreeCAD.app/Contents/Mod where FreeCAD.app is the folder where FreeCAD is installed.
  * as ALTERNATIVE method you can use FreeCAD-Addon-Installer macro from https://github.com/FreeCAD/FreeCAD-addons

* create a gear:
  * open freecad
  * go to the gear workbench
  * create new document
  * create a gear (click on gear symbol)
  * change parameters 
