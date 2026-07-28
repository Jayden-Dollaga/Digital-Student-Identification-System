@echo off
rem GitCommander launcher - portable Git helper
setlocal
set "SCRIPT_DIR=%~dp0"
pwsh -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%gc\main.ps1" %*
endlocal
exit /b %ERRORLEVEL%
