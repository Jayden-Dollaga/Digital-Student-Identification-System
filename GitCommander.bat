@echo off
rem GitCommander launcher - portable Git helper
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%gc\main.ps1" %*

exit /b %ERRORLEVEL%
@echo off
REM Git Commander - launcher
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0gc\main.ps1" %*
endlocal
