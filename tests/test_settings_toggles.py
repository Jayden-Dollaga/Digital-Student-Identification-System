"""
Test settings toggles to ensure they save and apply correctly in the GUI.
"""
import sys
import os
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

# Add python folder to path for imports
python_dir = PYTHON_ROOT / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

import json
import tempfile
from unittest.mock import MagicMock, patch

from settings_store import default_settings, load_settings, save_settings


def test_default_settings():
    """Verify default settings include all toggle flags."""
    defaults = default_settings()
    assert "auto_reconnect" in defaults
    assert "auto_detect_serial" in defaults
    assert "compact_sidebar" in defaults
    assert "enable_profiler" in defaults
    print("✓ Default settings include all toggle flags")


def test_save_and_load_settings():
    """Verify settings can be saved and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        
        # Create test settings with toggles enabled
        test_settings = {
            "com_port": "COM3",
            "baud_rate": 115200,
            "cooldown": 10,
            "theme": "dark",
            "auto_reconnect": True,
            "auto_detect_serial": False,
            "compact_sidebar": True,
            "enable_profiler": True,
        }
        
        # Save settings
        save_settings(test_settings, settings_file)
        assert settings_file.exists(), "Settings file was not created"
        print("✓ Settings file created successfully")
        
        # Load settings
        loaded = load_settings(settings_file)
        assert loaded["auto_reconnect"] is True
        assert loaded["auto_detect_serial"] is False
        assert loaded["compact_sidebar"] is True
        assert loaded["enable_profiler"] is True
        print("✓ Settings loaded with correct toggle states")


def test_settings_toggle_persistence():
    """Verify toggles persist across save/load cycles."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        
        # Cycle 1: Enable all toggles
        settings1 = default_settings()
        settings1.update({
            "auto_reconnect": True,
            "auto_detect_serial": True,
            "compact_sidebar": True,
            "enable_profiler": True,
        })
        save_settings(settings1, settings_file)
        loaded1 = load_settings(settings_file)
        assert all([
            loaded1["auto_reconnect"],
            loaded1["auto_detect_serial"],
            loaded1["compact_sidebar"],
            loaded1["enable_profiler"],
        ]), "All toggles should be True in cycle 1"
        print("✓ All toggles persisted as True")
        
        # Cycle 2: Disable specific toggles
        settings2 = loaded1.copy()
        settings2.update({
            "auto_reconnect": False,
            "compact_sidebar": False,
        })
        save_settings(settings2, settings_file)
        loaded2 = load_settings(settings_file)
        assert loaded2["auto_reconnect"] is False
        assert loaded2["compact_sidebar"] is False
        assert loaded2["auto_detect_serial"] is True
        assert loaded2["enable_profiler"] is True
        print("✓ Toggle state changes persisted correctly")


def test_settings_json_format():
    """Verify saved settings are valid JSON with expected structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        
        test_settings = default_settings()
        save_settings(test_settings, settings_file)
        
        # Read raw JSON to verify format
        with open(settings_file, 'r') as f:
            raw_json = json.load(f)
        
        required_keys = [
            "com_port", "baud_rate", "cooldown", "theme",
            "auto_reconnect", "auto_detect_serial", "compact_sidebar", "enable_profiler"
        ]
        for key in required_keys:
            assert key in raw_json, f"Missing key: {key}"
        print(f"✓ Settings JSON contains all required keys: {', '.join(required_keys)}")


def test_toggle_types():
    """Verify toggle settings are boolean types."""
    settings = default_settings()
    toggles = [
        ("auto_reconnect", settings["auto_reconnect"]),
        ("auto_detect_serial", settings["auto_detect_serial"]),
        ("compact_sidebar", settings["compact_sidebar"]),
        ("enable_profiler", settings["enable_profiler"]),
    ]
    for name, value in toggles:
        assert isinstance(value, bool), f"{name} should be bool, got {type(value)}"
    print("✓ All toggle settings are boolean type")


def test_settings_merge_on_load():
    """Verify new settings are merged with defaults when loading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        
        # Save partial settings (missing some keys)
        partial = {
            "com_port": "COM5",
            "baud_rate": 9600,
        }
        with open(settings_file, 'w') as f:
            json.dump(partial, f)
        
        # Load should merge with defaults
        loaded = load_settings(settings_file)
        assert loaded["com_port"] == "COM5"  # Should be from file
        assert loaded["baud_rate"] == 9600   # Should be from file
        assert loaded["auto_reconnect"] == True  # Should be from defaults
        assert loaded["compact_sidebar"] == False  # Should be from defaults
        print("✓ Settings correctly merged with defaults on load")


if __name__ == "__main__":
    try:
        test_default_settings()
        test_save_and_load_settings()
        test_settings_toggle_persistence()
        test_settings_json_format()
        test_toggle_types()
        test_settings_merge_on_load()
        print("\n✅ All settings toggle tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
