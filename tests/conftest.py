"""Stable import paths for active and archived test fixtures."""

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATHS = (
    ROOT / "python",
    ROOT / "tests" / "Prototype" / "Python",
)

for path in reversed(PATHS):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

# Never point the test suite at the normal data directory or a caller-provided
# production database by accident. Opting out is deliberately explicit:
# DSIS_TEST_USE_CONFIGURED_DATA=1. Redirect the data directory as well as the
# individual DB/export/log paths because settings_store persists settings below
# CONFIG.data_dir and otherwise could still read or mutate the developer's
# real settings.json.
if os.getenv("DSIS_TEST_USE_CONFIGURED_DATA", "").strip() != "1":
    _TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="dsis-tests-"))
    atexit.register(shutil.rmtree, _TEST_DATA_DIR, ignore_errors=True)
    os.environ["FINGERPRINT_DATA_DIR"] = str(_TEST_DATA_DIR)
    os.environ["FINGERPRINT_DB_PATH"] = str(_TEST_DATA_DIR / "attendance.db")
    os.environ["FINGERPRINT_EXPORT_FOLDER"] = str(_TEST_DATA_DIR / "exports")
    os.environ["FINGERPRINT_LOG_FOLDER"] = str(_TEST_DATA_DIR / "logs")

from core import permissions


def grant_test_session_role(role: str = "admin", action: str = "enroll", timeout_seconds: float = 600.0) -> str:
    """Set the supported in-memory session role required for privileged hardware tests."""
    permissions.set_session_role(role, timeout_seconds)
    assert permissions.require_permission(action), (
        f"Session role '{role}' lacks permission '{action}'. "
        "Use the supported permissions.set_session_role() path before calling protected commands."
    )
    return permissions.get_current_role()


@pytest.fixture(autouse=True)
def reset_session_role_to_default():
    """Ensure privileged role state does not leak from one test into another."""
    yield
    permissions.set_session_role("guest", 600.0)
