$startup = [Environment]::GetFolderPath('Startup')
$target = Join-Path $startup 'PotholeSense-AutoStart.lnk'

if (Test-Path $target) {
    Remove-Item $target -Force
    Write-Host "PotholeSense auto-start shortcut removed successfully."
} else {
    Write-Host "PotholeSense auto-start shortcut was not present."
}
