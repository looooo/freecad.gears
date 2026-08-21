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

import math

from freecad import app
from pygears import __version__


def _parse_version(v):
    """'1.3.1' -> (1, 3, 1); ignore non-numeric suffixes."""
    parts = []
    for p in str(v).split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


# Version in which the helical profile-shift interpretation changed from the
# transverse coefficient x_t to the normal coefficient x_n. Files created with
# this version (or newer) already use the correct interpretation.
_FIX_VERSION = _parse_version(__version__)


def _helix_angle_rad(obj):
    ha = getattr(obj, "helix_angle", None)
    if ha is None:
        return 0.0
    try:
        return float(ha.Value) * math.pi / 180.0
    except (AttributeError, TypeError):
        return 0.0


def _shift_value(obj):
    try:
        return float(getattr(obj, "shift", 0.0))
    except (TypeError, ValueError):
        return 0.0


def needs_shift_migration(obj):
    """True if this gear was created with the old x_t shift interpretation.

    Only normal-system helical gears with a non-zero profile shift and a file
    version older than the fix are affected; spur gears and transverse/radial
    system gears never are.
    """
    if _parse_version(getattr(obj, "version", "0")) >= _FIX_VERSION:
        return False
    if not getattr(obj, "properties_from_tool", False):
        return False
    if abs(_shift_value(obj)) < 1e-9:
        return False
    if abs(_helix_angle_rad(obj)) < 1e-9:
        return False
    return True


def convert_shift_to_normal(obj):
    """x_n = x_t / cos(beta) keeps the transverse tooth thickness unchanged."""
    beta = _helix_angle_rad(obj)
    if abs(math.cos(beta)) < 1e-9:
        return False
    obj.shift = _shift_value(obj) / math.cos(beta)
    return True


def _prompt_convert_gui(obj):
    try:
        from PySide6 import QtWidgets
    except ImportError:
        try:
            from PySide import QtWidgets
        except ImportError:
            return False

    parent = None
    try:
        import FreeCADGui

        parent = FreeCADGui.getMainWindow()
    except Exception:
        parent = None

    box = QtWidgets.QMessageBox(parent)
    box.setModal(True)
    box.setIcon(QtWidgets.QMessageBox.Question)
    box.setWindowTitle(
        app.Qt.translate("Workbench", "Helical gear profile shift")
    )
    box.setText(
        app.Qt.translate(
            "Workbench",
            "This file was created with an older version of the Gears "
            "workbench that interpreted the profile shift of helical gears "
            "differently.",
        )
    )
    box.setInformativeText(
        app.Qt.translate(
            "Workbench",
            "For 'properties_from_tool' set to 'Yes', the parameter 'shift' "
            "is now interpreted as the normal coefficient (x_n) instead of "
            "the transverse coefficient (x_t).\n\n"
            "Convert the shift value to x_n = x_t / cos(β) to keep the tooth "
            "thickness unchanged (recommended), or keep the current value and "
            "accept the corrected tooth thickness.\n\n"
            "Please recompute the document to regenerate the gear geometry.",
        )
    )
    keep = box.addButton(
        app.Qt.translate("Workbench", "Keep current shift value"),
        QtWidgets.QMessageBox.RejectRole,
    )
    convert = box.addButton(
        app.Qt.translate("Workbench", "Convert shift (x_t → x_n)"),
        QtWidgets.QMessageBox.AcceptRole,
    )
    box.setDefaultButton(convert)
    box.exec_()
    return box.clickedButton() == convert


def _prompt_convert_cli(obj):
    beta_deg = math.degrees(_helix_angle_rad(obj))
    print(
        "\nWARNING: This file was created with an older version of the Gears "
        "workbench that interpreted the profile shift of helical gears "
        "differently."
    )
    print(
        "For 'properties_from_tool' set to 'Yes', the parameter 'shift' is "
        "now interpreted as the normal coefficient (x_n) instead of the "
        "transverse coefficient (x_t)."
    )
    print(
        "Convert the shift value to x_n = x_t / cos(β=%.3f°) to keep the "
        "tooth thickness unchanged." % beta_deg
    )
    print("Afterwards, recompute the document to regenerate the gear geometry.")
    while True:
        try:
            ans = input("Convert shift value? [Y/n]: ").strip().lower()
        except EOFError:  # non-interactive stdin: default to no conversion
            print("No input available; keeping the current shift value.")
            return False
        if ans in ("y", "yes", ""):
            return True
        if ans in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'.")


def migrate_shift(obj):
    """Offer to migrate the old x_t shift to x_n.

    Shown for GUI and command-line (headless) use alike. After the choice is
    made the file's version is bumped to the current version, which marks the
    migration as done so it is never offered again.
    """
    if not needs_shift_migration(obj):
        return
    if app.GuiUp:
        convert = _prompt_convert_gui(obj)
    else:
        convert = _prompt_convert_cli(obj)
    if convert:
        convert_shift_to_normal(obj)
    obj.version = __version__
    # The shift value (kept or converted) has a new meaning, so mark the gear
    # touched so a recompute regenerates its geometry; the user is asked to
    # recompute manually.
    try:
        obj.touch()
    except Exception:
        pass
