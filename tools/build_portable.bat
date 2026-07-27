@echo off
setlocal
cd /d "%~dp0.."

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py -3
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python
    ) else (
        echo Python was not found on PATH.
        echo Install Python 3.10+ and try again.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% -m pip install --upgrade pip pyinstaller
%PYTHON_CMD% -m pip install -r requirements.txt
%PYTHON_CMD% -m pip install esptool

if errorlevel 1 (
    echo Some optional dependencies could not be installed, but the portable build can continue.
)
%PYTHON_CMD% -m PyInstaller --clean --noconfirm --distpath dist\portable --workpath build\pyinstaller tools\fingerprint_portable.spec
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo Build completed.
echo Output folder: dist\portable\FingerprintAttendanceSystem
pause
