@echo off
setlocal

:: Install_CP210x_Driver.bat
:: Lives in root\driver
:: Downloads, extracts, and keeps driver files in root\driver\install
:: so that folder can be gitignored.
:: Driver installs require admin rights, so this re-launches itself
:: elevated if it wasn't started as admin.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator permission...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

:: Script is in root\driver. All zip/extracted files go in root\driver\install.
set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%SCRIPT_DIR%install"
set "ZIP_FILE=%INSTALL_DIR%\CP210x_Universal_Windows_Driver.zip"
set "INF_FILE="

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo.
echo ============================================
echo  Installing CP210x USB to UART Bridge Driver
echo ============================================
echo.

:find_existing_inf
:: First use an already extracted driver without downloading or unzipping.
if exist "%INSTALL_DIR%\silabser.inf" set "INF_FILE=%INSTALL_DIR%\silabser.inf"
if not defined INF_FILE for /d %%D in ("%INSTALL_DIR%\*") do if exist "%%~fD\silabser.inf" set "INF_FILE=%%~fD\silabser.inf"
if defined INF_FILE goto install_driver

:: If the ZIP is already present, reuse it and skip the download.
if exist "%ZIP_FILE%" goto unzip_driver

:: Download the official Silicon Labs driver package when neither file exists.
echo Downloading the official CP210x driver package...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.silabs.com/documents/public/software/CP210x_Universal_Windows_Driver.zip' -OutFile '%ZIP_FILE%'"
if errorlevel 1 (
    echo ERROR: Driver download failed.
    echo Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
if not exist "%ZIP_FILE%" (
    echo ERROR: Driver download did not create the ZIP file.
    echo.
    pause
    exit /b 1
)

:unzip_driver
:: Extract into root\driver\install. Keep the ZIP as a reusable local copy.
echo Extracting the CP210x driver package...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP_FILE%' -DestinationPath '%INSTALL_DIR%' -Force"
if errorlevel 1 (
    echo ERROR: Driver ZIP extraction failed.
    echo.
    pause
    exit /b 1
)

:: Look for silabser.inf in install\ and one level of subfolders.
if exist "%INSTALL_DIR%\silabser.inf" set "INF_FILE=%INSTALL_DIR%\silabser.inf"
if not defined INF_FILE for /d %%D in ("%INSTALL_DIR%\*") do if exist "%%~fD\silabser.inf" set "INF_FILE=%%~fD\silabser.inf"

if not defined INF_FILE (
    echo ERROR: silabser.inf was not found after extracting the driver ZIP.
    echo.
    pause
    exit /b 1
)

:install_driver
pnputil /add-driver "%INF_FILE%" /install

echo.
echo ============================================
echo  Done. Check Device Manager under
echo  "Ports (COM ^& LPT)" for the new COM port.
echo  (You may need to unplug/replug the ESP32
echo  if it doesn't show up right away.)
echo ============================================
echo.
pause