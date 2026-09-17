@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

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

if not exist "requirements.txt" (
    echo requirements.txt not found in this folder.
    echo Make sure you're running this from the project root.
    pause
    exit /b 1
)

set VENV_DIR=.venv

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo No virtual environment found.
    set /p USE_VENV="Create one now at .venv? (Y/N): "
    if /i "!USE_VENV!"=="Y" (
        echo Creating virtual environment...
        %PYTHON_CMD% -m venv %VENV_DIR%
        if errorlevel 1 (
            echo Failed to create virtual environment.
            pause
            exit /b 1
        )
    )
)

if exist "%VENV_DIR%\Scripts\python.exe" (
    echo Using virtual environment at %VENV_DIR%
    set PYTHON_CMD=%VENV_DIR%\Scripts\python.exe
) else (
    echo Using system %PYTHON_CMD% ^(no venv^)...
)

rem Skip the user cache because a stale or inaccessible cached wheel can block installation.
%PYTHON_CMD% -m pip install --no-cache-dir --upgrade pip
if errorlevel 1 (
    echo Warning: failed to upgrade pip. Continuing anyway...
)

%PYTHON_CMD% -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    echo Please check your Python installation and requirements.txt.
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully.
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo Remember: activate the venv before running the app with:
    echo   %VENV_DIR%\Scripts\activate
)
pause