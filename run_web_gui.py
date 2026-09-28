"""Launch the active HTML/pywebview DSIS interface (v3) from the repository root."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "python"
GUI_WEB_DIR = PYTHON_DIR / "gui_web"

for path in (PYTHON_DIR, GUI_WEB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from startup_preflight import format_preflight_report, run_environment_preflight


def main(preflight_runner=run_environment_preflight, app_launcher=None):
    report = preflight_runner()
    output = format_preflight_report(report)
    if output:
        print(output, file=sys.stderr)
    if not report.ok:
        raise SystemExit(1)

    if app_launcher is None:
        from gui_web.main_web import main as app_launcher

    app_launcher()


if __name__ == "__main__":
    main()
