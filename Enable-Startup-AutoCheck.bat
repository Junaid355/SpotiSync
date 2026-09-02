@echo off
title Enable Silent Startup Auto-Check
cd /d "%~dp0"

echo Enabling silent startup auto-check (runs hidden on boot, checks/starts Spotify, and auto-closes with 0 RAM)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0SpotifyAutoManager.ps1" -Startup

echo.
pause
