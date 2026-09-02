@echo off
title Silent Background Test
cd /d "%~dp0"

echo Running invisible background check now (NO UI will appear)...
wscript.exe "%~dp0BackgroundStartupCheck.vbs"

echo Check executed and auto-closed. 0 RAM remaining.
pause
