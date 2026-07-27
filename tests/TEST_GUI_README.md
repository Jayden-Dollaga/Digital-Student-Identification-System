# Test GUI Demo - Fingerprint Attendance System

## Overview
This is a test GUI that demonstrates the settings toggles working in your attendance system. You can toggle settings on/off and see them save and persist.

## How to Run

### Quick Start
```bash
cd "c:\Users\EnforcerX\Downloads\Arduino-IDE - Project\AI-Assisted Fingerprint Attendance System"
python tests/test_gui_demo.py
```

### What You'll See
- **Left Sidebar**: Settings controls with 4 toggles
- **Main Area**: Attendance dashboard with sample data
- **Status Updates**: Real-time log of what's happening

---

## Testing the Toggles

### The 4 Settings Toggles

1. **Auto-Reconnect** ✓
   - When ON: System reconnects automatically if ESP32 disconnects
   - When OFF: Requires manual reconnection
   - Status: Shows in sidebar

2. **Auto-Detect ESP32** ✓
   - When ON: System automatically finds ESP32 on startup
   - When OFF: You must manually select the COM port
   - Status: Shows in sidebar

3. **Compact Sidebar** ✓
   - When ON: Buttons show icons only (takes less space)
   - When OFF: Buttons show full text labels
   - Status: Updates sidebar layout immediately

4. **Enable Profiler** ✓
   - When ON: Tracks performance metrics
   - When OFF: Performance tracking disabled
   - Status: Updates in real-time

### Testing Steps

1. **Start the GUI**
   ```bash
   python tests/test_gui_demo.py
   ```

2. **Check initial state**
   - Look at the left sidebar
   - See which toggles are already enabled
   - Notice the "Active Toggles" counter shows how many are on

3. **Toggle each setting**
   - Click each checkbox to toggle it ON/OFF
   - Watch the log area show "Toggle changed"
   - Notice the active count updates

4. **Save Settings**
   - Click "Save Settings" button
   - Watch the status change to "✓ Settings saved"
   - Check the log for confirmation

5. **Verify Persistence**
   - Close the GUI completely
   - Re-run it: `python tests/test_gui_demo.py`
   - Your saved settings should still be there!

---

## What Happens Behind the Scenes

### Settings File Location
Settings are saved to: `data/settings.json`

### Sample settings.json
```json
{
  "com_port": "COM3",
  "baud_rate": 115200,
  "cooldown": 10,
  "theme": "dark",
  "auto_reconnect": true,
  "auto_detect_serial": false,
  "compact_sidebar": true,
  "enable_profiler": false
}
```

### How Toggles Work

1. **User clicks toggle** → Checkbox state changes
2. **User clicks "Save Settings"** → Settings saved to JSON file
3. **GUI reads settings on next startup** → Settings restored
4. **App applies settings to runtime** → Features activate/deactivate

---

## Testing Checklist

Use this checklist to verify everything works:

- [ ] Run GUI without errors
- [ ] All 4 toggles are visible
- [ ] Toggle "Auto-Reconnect" ON/OFF
- [ ] Toggle "Auto-Detect ESP32" ON/OFF
- [ ] Toggle "Compact Sidebar" ON/OFF
- [ ] Toggle "Enable Profiler" ON/OFF
- [ ] Click "Save Settings" button
- [ ] See "Settings saved" message
- [ ] Close and reopen GUI
- [ ] Verify saved settings are still there
- [ ] Check `data/settings.json` file exists
- [ ] Verify JSON is valid format

---

## Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the project root:
cd "c:\Users\EnforcerX\Downloads\Arduino-IDE - Project\AI-Assisted Fingerprint Attendance System"
python tests/test_gui_demo.py
```

### Settings not saving
- Check that `data/` folder exists
- Verify write permissions to the folder
- Check `data/settings.json` file

### GUI doesn't open
- Make sure `customtkinter` is installed:
  ```bash
  pip install customtkinter
  ```

### Toggles don't stick after closing
- Check file permissions
- Verify `settings.json` is being written
- Run tests to verify settings persistence: `python tests/test_settings_toggles.py`

---

## Running Automated Tests

### Test Settings Persistence
```bash
python tests/test_settings_toggles.py
```
Expected output: ✅ All settings toggle tests passed!

### Test GUI Integration
```bash
python tests/test_gui_settings_integration.py
```
Expected output: ✅ All GUI settings integration tests passed!

### Run All Tests
```bash
python -m pytest tests/ -v
```
Expected: 35+ tests passing

---

## What Gets Tested

### In `test_settings_toggles.py`:
- ✓ Settings save/load correctly
- ✓ Toggle states persist across restart
- ✓ JSON format is valid
- ✓ All toggles are boolean type

### In `test_gui_settings_integration.py`:
- ✓ Settings apply to app components
- ✓ Compact sidebar changes button display
- ✓ Profiler enable/disable works
- ✓ Settings merge with defaults

---

## Next Steps

Once you verify the toggles work:

1. Test with the **real GUI**: `python python/gui/app.py`
2. Connect an **ESP32** and test settings in production
3. Verify **Auto-Reconnect** works when ESP32 disconnects
4. Check **Compact Sidebar** with real buttons
5. Monitor **Profiler** output in logs

---

## Questions?

Check these files:
- **Settings logic**: `python/settings_store.py`
- **GUI settings dialog**: `python/gui/settings_dialog.py`
- **Settings apply**: `python/gui/app.py` (search for `_apply_settings_to_runtime`)
- **Sidebar build**: `python/gui/sidebar.py` (search for `compact_sidebar`)
