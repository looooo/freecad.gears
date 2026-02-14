"""Visual regression tests (freecad.visual_tests): one test per project in tests/data."""
from pathlib import Path

import pytest

from freecad.visual_tests import discover_projects, run_metafile_test

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(__file__).resolve().parent / "data"
PROJECT_DIRS = discover_projects(DATA_DIR)


def _write_exitstatus(value: int) -> None:
    try:
        (PROJECT_ROOT / ".pytest_exitstatus").write_text(str(value))
    except Exception:
        pass


@pytest.fixture(scope="session")
def freecad_vis_session(request):
    """One FreeCAD GUI session for the whole test run."""
    from freecad.visual_tests.visual import VisualTestSession

    session = VisualTestSession.start()
    yield session
    try:
        status = 0 if request.node.session.testsfailed == 0 else 1
        _write_exitstatus(status)
    except Exception:
        pass
    session.shutdown()


def pytest_sessionfinish(session, exitstatus):
    """Persist exit status for wrapper scripts (e.g. xvfb)."""
    _write_exitstatus(exitstatus)


@pytest.mark.visual
@pytest.mark.parametrize("project_dir", PROJECT_DIRS, ids=[d.name for d in PROJECT_DIRS])
def test_visual_project(freecad_vis_session, project_dir: Path):
    """Run metafile-driven visual test (SSIM comparison). Requires display or xvfb."""
    run_metafile_test(freecad_vis_session, project_dir)
