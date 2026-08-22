#!/usr/bin/env python3
"""Run visual pytest under xvfb with a Coin/Qt-safe GL stack.

Collect only tests/test_visual_projects.py. Collecting tests/ also imports
workbench modules (freecad.gears.commands → FreeCADGui) and Coin then
segfaults in View3DInventorViewer::renderScene when the first document opens.

Also force X11/GLX software rendering so Wayland env vars cannot leak into xvfb.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = PROJECT_ROOT / ".pytest_exitstatus"

# Force X11/GLX software rendering before QApplication / Coin start.
for key in ("WAYLAND_DISPLAY", "QT_WAYLAND_SHELL_INTEGRATION"):
    os.environ.pop(key, None)
os.environ["XDG_SESSION_TYPE"] = "x11"
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.setdefault("QT_XCB_GL_INTEGRATION", "xcb_glx")
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")


def main() -> int:
    extra = sys.argv[1:]
    if STATUS_FILE.exists():
        try:
            STATUS_FILE.unlink()
        except OSError:
            pass

    result = subprocess.run(
        [
            "xvfb-run",
            "-a",
            "-s",
            "-screen 0 1920x1080x24 +extension GLX +render -noreset",
            "pytest",
            "tests/test_visual_projects.py",
            "-v",
            "-s",
            *extra,
        ],
        cwd=PROJECT_ROOT,
        env=os.environ,
    )

    saved = None
    if STATUS_FILE.exists():
        try:
            saved = int(STATUS_FILE.read_text().strip())
        except (ValueError, OSError):
            pass

    if result.returncode == 0:
        return 0
    if saved is not None:
        return 0 if saved == 0 else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
