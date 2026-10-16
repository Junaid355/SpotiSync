@echo off
title SpotiSync - Spotify & Spicetify Suite
cd /d "%~dp0"

set "PY_EXE="
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" set "PY_EXE=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
if not defined PY_EXE if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PY_EXE=%LOCALAPPDATA%\Python\bin\python.exe"
if not defined PY_EXE (
    for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
        if exist "%%i\python.exe" set "PY_EXE=%%i\python.exe"
    )
)
if not defined PY_EXE (
    for /d %%i in ("%ProgramFiles%\Python*") do (
        if exist "%%i\python.exe" set "PY_EXE=%%i\python.exe"
    )
)
if not defined PY_EXE (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PY_EXE=py -3"
)
if not defined PY_EXE (
    python --version >nul 2>&1
    if not errorlevel 1 set "PY_EXE=python"
)

if defined PY_EXE (
    echo Launching SpotiSync Suite via %PY_EXE%...
    %PY_EXE% app.py
    if not errorlevel 1 exit /b 0
)

echo.
echo Python Desktop UI not available, falling back to PowerShell Manager...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0SpotifyAutoManager.ps1"
