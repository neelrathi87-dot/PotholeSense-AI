$WshShell = New-Object -ComObject WScript.Shell
$startup = [Environment]::GetFolderPath('Startup')
$target = Join-Path $startup 'PotholeSense-AutoStart.lnk'
$projDir = "C:\Users\neeln\Projects\Ai-Thon"

$Shortcut = $WshShell.CreateShortcut($target)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$projDir\run_background.vbs`""
$Shortcut.WorkingDirectory = $projDir
$Shortcut.Description = "Starts PotholeSense AI and Cloudflare 24/7 silently on Windows boot"
$Shortcut.Save()

Write-Host "PotholeSense 24/7 Auto-Start installed successfully at:"
Write-Host " $target"
