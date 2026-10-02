@echo off
setlocal enabledelayedexpansion
title Stopping PotholeSense AI Services

echo ================================================================
echo  Stopping PotholeSense AI and Cloudflare Services
echo ================================================================

:: 1. Terminate Cloudflared
echo [1/4] Stopping Cloudflare Tunnel...
taskkill /f /im cloudflared.exe >nul 2>&1

:: 2. Terminate port 8000 (FastAPI / uvicorn)
echo [2/4] Releasing Port 8000 (FastAPI)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 3. Terminate port 3000 (Next.js)
echo [3/4] Releasing Port 3000 (Next.js)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 4. Terminate Orchestrator PID if present
if exist "server.pid" (
    set /p ORCH_PID=<server.pid
    if defined ORCH_PID (
        taskkill /f /pid !ORCH_PID! >nul 2>&1
    )
    del "server.pid" >nul 2>&1
)

echo.
echo ================================================================
echo  All PotholeSense background processes stopped successfully.
echo ================================================================
ping 127.0.0.1 -n 3 >nul
