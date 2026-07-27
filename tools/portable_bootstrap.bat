@echo off
setlocal
cd /d "%~dp0.."

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Python launcher found.
    py -3 -m pip install --upgrade pip
    py -3 -m pip install -r requirements.txt
    exit /b 0
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Python found on PATH.
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    exit /b 0
)

echo Python was not found on PATH.
echo Please install Python 3.10+ from https://www.python.org/downloads/windows/
pause
exit /b 1
