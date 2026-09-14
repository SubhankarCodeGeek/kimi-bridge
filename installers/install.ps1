$ErrorActionPreference = "Stop"

$InstallDir = if ($env:KIMIBRIDGE_INSTALL_DIR) { $env:KIMIBRIDGE_INSTALL_DIR } else { Join-Path $env:USERPROFILE ".kimibridge\app" }
$ConfigDir = Join-Path $env:USERPROFILE ".kimibridge"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$TaskName = "KimiBridge"

function Find-Python {
    $python = Get-Command py -ErrorAction SilentlyContinue
    if ($python) {
        return "py"
    }

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3) {
        return "python3"
    }

    $pythonExe = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonExe) {
        return "python"
    }

    throw "Python is required until native binaries are published."
}

Write-Host "KimiBridge Installer"
Write-Host "Install directory: $InstallDir"

$PythonBin = Find-Python
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

Copy-Item -Path (Join-Path $RepoRoot "*") -Destination $InstallDir -Recurse -Force

Push-Location $InstallDir
try {
    & $PythonBin -m kimibridge.cli start --auto-port --save-port --dry-run
}
finally {
    Pop-Location
}

$Action = New-ScheduledTaskAction -Execute $PythonBin -Argument "-m kimibridge.cli start --auto-port" -WorkingDirectory $InstallDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal

Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "KimiBridge is installed."
& $PythonBin -m kimibridge.cli config show
Write-Host ""
Write-Host "Use the endpoint above in Android Studio as an OpenAI-compatible provider."
