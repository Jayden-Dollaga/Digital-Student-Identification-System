# Desktop Troubleshooting

## Application does not start

Check Python and requirements first:

    python -m pip install -r requirements.txt
    python run_web_gui.py

Then verify the v3 web files exist under `python/gui_web/web/`.

For a packaged build, verify the collected executable and web assets.

## Wizard keeps appearing

The wizard is controlled by the password hash plus these settings flags:

- `setup_device_step_done`
- `setup_schedule_step_done`
- `setup_branding_step_done`

The `current_role` setting is not an authentication source.

## Settings are denied

Some settings operations are Administrator-only. Confirm the current in-memory role rather than editing `settings.json`.

## Logs are missing

Check that `data/logs/` is writable and file logging is enabled. The UI's recent log view is fed by the central logger.

## Archive confusion

For current behavior, always run `run_web_gui.py`. The CustomTkinter and Qt implementations under `archive/legacy-ui/` are historical.
