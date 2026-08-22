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

import numpy as np

from freecad import app

from pygears.computation import compute_planetary_gears, root_diameter

from .planetary_preview import PlanetaryPreview

QT_TRANSLATE_NOOP = app.Qt.QT_TRANSLATE_NOOP

ICON = os.path.join(os.path.dirname(__file__), "icons", "planetarygear.svg")


def _widgets():
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide import QtWidgets
    return QtWidgets


def _qtgui():
    try:
        from PySide6 import QtGui
    except ImportError:
        from PySide import QtGui
    return QtGui


def _qtcore():
    try:
        from PySide6 import QtCore
    except ImportError:
        from PySide import QtCore
    return QtCore


def _tr(text):
    return app.Qt.translate("FCGear_PlanetaryGear", text)


def _button_flags(*buttons):
    """Combine button flags into the plain int FreeCAD's task view expects.

    PySide6 exposes the flags as a strict ``enum.Flag`` that refuses ``int()``,
    while PySide2 hands out plain integers.
    """
    flags = buttons[0]
    for button in buttons[1:]:
        flags = flags | button
    return getattr(flags, "value", None) or int(flags)


class PlanetaryGearTaskPanel:
    """Task panel for planetary gear calculation and creation.

    The panel follows FreeCAD's task dialog protocol, so it is shown through
    ``Gui.Control.showDialog`` and docked into the combo view instead of
    blocking the application with a modal window. Because ``showDialog``
    returns immediately, the panel cannot hand its result back to the caller;
    the caller passes an ``on_accept`` callback that receives the parameter
    dict once the user confirms a valid configuration.
    """

    def __init__(self, on_accept=None):
        self._on_accept = on_accept
        QtWidgets = _widgets()

        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle(_tr("Planetary Gear Assembly"))
        self.form.setWindowIcon(_qtgui().QIcon(ICON))
        layout = QtWidgets.QVBoxLayout(self.form)

        gears = self._group(layout, _tr("Gear data"))
        self.module = self._length(gears, _tr("Module"), 1.0, minimum=0.1)
        self.pressure_angle = self._number(
            gears, _tr("Pressure angle"), 20.0, 10.0, 30.0, decimals=1, suffix=" deg"
        )
        self.height = self._length(gears, _tr("Height"), 5.0, minimum=0.1)
        self.num_planets = self._integer(gears, _tr("Number of planets"), 3, 1, 12)
        self.z_sun = self._integer(gears, _tr("Sun teeth"), 24, 6, 500)
        self.z_planet = self._integer(gears, _tr("Planet teeth"), 18, 6, 500)
        self.ring_thickness = self._length(
            gears, _tr("Ring wall thickness"), 5.0, minimum=0.1
        )

        shifts = self._group(layout, _tr("Profile shift"))
        self.shift_sun = self._number(
            shifts, _tr("Sun"), 0.0, -1.0, 1.0, decimals=3, step=0.05
        )
        self.shift_planet = self._number(
            shifts, _tr("Planet"), 0.0, -1.0, 1.0, decimals=3, step=0.05
        )
        self.shift_ring = self._number(
            shifts, _tr("Ring"), 0.0, -1.0, 1.0, decimals=3, step=0.05
        )

        fits = self._group(layout, _tr("Bores and backlash"))
        self.hole_sun = self._length(fits, _tr("Sun bore"), 0.0, special=_tr("none"))
        self.hole_planets = self._length(
            fits, _tr("Planet bore"), 0.0, special=_tr("none")
        )
        self.backlash = self._number(
            fits, _tr("Backlash"), 0.0, 0.0, 10.0, decimals=3, step=0.01, suffix=" mm"
        )

        self.use_assembly = QtWidgets.QCheckBox(
            _tr("Assembly workbench with movable joints")
        )
        self.use_assembly.setChecked(True)
        layout.addWidget(self.use_assembly)

        self.show_preview = QtWidgets.QCheckBox(_tr("Live preview in the 3D view"))
        self.show_preview.setChecked(True)
        self.show_preview.toggled.connect(self._refresh_preview)
        layout.addWidget(self.show_preview)

        result = self._group(layout, _tr("Calculation"), form=False)
        self.summary = QtWidgets.QPlainTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setMinimumHeight(160)
        result.addWidget(self.summary)

        layout.addStretch(1)

        for widget in (
            self.module,
            self.pressure_angle,
            self.num_planets,
            self.z_sun,
            self.z_planet,
            self.shift_sun,
            self.shift_planet,
            self.shift_ring,
            self.hole_sun,
            self.hole_planets,
            self.ring_thickness,
            self.backlash,
        ):
            widget.valueChanged.connect(self._on_value_changed)

        # Redrawing takes a few milliseconds, but holding a spin box arrow fires
        # far faster than that, so the requests are coalesced.
        self._preview = PlanetaryPreview()
        self._preview_timer = _qtcore().QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(60)
        self._preview_timer.timeout.connect(self._draw_preview)

        self._update_summary()
        self._refresh_preview()

    def _group(self, layout, title, form=True):
        QtWidgets = _widgets()
        box = QtWidgets.QGroupBox(title)
        inner = QtWidgets.QFormLayout(box) if form else QtWidgets.QVBoxLayout(box)
        if form:
            inner.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        layout.addWidget(box)
        return inner

    def _number(
        self,
        form,
        label,
        value,
        minimum,
        maximum,
        decimals=2,
        step=None,
        suffix="",
        special="",
    ):
        QtWidgets = _widgets()
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        if step is not None:
            spin.setSingleStep(step)
        spin.setSuffix(suffix)
        if special:
            spin.setSpecialValueText(special)
        spin.setValue(value)
        form.addRow(label, spin)
        return spin

    def _length(self, form, label, value, minimum=0.0, special=""):
        return self._number(
            form, label, value, minimum, 1000.0, decimals=3, suffix=" mm",
            special=special,
        )

    def _integer(self, form, label, value, minimum, maximum):
        QtWidgets = _widgets()
        spin = QtWidgets.QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        form.addRow(label, spin)
        return spin

    def _current_result(self):
        result = compute_planetary_gears(
            self.module.value(),
            np.deg2rad(self.pressure_angle.value()),
            self.z_sun.value(),
            self.z_planet.value(),
            self.num_planets.value(),
            self.shift_sun.value(),
            self.shift_planet.value(),
            self.shift_ring.value(),
        )
        bore_warnings = self._bore_warnings()
        if bore_warnings:
            result["messages"] = result["messages"] + bore_warnings
            result["valid"] = False
        return result

    def _bore_warnings(self):
        warnings = []
        checks = (
            ("Sun", self.hole_sun.value(), self.z_sun.value(), self.shift_sun.value()),
            (
                "Planet",
                self.hole_planets.value(),
                self.z_planet.value(),
                self.shift_planet.value(),
            ),
        )
        for name, diameter, num_teeth, shift in checks:
            if diameter <= 0.0:
                continue
            root = root_diameter(self.module.value(), num_teeth, shift)
            if diameter >= root:
                warnings.append(
                    f"{name} bore {diameter:.3f} reaches the root diameter "
                    f"{root:.3f}."
                )
        return warnings

    def _update_summary(self):
        result = self._current_result()
        spacing = ", ".join(f"{angle:.2f}" for angle in result["orbit_angles"])
        lines = [
            f"z_ring = {result['z_ring']}",
            f"Sun-planet distance = {result['sun_planet_distance']:.4f} mm",
            f"Planet-ring distance = {result['planet_ring_distance']:.4f} mm",
            f"Planet positions = {spacing} deg",
            "",
            f"Ring fixed: sun turns {result['ratio_ring_fixed']:.4f} x per carrier turn",
            f"Sun fixed: ring turns {result['ratio_sun_fixed']:.4f} x per carrier turn",
            f"Carrier fixed: sun turns {result['ratio_carrier_fixed']:.4f} x per ring turn",
            "",
        ]
        if result["valid"]:
            lines.append(_tr("Configuration is valid."))
        else:
            lines.extend(result["messages"])
        self.summary.setPlainText("\n".join(lines))

    def _on_value_changed(self):
        self._update_summary()
        self._refresh_preview()

    def _refresh_preview(self):
        if not self.show_preview.isChecked():
            self._preview.remove()
            return
        self._preview_timer.start()

    def _draw_preview(self):
        self._preview.update(
            module=self.module.value(),
            pressure_angle=self.pressure_angle.value(),
            z_sun=self.z_sun.value(),
            z_planet=self.z_planet.value(),
            num_planets=self.num_planets.value(),
            shift_sun=self.shift_sun.value(),
            shift_planet=self.shift_planet.value(),
            shift_ring=self.shift_ring.value(),
            ring_thickness=self.ring_thickness.value(),
            backlash=self.backlash.value(),
        )

    def parameters(self):
        """Return the current settings as keyword arguments for the factory."""
        return {
            "module": f"{self.module.value():.6g} mm",
            "pressure_angle": f"{self.pressure_angle.value():.6g} deg",
            "height": f"{self.height.value():.6g} mm",
            "num_planets": self.num_planets.value(),
            "z_sun": self.z_sun.value(),
            "z_planet": self.z_planet.value(),
            "shift_sun": self.shift_sun.value(),
            "shift_planet": self.shift_planet.value(),
            "shift_ring": self.shift_ring.value(),
            "use_assembly": self.use_assembly.isChecked(),
            "ring_thickness": f"{self.ring_thickness.value():.6g} mm",
            "hole_sun": f"{self.hole_sun.value():.6g} mm",
            "hole_planets": f"{self.hole_planets.value():.6g} mm",
            "backlash": f"{self.backlash.value():.6g} mm",
        }

    def getStandardButtons(self):
        QtWidgets = _widgets()
        return _button_flags(
            QtWidgets.QDialogButtonBox.Ok, QtWidgets.QDialogButtonBox.Cancel
        )

    def accept(self):
        result = self._current_result()
        if not result["valid"]:
            QtWidgets = _widgets()
            QtWidgets.QMessageBox.warning(
                self.form,
                _tr("Invalid configuration"),
                "\n".join(result["messages"]),
            )
            return False

        # Drop the preview before building, so the real gears are not drawn
        # over by their own outlines.
        self._stop_preview()

        if self._on_accept is not None:
            try:
                self._on_accept(self.parameters())
            except Exception as error:
                app.Console.PrintError(
                    f"FCGear PlanetaryGear: {error}\n"
                )
                return False

        self._close()
        return True

    def reject(self):
        self._stop_preview()
        self._close()
        return True

    def _stop_preview(self):
        self._preview_timer.stop()
        self._preview.remove()

    def _close(self):
        try:
            from freecad import gui

            gui.Control.closeDialog()
        except Exception:
            pass


def show_planetary_task_panel(on_accept=None):
    """Dock the planetary gear task panel into the combo view.

    Returns the panel, or ``None`` when another task is already open, since
    FreeCAD allows only one task dialog at a time.
    """
    from freecad import gui

    if gui.Control.activeDialog():
        QtWidgets = _widgets()
        QtWidgets.QMessageBox.warning(
            gui.getMainWindow(),
            _tr("Planetary Gear Assembly"),
            _tr("Another task is already open. Please close it first."),
        )
        return None

    panel = PlanetaryGearTaskPanel(on_accept)
    gui.Control.showDialog(panel)
    return panel
