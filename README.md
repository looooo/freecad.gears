# FreeCAD Gears

A gear workbench for FreeCAD: create involute, cycloid, bevel, worm, timing, lantern and crown gears with full control over parameters.

## Requirements

- **FreeCAD** ≥ 1.0 (or ≥ 0.16 for older setups)
- **Python** ≥ 3.8 (used by FreeCAD)
- **Python packages:** `numpy`, `scipy`, `sympy` (optional: `jupyter`, `matplotlib`)

## Supported gear types

### Cylindric involute
- Shifting, helical, double helical, undercut, fillets

![involute-gear](examples/images/involute-double-helical-gear.png)

### Involute rack
![involute-rack](examples/images/involute-rack.png)

### Cylindric cycloid
- Helical, double helical, fillets

![cycloid-gear](examples/images/cycloid-gear.png)

### Cycloid rack
![cycloid-rack](examples/images/cycloid-rack.png)

### Spherical involute bevel gear
- Spiral

![bevel-gear](examples/images/bevel-gear.png)

### Crown gear
![crown-gear](examples/images/crown-gear.png)

### Worm gear
![worm-gear](examples/images/worm-gear.png)

### Timing gear
![timing-gear](examples/images/timing-gear.png)

### Lantern gear
![lantern-gear](examples/images/lantern-gear.png)

---

## Installation

### Addon Manager (recommended)
In FreeCAD: **Tools** → **Addon Manager** → search for “Gears” (or “FCGear”) → Install.

### pip
```bash
pip install freecad.gears
```
Or from source:
```bash
pip install https://github.com/looooo/freecad.gears/archive/master.tar.gz
```
Use the same Python/pip that FreeCAD uses on your system.

---

## Usage

### In FreeCAD
1. Open FreeCAD and switch to the **Gear** workbench.
2. **File** → **New** (or open a document).
3. Create a gear from the toolbar and adjust parameters in the property panel.

### From Python
```python
import FreeCAD as App
import freecad.gears.commands

gear = freecad.gears.commands.CreateInvoluteGear.create()
gear.num_teeth = 20
gear.beta = 20
gear.height = 10
gear.double_helix = True
App.ActiveDocument.recompute()
Gui.SendMsgToActiveView("ViewFit")
```

---

## Development

The project uses [pixi](https://pixi.sh/) for environment and task management.

### Setup
```bash
pixi install
```

### Pixi commands


### Tasks (Kurzreferenz)

| Befehl | Beschreibung |
|--------|--------------|
| `pixi run freecad` | FreeCAD mit freecad.gears starten. |
| `pixi run lint` | Pylint. |
| `pixi run test` | Unit-Tests. |
| `pixi run test-visual` | Visual-Tests (Display nötig). |
| `pixi run test-visual-xvfb` | Visual-Tests unter xvfb. |
| `pixi run test-all` | Alle Tests. |
| `pixi run create-references` | Referenzbilder erzeugen. |
| `pixi run create-references-xvfb` | Referenzbilder unter xvfb. |
| `pixi run clean-test` | Test-Artefakte und Referenzen löschen. |

Visual tests use [freecad.visual_tests](https://github.com/looooo/freecad.visual_tests): each project under `tests/data/*/` has a `metafile.yaml` and a `.FCStd` model; references are stored in `references/`.

### CI (GitHub Actions)
- **Pylint:** Runs on push, pull_request and `workflow_dispatch` (lint does not fail the job).
- **Tests:** Unit tests on all OS; visual tests (xvfb) on Ubuntu only.
- **Update reference images:** Manual workflow “Update reference images” to regenerate references on CI and push them to the repo.

---

## References

- Elements of Metric Gear Technology ([PDF](http://qtcgears.com/tools/catalogs/PDF_Q420/Tech.pdf))

### FreeCAD Forum
- [Involute gear generator preview](https://forum.freecadweb.org/viewtopic.php?f=10&t=4829)
- [Bevel gear – module/script/tutorial](https://forum.freecadweb.org/viewtopic.php?f=3&t=12878)
- [Gears in FreeCAD: FC Gear](https://forum.freecadweb.org/viewtopic.php?f=24&t=27381)
- [FC Gears: Feedback thread](https://forum.freecadweb.org/viewtopic.php?f=8&t=27626)

Please check the [issue tracker](https://github.com/looooo/freecad.gears/issues) before opening a new report.

---

## License

GNU General Public License v3.0
