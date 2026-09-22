# Release and Portable Build

## Active build

The maintained Windows package uses:

    Build/DSIS_v3.spec

The spec runs `run_web_gui.py`, collects `python/gui_web/web/`, includes the DSIS icon, and excludes the archived Qt/CustomTkinter stacks.

Build command:

    python -m PyInstaller Build\DSIS_v3.spec --clean --noconfirm --workpath Build\build-v3 --distpath Build\DSIS_v3

The spec currently names the collected directory `DSIS-v3` and executable `DSIS-v3.exe`.

## Validation

Run:

    python -m pytest -q
    python -m compileall python
    node --check python/gui_web/web/app.js

Then verify the package starts and keeps writable runtime data external to the frozen bundle.

## Runtime data

The package must be able to create/write:

    data/
      settings.json
      attendance.db
      backups/
      logs/
      exports/
      charts/

## Historical packaging

Older packaging helpers under `tools/` belong to the historical CustomTkinter product generation. They are preserved but do not define the current v3 package.
