@echo off
title Remove PotholeSense Auto-Start

echo ================================================================
echo  Removing PotholeSense from Windows Startup
echo ================================================================

powershell -ExecutionPolicy Bypass -File "%~dp0remove_startup.ps1"

echo.
echo ================================================================
echo  PotholeSense auto-start has been disabled.
echo ================================================================
echo.
pause
