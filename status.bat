@echo off
setlocal enabledelayedexpansion
title PotholeSense AI Service Status

echo ================================================================
echo  PotholeSense AI Service Status and Live Links
echo ================================================================

:: Check Port 8000
netstat -aon | findstr :8000 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] FastAPI AI Server   : RUNNING (Port 8000)
) else (
    echo  [--] FastAPI AI Server   : STOPPED
)

:: Check Port 3000
netstat -aon | findstr :3000 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Next.js Dashboard   : RUNNING (Port 3000)
) else (
    echo  [--] Next.js Dashboard   : STOPPED
)

:: Check Cloudflare Process
tasklist /fi "imagename eq cloudflared.exe" | findstr /i "cloudflared.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Cloudflare Tunnel   : RUNNING
) else (
    echo  [--] Cloudflare Tunnel   : STOPPED
)

echo ----------------------------------------------------------------
if exist "active_tunnel_url.txt" (
    set /p TUNNEL_URL=<active_tunnel_url.txt
    echo  Live Cloudflare HTTPS : !TUNNEL_URL!
    echo  Mobile Patrol Camera  : !TUNNEL_URL!/mobile
    echo  Health Check Endpoint : !TUNNEL_URL!/health
) else (
    echo  No active Cloudflare tunnel URL detected.
)
echo  Local Municipal Map   : http://localhost:3000
echo  Local API Docs        : http://localhost:8000/docs
echo ================================================================

if exist "servers.log" (
    echo Recent Log Activity (last 10 entries):
    powershell -command "Get-Content servers.log -Tail 10"
)
echo ================================================================
pause
