# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

if "__file__" in globals():
    ROOT = Path(__file__).resolve().parent
else:
    ROOT = Path(os.getcwd()).resolve()

block_cipher = None

# Current presentation GUI entry point for the active DSIS Qt app.
a = Analysis(
    [str(ROOT / "run_qt_gui.py")],
    pathex=[str(ROOT / "python")],
    binaries=[],
    datas=[
        (str(ROOT / "data"), "data"),
        (str(ROOT / "assets"), "assets"),
        (str(ROOT / "python" / "gui_qt" / "theme.qss"), "python/gui_qt"),
        (str(ROOT / "python" / "gui_qt" / "theme_light.qss"), "python/gui_qt"),
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
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DSIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
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
    name="DSIS",
)
