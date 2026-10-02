$WshShell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$projDir = "C:\Users\neeln\Projects\Ai-Thon"

# 1. Start Silent Shortcut
$p1 = Join-Path $desktop "Start PotholeSense.lnk"
$s1 = $WshShell.CreateShortcut($p1)
$s1.TargetPath = "wscript.exe"
$s1.Arguments = "`"$projDir\run_background.vbs`""
$s1.WorkingDirectory = $projDir
$s1.Description = "Start PotholeSense AI and Cloudflare in background (no windows)"
$s1.Save()

# 2. Stop Shortcut
$p2 = Join-Path $desktop "Stop PotholeSense.lnk"
$s2 = $WshShell.CreateShortcut($p2)
$s2.TargetPath = Join-Path $projDir "stop_background.bat"
$s2.WorkingDirectory = $projDir
$s2.Description = "Stop PotholeSense servers and Cloudflare"
$s2.Save()

# 3. Status Shortcut
$p3 = Join-Path $desktop "PotholeSense Status.lnk"
$s3 = $WshShell.CreateShortcut($p3)
$s3.TargetPath = Join-Path $projDir "status.bat"
$s3.WorkingDirectory = $projDir
$s3.Description = "Check PotholeSense server status, live Cloudflare URL, and logs"
$s3.Save()

Write-Host "Created 3 shortcuts on Desktop:"
Write-Host " 1. Start PotholeSense.lnk"
Write-Host " 2. Stop PotholeSense.lnk"
Write-Host " 3. PotholeSense Status.lnk"
