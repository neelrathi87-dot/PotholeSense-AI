@echo off
title Create Desktop Shortcuts for PotholeSense

echo ================================================================
echo  Creating Desktop Shortcuts for PotholeSense AI
echo ================================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -comObject WScript.Shell; $desk = [Environment]::GetFolderPath('Desktop'); $s1 = $WshShell.CreateShortcut(\"$desk\Start PotholeSense (Silent).lnk\"); $s1.TargetPath = 'wscript.exe'; $s1.Arguments = '\"C:\Users\neeln\Projects\Ai-Thon\run_background.vbs\"'; $s1.WorkingDirectory = 'C:\Users\neeln\Projects\Ai-Thon'; $s1.Description = 'Start PotholeSense AI and Cloudflare in background'; $s1.Save(); $s2 = $WshShell.CreateShortcut(\"$desk\Stop PotholeSense.lnk\"); $s2.TargetPath = 'C:\Users\neeln\Projects\Ai-Thon\stop_background.bat'; $s2.WorkingDirectory = 'C:\Users\neeln\Projects\Ai-Thon'; $s2.Description = 'Stop PotholeSense servers and Cloudflare'; $s2.Save(); $s3 = $WshShell.CreateShortcut(\"$desk\PotholeSense Status.lnk\"); $s3.TargetPath = 'C:\Users\neeln\Projects\Ai-Thon\status.bat'; $s3.WorkingDirectory = 'C:\Users\neeln\Projects\Ai-Thon'; $s3.Description = 'Check PotholeSense status and get Cloudflare link'; $s3.Save(); Write-Host 'Desktop shortcuts created successfully!'"

echo.
echo ================================================================
echo  3 Shortcuts placed on your Desktop:
echo   1. Start PotholeSense (Silent)
echo   2. Stop PotholeSense
echo   3. PotholeSense Status
echo ================================================================
echo.
pause
