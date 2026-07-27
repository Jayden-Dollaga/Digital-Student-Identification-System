# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path.cwd()

block_cipher = None

a = Analysis(
    [str(root / "python" / "main.py")],
    pathex=[str(root / "python")],
    binaries=[],
    datas=[
        (str(root / "data"), "data"),
        (str(root / "assets"), "assets"),
        (str(root / "docs"), "docs"),
        (str(root / "firmware"), "firmware"),
        (str(root / "firmware" / "prebuilt"), "firmware/prebuilt"),
    ],
    hiddenimports=[
        "customtkinter",
        "serial",
        "esptool",
        "PIL",
        "matplotlib",
        "openpyxl",
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
    name="FingerprintAttendanceSystem",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name="FingerprintAttendanceSystem",
)
