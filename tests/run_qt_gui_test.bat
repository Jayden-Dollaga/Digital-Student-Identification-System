@echo off
setlocal
cd /d "%~dp0.."

set PYTHON_CMD=python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=python3
    %PYTHON_CMD% --version >nul 2>&1
    if errorlevel 1 (
        echo Python is not installed or not on PATH.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% tests\qt_gui_interactive.py
if errorlevel 1 pause
