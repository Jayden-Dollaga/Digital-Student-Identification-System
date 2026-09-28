# Portable Build Guide

This guide covers the current DSIS v3 packaging path. The active build output is based on the v3 pywebview app and uses the repo source launcher `run_web_gui.py`.

> Historical portable build scripts tied to the older CustomTkinter or Qt paths are archived and must not be treated as the current supported package.

## Active spec

The maintained packaging target is:

- `Build/DSIS_v3.spec`

The app writes runtime data to the local `data/` directory, not inside the bundled frozen app. The packaged app must be deployed with a writable data folder next to the executable.

## Build command

From the repository root:

```powershell
python -m PyInstaller Build\DSIS_v3.spec --clean --noconfirm --workpath Build\build-v3 --distpath Build\DSIS_v3
```

Expected output:

```text
Build\DSIS_v3\DSIS\DSIS.exe
```

## Deployment checklist

1. Copy the built package together with a writable `data/` directory.
2. Keep `settings.json`, `attendance.db`, `backups/`, `logs/`, and `exports/` outside the frozen executable tree.
3. Ensure the target Windows machine has the correct ESP32 USB driver installed.
4. Verify the device is flashed with the maintained firmware at `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`.
5. Run the app and validate the first-run wizard and device connection flow.
6. Confirm attendance scan, enrollment, backup/restore, and export flows still work on the packaged build.

## Validation checklist

Before a release or package handoff:

- run `python run_web_gui.py` as a source smoke test
- run the PyInstaller command above
- verify the packaged app starts and loads the v3 UI
- verify the serial connection and handshake succeed
- verify enrollment and scan flows operate normally
- verify restore and export paths remain writable and valid

## Historical packaging notes

The repository contains older portable tooling and legacy packaging spec files in `tools/` and historical archive paths. Those are kept as reference only and may package earlier UI implementations; they should not be used for the current v3 distribution.

See [docs/Development/release-and-portable-build.md](docs/Development/release-and-portable-build.md) for the release validation workflow.
