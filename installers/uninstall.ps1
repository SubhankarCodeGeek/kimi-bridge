$ErrorActionPreference = "Stop"

$InstallDir = if ($env:KIMIBRIDGE_INSTALL_DIR) { $env:KIMIBRIDGE_INSTALL_DIR } else { Join-Path $env:USERPROFILE ".kimibridge\app" }
$TaskName = "KimiBridge"

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Get-Process -Name "kimibridge" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "python*", "py*" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -and $_.CommandLine -like "*kimibridge*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

$BinCandidates = @(
    (Join-Path $InstallDir "bin\kimibridge.exe"),
    (Join-Path $env:USERPROFILE ".kimibridge\bin\kimibridge.exe")
)
foreach ($binPath in $BinCandidates) {
    if (Test-Path $binPath) {
        Remove-Item -Path $binPath -Force -ErrorAction SilentlyContinue
    }
}

if (Test-Path $InstallDir) {
    Remove-Item -Path $InstallDir -Recurse -Force
}

Write-Host "KimiBridge service, binaries, and app files were removed."
Write-Host "User config remains at $env:USERPROFILE\.kimibridge\config.json"
