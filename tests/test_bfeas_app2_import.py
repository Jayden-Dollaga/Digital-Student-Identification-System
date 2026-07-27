import runpy
from pathlib import Path
from unittest.mock import patch

import customtkinter as ctk


def test_bfeas_app2_script_runs_without_module_path_errors():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "python" / "gui" / "legacy" / "bfeas_app2.py"

    with patch.object(ctk.CTk, "mainloop", lambda self: None):
        runpy.run_path(str(script_path), run_name="__main__")
