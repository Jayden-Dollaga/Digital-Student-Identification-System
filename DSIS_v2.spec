# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd().resolve()
V2_ROOT = ROOT / "archive" / "legacy-ui" / "v2"
V2_PYTHON = V2_ROOT / "python"

block_cipher = None

a = Analysis(
    [str(V2_ROOT / "run_qt_gui.py")],
    pathex=[str(V2_PYTHON)],
    binaries=[],
    datas=[
        (str(V2_ROOT / "data"), "data"),
        (str(V2_PYTHON / "gui_qt" / "theme.qss"), "gui_qt"),
        (str(V2_PYTHON / "gui_qt" / "theme_light.qss"), "gui_qt"),
    ],
    hiddenimports=[
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "gui_qt.main_qt",
        "gui_qt.main_window",
        "gui_qt.pages.dashboard_page",
        "gui_qt.pages.attendance_page",
        "gui_qt.pages.students_page",
        "gui_qt.pages.reports_page",
        "gui_qt.pages.logs_page",
        "gui_qt.pages.settings_page",
        "gui_qt.widgets.sidebar",
        "gui_qt.widgets.stat_card",
        "gui_qt.workers.connection_worker",
        "gui_qt.workers.serial_worker",
        "serial",
        "matplotlib",
        "openpyxl",
        "PIL",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["gui", "main", "customtkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DSIS-v2",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    name="DSIS-v2",
)