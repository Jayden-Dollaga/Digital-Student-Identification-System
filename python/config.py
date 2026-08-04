"""Configuration helpers for the fingerprint attendance system.

The module now exposes a small config dataclass and environment-aware helpers
without doing expensive serial discovery during import time.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from serial.tools import list_ports
except Exception:  # pragma: no cover - optional dependency on non-serial setups
    list_ports = None

def _resolve_project_root() -> Path:
    """Return the writable runtime root for both source and packaged builds."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _resolve_project_root()
DATA_DIR = PROJECT_ROOT / "data"

DEFAULT_COM_PORT = "COM5"
DEFAULT_BAUD_RATE = 115200
DEFAULT_BAUD_RATES: Tuple[int, ...] = (9600, 19200, 38400, 57600, 115200)
DEFAULT_THEME_MODES: Tuple[str, ...] = ("Dark", "Light")
DEFAULT_IGNORE_PREFIXES: Tuple[str, ...] = (
    "rst:",
    "load:",
    "entry",
    "configsip",
    "mode:",
    "ho ",
    "clk_",
    "========",
    "Commands",
    "ENROLL:",
    "DELETE:",
    "WIPE",
    "LIST",
    "SCAN",
    "STOP",
    "Place finger",
    "Enroll finger",
    "Delete finger",
    "Delete ALL",
    "Show stored",
    "Start attendance",
    "Stop scanning",
    "line ending",
)
DEFAULT_USER_ROLES: Dict[str, Dict[str, Any]] = {
    "admin": {
        "name": "Administrator",
        "permissions": ["scan", "enroll", "delete", "wipe", "export", "backup", "restore"],
        "can_manage_users": True,
    },
    "teacher": {
        "name": "Teacher",
        "permissions": ["scan", "export", "backup"],
        "can_manage_users": False,
    },
    "guest": {
        "name": "Guest",
        "permissions": ["scan"],
        "can_manage_users": False,
    },
}


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if value is None:
        return default
    return Path(value).expanduser()


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration values with environment override support."""

    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    data_dir: Path = field(default_factory=lambda: DATA_DIR)
    com_port: str = field(default_factory=lambda: os.getenv("FINGERPRINT_COM_PORT", DEFAULT_COM_PORT))
    baud_rate: int = field(default_factory=lambda: _env_int("FINGERPRINT_BAUD_RATE", DEFAULT_BAUD_RATE))
    baud_rates: Tuple[int, ...] = field(default_factory=lambda: DEFAULT_BAUD_RATES)
    auto_scan: bool = field(default_factory=lambda: _env_flag("FINGERPRINT_AUTO_SCAN", True))
    theme_modes: Tuple[str, ...] = field(default_factory=lambda: DEFAULT_THEME_MODES)
    cooldown_seconds: int = field(default_factory=lambda: _env_int("FINGERPRINT_COOLDOWN_SECONDS", 10))
    min_confidence: int = field(default_factory=lambda: _env_int("FINGERPRINT_MIN_CONFIDENCE", 100))
    db_path: Path = field(default_factory=lambda: _env_path("FINGERPRINT_DB_PATH", DATA_DIR / "attendance.db"))
    export_folder: Path = field(default_factory=lambda: _env_path("FINGERPRINT_EXPORT_FOLDER", DATA_DIR / "exports"))
    ignore_prefixes: Tuple[str, ...] = field(default_factory=lambda: DEFAULT_IGNORE_PREFIXES)
    log_to_file: bool = field(default_factory=lambda: _env_flag("FINGERPRINT_LOG_TO_FILE", True))
    log_folder: Path = field(default_factory=lambda: _env_path("FINGERPRINT_LOG_FOLDER", DATA_DIR / "logs"))
    log_file_name: str = field(default_factory=lambda: os.getenv("FINGERPRINT_LOG_FILE_NAME", "fingerprint_attendance.log"))
    log_level: str = field(default_factory=lambda: os.getenv("FINGERPRINT_LOG_LEVEL", "DEBUG" if _env_flag("FINGERPRINT_ENABLE_DEBUG_LOGGING", False) else "INFO").upper())
    log_rotation_when: str = field(default_factory=lambda: os.getenv("FINGERPRINT_LOG_ROTATION_WHEN", "midnight"))
    log_rotation_interval: int = field(default_factory=lambda: _env_int("FINGERPRINT_LOG_ROTATION_INTERVAL", 1))
    log_rotation_backup_count: int = field(default_factory=lambda: _env_int("FINGERPRINT_LOG_ROTATION_BACKUP_COUNT", 7))
    enable_debug_logging: bool = field(default_factory=lambda: _env_flag("FINGERPRINT_ENABLE_DEBUG_LOGGING", False))
    auto_reconnect: bool = field(default_factory=lambda: _env_flag("FINGERPRINT_AUTO_RECONNECT", True))
    reconnect_max_retries: int = field(default_factory=lambda: _env_int("FINGERPRINT_RECONNECT_MAX_RETRIES", 5))
    reconnect_base_delay: int = field(default_factory=lambda: _env_int("FINGERPRINT_RECONNECT_BASE_DELAY", 2))
    user_roles: Dict[str, Dict[str, Any]] = field(default_factory=lambda: DEFAULT_USER_ROLES)
    default_user_role: str = field(default_factory=lambda: os.getenv("FINGERPRINT_DEFAULT_USER_ROLE", "admin"))

    @classmethod
    def from_env(cls, overrides: Optional[Dict[str, Any]] = None) -> "AppConfig":
        overrides = overrides or {}
        return cls(
            com_port=overrides.get("com_port", os.getenv("FINGERPRINT_COM_PORT", DEFAULT_COM_PORT)),
            baud_rate=overrides.get("baud_rate", _env_int("FINGERPRINT_BAUD_RATE", DEFAULT_BAUD_RATE)),
            auto_scan=overrides.get("auto_scan", _env_flag("FINGERPRINT_AUTO_SCAN", True)),
            cooldown_seconds=overrides.get("cooldown_seconds", _env_int("FINGERPRINT_COOLDOWN_SECONDS", 10)),
            min_confidence=overrides.get("min_confidence", _env_int("FINGERPRINT_MIN_CONFIDENCE", 100)),
            db_path=overrides.get("db_path", _env_path("FINGERPRINT_DB_PATH", DATA_DIR / "attendance.db")),
            export_folder=overrides.get("export_folder", _env_path("FINGERPRINT_EXPORT_FOLDER", DATA_DIR / "exports")),
            log_to_file=overrides.get("log_to_file", _env_flag("FINGERPRINT_LOG_TO_FILE", True)),
            log_folder=overrides.get("log_folder", _env_path("FINGERPRINT_LOG_FOLDER", DATA_DIR / "logs")),
            log_file_name=overrides.get("log_file_name", os.getenv("FINGERPRINT_LOG_FILE_NAME", "fingerprint_attendance.log")),
            log_level=overrides.get("log_level", os.getenv("FINGERPRINT_LOG_LEVEL", "DEBUG" if _env_flag("FINGERPRINT_ENABLE_DEBUG_LOGGING", False) else "INFO").upper()),
            log_rotation_when=overrides.get("log_rotation_when", os.getenv("FINGERPRINT_LOG_ROTATION_WHEN", "midnight")),
            log_rotation_interval=overrides.get("log_rotation_interval", _env_int("FINGERPRINT_LOG_ROTATION_INTERVAL", 1)),
            log_rotation_backup_count=overrides.get("log_rotation_backup_count", _env_int("FINGERPRINT_LOG_ROTATION_BACKUP_COUNT", 7)),
            enable_debug_logging=overrides.get("enable_debug_logging", _env_flag("FINGERPRINT_ENABLE_DEBUG_LOGGING", False)),
            auto_reconnect=overrides.get("auto_reconnect", _env_flag("FINGERPRINT_AUTO_RECONNECT", True)),
            reconnect_max_retries=overrides.get("reconnect_max_retries", _env_int("FINGERPRINT_RECONNECT_MAX_RETRIES", 5)),
            reconnect_base_delay=overrides.get("reconnect_base_delay", _env_int("FINGERPRINT_RECONNECT_BASE_DELAY", 2)),
            default_user_role=overrides.get("default_user_role", os.getenv("FINGERPRINT_DEFAULT_USER_ROLE", "admin")),
        )


_CONFIG = AppConfig.from_env()


def get_config() -> AppConfig:
    """Return the shared runtime configuration object."""
    return _CONFIG


def discover_serial_ports() -> List[str]:
    """Return a list of available serial ports when pyserial is available."""
    if list_ports is None:
        return []
    try:
        return [port.device for port in list_ports.comports()]
    except Exception:
        return []


def get_default_com_port(default_fallback: Optional[str] = None) -> str:
    """Choose the most likely ESP32 serial port without doing work at import time."""
    fallback = default_fallback or os.getenv("FINGERPRINT_COM_PORT", DEFAULT_COM_PORT)
    if list_ports is None:
        return fallback

    try:
        ports = list_ports.comports()
    except Exception:
        return fallback

    if not ports:
        return fallback

    keywords = [
        "cp210",
        "ch340",
        "usb serial",
        "silicon labs",
        "uart",
        "esp32",
        "arduino",
    ]
    known_vid_pids = {
        "10c4:ea60": 140,
        "1a86:7523": 140,
        "0403:6001": 120,
        "1a86:55d3": 120,
    }
    scored_ports = []
    for port in ports:
        device = (getattr(port, "device", "") or "").lower()
        description = (getattr(port, "description", "") or "").lower()
        combined = f"{device} {description}"
        vid = getattr(port, "vid", None)
        pid = getattr(port, "pid", None)
        # Normalize VID:PID to zero-padded 4-digit hex (matches settings UI formatting)
        vid_pid = f"{vid:04x}:{pid:04x}" if vid is not None and pid is not None else ""
        score = 0
        if vid_pid in known_vid_pids:
            score += known_vid_pids[vid_pid]
        if any(keyword in combined for keyword in keywords):
            score += 80
        if "bluetooth" in combined or "bt" in combined:
            score -= 100
        if "com" in device:
            score += 10
        if "usb" in combined:
            score += 10
        scored_ports.append((score, device, getattr(port, "description", "")))

    scored_ports.sort(key=lambda item: item[0], reverse=True)
    best_port = None
    for score, device, _description in scored_ports:
        if device:
            best_port = device
            if score >= 80:
                return best_port
    return best_port or fallback


def get_com_port(default_fallback: Optional[str] = None) -> str:
    """Return the preferred serial port, preferring an environment override."""
    return os.getenv("FINGERPRINT_COM_PORT") or get_default_com_port(default_fallback)


# Backward-compatible module-level values
COM_PORT = os.getenv("FINGERPRINT_COM_PORT", DEFAULT_COM_PORT)
BAUD_RATE = _CONFIG.baud_rate
BAUD_RATES = list(_CONFIG.baud_rates)
AUTO_SCAN = _CONFIG.auto_scan
THEME_MODES = list(_CONFIG.theme_modes)
COOLDOWN_SECONDS = _CONFIG.cooldown_seconds
MIN_CONFIDENCE = _CONFIG.min_confidence
DB_PATH = str(_CONFIG.db_path)
EXPORT_FOLDER = str(_CONFIG.export_folder)
IGNORE_PREFIXES = _CONFIG.ignore_prefixes
LOG_TO_FILE = _CONFIG.log_to_file
LOG_FOLDER = str(_CONFIG.log_folder)
ENABLE_DEBUG_LOGGING = _CONFIG.enable_debug_logging
AUTO_RECONNECT = _CONFIG.auto_reconnect
RECONNECT_MAX_RETRIES = _CONFIG.reconnect_max_retries
RECONNECT_BASE_DELAY = _CONFIG.reconnect_base_delay
USER_ROLES = _CONFIG.user_roles
DEFAULT_USER_ROLE = _CONFIG.default_user_role