@echo off
rem Installer: copies the PowerShell hooks into .git/hooks (POSIX shell wrappers)
setlocal
for %%I in ("%~dp0..") do set "REPO_ROOT=%%~fI\"
set "HOOKS_DIR=%REPO_ROOT%.git\hooks"
if not exist "%HOOKS_DIR%" (
    echo .git/hooks not found. Are you in a git repository root?
    pause
    exit /b 1
)
echo Installing pre-commit hook...
set "HOOK_FILE=%HOOKS_DIR%\pre-commit"
(
echo #!/bin/sh
echo pwsh -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%gc\hooks\pre-commit.ps1" "$@"
) > "%HOOK_FILE%"
attrib -r "%HOOK_FILE%" 2>nul
echo Hook written to %HOOK_FILE%
echo Installing post-commit hook...
set "HOOK_FILE=%HOOKS_DIR%\post-commit"
(
echo #!/bin/sh
echo pwsh -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%gc\hooks\post-commit.ps1" "$@"
) > "%HOOK_FILE%"
attrib -r "%HOOK_FILE%" 2>nul
echo Hook written to %HOOK_FILE%
echo Ensure Git can execute hooks (on Windows: use Git Bash or ensure pwsh in PATH).
pause
endlocal
