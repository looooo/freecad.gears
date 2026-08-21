# -*- coding: utf-8 -*-
"""Shared fixtures for FreeCAD workbench tests (headless)."""

import pytest

from freecad import app


@pytest.fixture
def doc(request):
    """Temporary FreeCAD document, closed after the test."""
    raw = "wb_" + request.node.name
    name = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in raw)[:50]
    document = app.newDocument(name)
    try:
        yield document
    finally:
        try:
            app.closeDocument(document.Name)
        except Exception:
            pass


@pytest.fixture
def headless_viewprovider():
    """Allow GearConnector ViewProviders to construct without a GUI ViewObject."""
    from freecad.gears.connector import ViewProviderGearConnector

    original = ViewProviderGearConnector.__init__

    def _init(self, vobj, icon_fn=None):
        if vobj is None:
            self.icon_fn = icon_fn or ""
            return None
        return original(self, vobj, icon_fn)

    ViewProviderGearConnector.__init__ = _init
    try:
        yield
    finally:
        ViewProviderGearConnector.__init__ = original
