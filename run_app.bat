@echo off
REM Compatibility launcher for the legacy Python workflow; use run_qt_gui.bat for the active Qt UI.
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Determine a working Python command
set PYTHON_CMD=python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=python3
    %PYTHON_CMD% --version >nul 2>&1
    if errorlevel 1 (
        echo Python is not installed or not on PATH.
        echo Install Python 3 and try again.
        pause
        exit /b 1
    )
)

echo Starting GUI app...
%PYTHON_CMD% python\main.py
if errorlevel 1 (
    echo Application exited with errors.
) else (
    echo Application finished.
)
pause