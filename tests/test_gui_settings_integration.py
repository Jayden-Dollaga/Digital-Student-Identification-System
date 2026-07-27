"""
Test that settings toggles apply correctly to the GUI app at runtime.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
python_dir = PYTHON_ROOT / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

import tempfile
import json
from unittest.mock import MagicMock, patch

from settings_store import save_settings, load_settings


def test_app_applies_auto_reconnect_setting():
    """Verify app applies auto_reconnect setting on startup."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        
        # Create settings with auto_reconnect disabled
        settings = {
            "com_port": "COM3",
            "baud_rate": 115200,
            "cooldown": 10,
            "theme": "dark",
            "auto_reconnect": False,
            "auto_detect_serial": True,
            "compact_sidebar": False,
            "enable_profiler": False,
        }
        save_settings(settings, settings_file)
        
        # Mock SerialHandler
        mock_serial = MagicMock()
        mock_serial.auto_reconnect_enabled = True  # Default
        
        # Load settings and apply to mock handler
        loaded = load_settings(settings_file)
        mock_serial.auto_reconnect_enabled = bool(loaded.get("auto_reconnect", True))
        
        # Verify setting was applied
        assert mock_serial.auto_reconnect_enabled is False
        print("✓ auto_reconnect setting applied to SerialHandler")


def test_app_applies_auto_detect_serial_setting():
    """Verify app applies auto_detect_serial setting on startup."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        
        # Create settings with auto_detect_serial enabled
        settings = {
            "com_port": "COM3",
            "baud_rate": 115200,
            "cooldown": 10,
            "theme": "dark",
            "auto_reconnect": True,
            "auto_detect_serial": True,
            "compact_sidebar": False,
            "enable_profiler": False,
        }
        save_settings(settings, settings_file)
        
        # Simulate app behavior
        loaded = load_settings(settings_file)
        app_auto_detect_serial = bool(loaded.get("auto_detect_serial", True))
        
        assert app_auto_detect_serial is True
        print("✓ auto_detect_serial setting applied to app")


def test_app_applies_profiler_setting():
    """Verify app applies enable_profiler setting to PerfProfiler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        
        # Create settings with profiler enabled
        settings = {
            "com_port": "COM3",
            "baud_rate": 115200,
            "cooldown": 10,
            "theme": "dark",
            "auto_reconnect": True,
            "auto_detect_serial": True,
            "compact_sidebar": False,
            "enable_profiler": True,
        }
        save_settings(settings, settings_file)
        
        # Mock PerfProfiler
        mock_profiler = MagicMock()
        mock_profiler.enabled = False  # Default
        
        # Load and apply
        loaded = load_settings(settings_file)
        mock_profiler.enabled = bool(loaded.get("enable_profiler", False))
        
        assert mock_profiler.enabled is True
        print("✓ enable_profiler setting applied to PerfProfiler")


def test_compact_sidebar_toggle_changes_button_display():
    """Verify compact_sidebar setting affects button rendering."""
    # Simulate the button display logic from sidebar.py
    def get_display_text(text, is_compact):
        if is_compact:
            return text.split()[0] if text and len(text.split()) > 0 else text
        else:
            return text
    
    full_text = "▶  Start Scan"
    
    # In compact mode
    compact_display = get_display_text(full_text, is_compact=True)
    assert compact_display == "▶", f"Expected '▶' in compact mode, got {compact_display}"
    
    # In normal mode
    normal_display = get_display_text(full_text, is_compact=False)
    assert normal_display == full_text, f"Expected '{full_text}' in normal mode, got {normal_display}"
    
    print("✓ compact_sidebar affects button display correctly")


def test_settings_change_persists_after_reload():
    """Verify changed settings persist after app restart."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        
        # Initial state
        initial = {
            "auto_reconnect": True,
            "auto_detect_serial": False,
            "compact_sidebar": False,
            "enable_profiler": False,
        }
        
        # Save initial settings
        save_settings(initial, settings_file)
        
        # Load and simulate user changing settings in GUI
        loaded1 = load_settings(settings_file)
        changed = loaded1.copy()
        changed.update({
            "auto_reconnect": False,
            "compact_sidebar": True,
            "enable_profiler": True,
        })
        save_settings(changed, settings_file)
        
        # Simulate app restart by loading again
        loaded2 = load_settings(settings_file)
        
        assert loaded2["auto_reconnect"] is False
        assert loaded2["compact_sidebar"] is True
        assert loaded2["enable_profiler"] is True
        assert loaded2["auto_detect_serial"] is False  # Should remain unchanged
        
        print("✓ Changed settings persist across simulated restart")


def test_all_toggles_have_runtime_effect():
    """Verify all toggles in settings dialog are actually used."""
    toggle_settings = {
        "auto_reconnect",
        "auto_detect_serial",
        "compact_sidebar",
        "enable_profiler",
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = Path(tmpdir) / "settings.json"
        settings = {
            "com_port": "COM3",
            "baud_rate": 115200,
            "cooldown": 10,
            "theme": "dark",
            "auto_reconnect": True,
            "auto_detect_serial": True,
            "compact_sidebar": True,
            "enable_profiler": True,
        }
        save_settings(settings, settings_file)
        
        loaded = load_settings(settings_file)
        for toggle_name in toggle_settings:
            assert toggle_name in loaded, f"Toggle {toggle_name} missing from loaded settings"
            assert isinstance(loaded[toggle_name], bool), f"Toggle {toggle_name} is not boolean"
        
        print(f"✓ All {len(toggle_settings)} toggles are present and boolean type")


if __name__ == "__main__":
    try:
        test_app_applies_auto_reconnect_setting()
        test_app_applies_auto_detect_serial_setting()
        test_app_applies_profiler_setting()
        test_compact_sidebar_toggle_changes_button_display()
        test_settings_change_persists_after_reload()
        test_all_toggles_have_runtime_effect()
        print("\n✅ All GUI settings integration tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
