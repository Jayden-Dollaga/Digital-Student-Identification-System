"""v3 HTML/pywebview interface for the Digital Student Identification System."""

# Expose the API module on the package so import paths like
# ``gui_web.api.permissions.require_permission`` resolve correctly when tests and
# runtime code use string-based attribute patching.
from . import api as api  # noqa: F401
