@echo off
title SpotiSync - Spotify & Spicetify Suite
cd /d "%~dp0"

echo Launching SpotiSync Suite...
python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Python Desktop UI not available, falling back to PowerShell Manager...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0SpotifyAutoManager.ps1"
)
