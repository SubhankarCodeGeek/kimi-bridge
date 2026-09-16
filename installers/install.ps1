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

    throw "Python 3 is required on host when standalone binary is not built. Please install Python 3 or build a standalone binary via python scripts\build_binary.py."
}

Write-Host "KimiBridge Installer"
Write-Host "Install directory: $InstallDir"

Write-Host "Cleaning up any existing installation..."
Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}
if (Test-Path $InstallDir) {
    Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

Copy-Item -Path (Join-Path $RepoRoot "*") -Destination $InstallDir -Recurse -Force

$BinaryCandidate = Join-Path $RepoRoot "dist\kimibridge-windows-x86_64.exe"
if (Test-Path $BinaryCandidate) {
    Write-Host "Found standalone binary artifact: $BinaryCandidate"
    $BinDir = Join-Path $InstallDir "bin"
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    Copy-Item -Path $BinaryCandidate -Destination (Join-Path $BinDir "kimibridge.exe") -Force
    $ExecPath = Join-Path $BinDir "kimibridge.exe"
    $ExecArgs = "start --auto-port"
} else {
    Write-Host "Standalone binary not found. Falling back to Python runtime."
    $PythonBin = Find-Python
    $ExecPath = $PythonBin
    $ExecArgs = "-m kimibridge.cli start --auto-port"
}

Push-Location $InstallDir
try {
    if ($ExecPath -eq $PythonBin) {
        & $PythonBin -m kimibridge.cli start --auto-port --save-port --dry-run
    } else {
        & $ExecPath start --auto-port --save-port --dry-run
    }
}
finally {
    Pop-Location
}

$Action = New-ScheduledTaskAction -Execute $ExecPath -Argument $ExecArgs -WorkingDirectory $InstallDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal

Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "KimiBridge is installed."
if ($ExecPath -eq $PythonBin) {
    & $PythonBin -m kimibridge.cli config show
} else {
    & $ExecPath config show
}
Write-Host ""
Write-Host "Use the endpoint above in Android Studio as an OpenAI-compatible provider."
