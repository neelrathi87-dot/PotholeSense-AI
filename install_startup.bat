@echo off
title Install PotholeSense Auto-Start on Boot

echo ================================================================
echo  Installing PotholeSense to Windows Startup (24/7 Auto-Start)
echo ================================================================

powershell -ExecutionPolicy Bypass -File "%~dp0setup_startup.ps1"

echo.
echo ================================================================
echo  PotholeSense will now start automatically whenever your laptop
echo  boots up or you log in! Zero terminal windows will appear.
echo ================================================================
echo.
pause
