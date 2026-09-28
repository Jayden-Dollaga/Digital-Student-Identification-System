"""Pre-launch checks for the supported DSIS v3 runtime."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence


MINIMUM_PYTHON = (3, 11)
MAXIMUM_PYTHON_EXCLUSIVE = (3, 15)
RUNTIME_IMPORTS = (
    ("pyserial", "serial"),
    ("cryptography", "cryptography"),
    ("openpyxl", "openpyxl"),
    ("matplotlib", "matplotlib"),
    ("Pillow", "PIL"),
    ("pywebview", "webview"),
)
WEBVIEW2_RUNTIME_ID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"


@dataclass(frozen=True)
class PreflightReport:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def check_startup_preflight(
    version_info: Sequence[int],
    import_module: Callable[[str], object],
    port_lister: Callable[[], Iterable[object]],
    database_path: str | Path,
    *,
    is_windows: bool,
    webview2_available: bool,
) -> PreflightReport:
    """Check injected runtime facts without importing app modules or hardware."""
    errors = []
    warnings = []
    version = tuple(version_info[:2])

    if not MINIMUM_PYTHON <= version < MAXIMUM_PYTHON_EXCLUSIVE:
        errors.append(
            "Unsupported Python version "
            f"{version[0]}.{version[1]}. DSIS supports Python 3.11 through 3.14."
        )

    for distribution, module_name in RUNTIME_IMPORTS:
        try:
            import_module(module_name)
        except Exception as exc:
            errors.append(
                f"Missing or unusable runtime package {distribution} "
                f"(import {module_name!r}): {exc}. Install with "
                "python -m pip install -r requirements.txt."
            )

    if is_windows and not webview2_available:
        errors.append(
            "Microsoft Edge WebView2 Runtime was not detected. Install the "
            "WebView2 Evergreen Runtime before starting DSIS."
        )

    database_path = Path(database_path)
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        if database_path.exists():
            with database_path.open("ab"):
                pass
        else:
            with tempfile.NamedTemporaryFile(
                prefix=f".{database_path.name}.preflight-",
                dir=database_path.parent,
            ):
                pass
    except OSError as exc:
        errors.append(
            f"Database location is not writable ({database_path}): {exc}. "
            "Choose a writable data directory or correct its permissions."
        )

    try:
        ports = list(port_lister())
    except PermissionError as exc:
        warnings.append(
            "WARNING: Serial-port discovery was denied; a port may be busy or "
            f"access may be restricted ({exc}). Close other serial tools and "
            "check Windows port permissions."
        )
    except Exception as exc:
        warnings.append(
            "WARNING: Serial-port discovery failed; a port may be busy or "
            f"access may be restricted ({exc}). Close other serial tools and "
            "check Windows port permissions."
        )
    else:
        if not ports:
            hint = " Check for a CH340 or CP210x USB driver if the board is connected." if is_windows else ""
            warnings.append(
                "WARNING: No serial port was detected. DSIS will still open, "
                "but hardware features will be unavailable until a port is "
                f"visible.{hint}"
            )

    return PreflightReport(tuple(errors), tuple(warnings))


def _list_serial_ports(import_module: Callable[[str], object]) -> Iterable[object]:
    list_ports = import_module("serial.tools.list_ports")
    return list_ports.comports()


def _webview2_is_installed(import_module: Callable[[str], object]) -> bool:
    try:
        winreg = import_module("winreg")
    except ImportError:
        return False

    registry_paths = (
        rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_RUNTIME_ID}",
        rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_RUNTIME_ID}",
    )
    for hive_name in ("HKEY_CURRENT_USER", "HKEY_LOCAL_MACHINE"):
        hive = getattr(winreg, hive_name)
        for registry_path in registry_paths:
            try:
                with winreg.OpenKey(hive, registry_path) as key:
                    version, _ = winreg.QueryValueEx(key, "pv")
                if version and str(version) != "0":
                    return True
            except OSError:
                continue
    return False


def run_environment_preflight() -> PreflightReport:
    """Collect real host inputs for the pure preflight checker."""
    from config import get_config

    import_module = importlib.import_module
    is_windows = os.name == "nt"
    webview2_available = not is_windows or _webview2_is_installed(import_module)
    return check_startup_preflight(
        sys.version_info,
        import_module,
        lambda: _list_serial_ports(import_module),
        get_config().db_path,
        is_windows=is_windows,
        webview2_available=webview2_available,
    )


def format_preflight_report(report: PreflightReport) -> str:
    lines = [f"ERROR: {message}" for message in report.errors]
    lines.extend(report.warnings)
    return "\n".join(lines)