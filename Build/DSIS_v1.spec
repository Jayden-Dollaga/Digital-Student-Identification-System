# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

if "__file__" in globals():
    ROOT = Path(__file__).resolve().parent.parent
else:
    ROOT = Path.cwd().resolve()

V1_ROOT = ROOT / "archive" / "legacy-ui" / "v1"
V1_PYTHON = V1_ROOT / "python"
LOGO_ICO = ROOT / "assets" / "icon" / "DSIS_LOGO.ico"

block_cipher = None

a = Analysis(
    [str(V1_PYTHON / "gui" / "app.py")],
    pathex=[str(V1_PYTHON)],
    binaries=[],
    datas=[
        (str(V1_ROOT / "data"), "data"),
        (str(LOGO_ICO), "assets/icon"),
    ],
    hiddenimports=collect_submodules("customtkinter") + collect_submodules("PIL") + [
        "config",
        "settings_store",
        "core.database",
        "core.serial_handler",
        "core.attendance",
        "core.commands",
        "core.utils",
        "gui.app",
        "gui.sidebar",
        "gui.attendance_page",
        "gui.statistics_page",
        "gui.log_page",
        "gui.settings_dialog",
        "gui.dialogs",
        "gui.reports_page",
        "gui.students_page",
        "gui.dashboard",
        "gui.settings_page",
        "gui.theme",
        "serial",
        "numpy",
        "matplotlib",
        "openpyxl",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6", "gui_qt", "webview"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DSIS-v1",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(LOGO_ICO),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DSIS-v1",
)
