import json
from pathlib import Path
from typing import Any, Dict

from config import get_config

CONFIG = get_config()
SETTINGS_FILE = CONFIG.data_dir / "settings.json"


def default_settings() -> Dict[str, Any]:
    return {
        "com_port": "",
        "baud_rate": CONFIG.baud_rate,
        "cooldown": CONFIG.cooldown_seconds,
        "theme": "dark",
        "auto_reconnect": True,
        "auto_detect_serial": True,
        # compact sidebar (icons-only) to save vertical space
        "compact_sidebar": False,
            # enable lightweight UI profiler (records timing of key UI events)
            "enable_profiler": False,
    }


def load_settings(path: str | Path | None = None) -> Dict[str, Any]:
    settings_path = Path(path or SETTINGS_FILE)
    if not settings_path.exists():
        return default_settings()

    try:
        with settings_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return default_settings()

    merged = default_settings()
    if isinstance(loaded, dict):
        merged.update({key: value for key, value in loaded.items() if key in merged})
    return merged


def save_settings(settings: Dict[str, Any], path: str | Path | None = None) -> Path:
    settings_path = Path(path or SETTINGS_FILE)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = default_settings()
    payload.update(settings)
    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return settings_path
