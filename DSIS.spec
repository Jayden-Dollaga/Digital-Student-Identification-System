# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

if "__file__" in globals():
    ROOT = Path(__file__).resolve().parent
else:
    ROOT = Path(os.getcwd()).resolve()

block_cipher = None

# Active V3 HTML/pywebview entry point.
a = Analysis(
    [str(ROOT / "run_web_gui.py")],
    pathex=[str(ROOT / "python"), str(ROOT / "python" / "gui_web")],
    binaries=[],
    datas=[
        (str(ROOT / "python" / "gui_web" / "web"), "gui_web/web"),
    ],
    hiddenimports=collect_submodules("webview") + [
        "webview",
        "gui_web.main_web",
        "gui_web.api",
        "api",
        "core.database",
        "core.serial_handler",
        "core.attendance",
        "core.permissions",
        "core.commands",
        "core.device_discovery",
        "core.logger",
        "config",
        "settings_store",
        "serial",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["gui_qt", "PySide6", "customtkinter"],
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
