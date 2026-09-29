@echo off
REM Launches the DSIS v3 HTML/pywebview interface.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
	".venv\Scripts\python.exe" run_web_gui.py
) else (
	python run_web_gui.py
)
pause
