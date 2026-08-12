@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m PyInstaller --noconfirm --clean DSIS.spec
) else (
    python -m PyInstaller --noconfirm --clean DSIS.spec
)

if errorlevel 1 (
    echo.
    echo PyInstaller build failed.
    exit /b 1
)

echo.
echo Presentation build complete.
echo Output: dist\DSIS\DSIS.exe
