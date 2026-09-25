param(
    [string]$Provider = $env:KIMIBRIDGE_PROVIDER,
    [string]$BaseUrl = $env:KIMIBRIDGE_BASE_URL,
    [switch]$DeepSeek,
    [switch]$Kimi,
    [switch]$All,
    [switch]$Binary
)

$ErrorActionPreference = "Stop"

if ($DeepSeek) { $Provider = "deepseek" }
if ($Kimi) { $Provider = "kimi" }
if ($All) { $Provider = "all" }

$ConfigDir = Join-Path $env:USERPROFILE ".kimibridge"
if (-not $Provider) {
    if ([Environment]::UserInteractive) {
        Write-Host ""
        Write-Host "Select your target AI provider for Android Studio / LLM clients:"
        Write-Host "  1) DeepSeek (https://api.deepseek.com) [Recommended]"
        Write-Host "  2) Kimi / Moonshot AI (https://api.moonshot.ai)"
        Write-Host "  3) All Providers (exposes both DeepSeek and Kimi models)"
        $choice = Read-Host "Enter choice [1-3, default: 1]"
        switch ($choice) {
            "2" { $Provider = "kimi" }
            "3" { $Provider = "all" }
            default { $Provider = "deepseek" }
        }
    } else {
        if (-not (Test-Path (Join-Path $ConfigDir "config.json"))) {
            $Provider = "deepseek"
        }
    }
}

$InstallDir = if ($env:KIMIBRIDGE_INSTALL_DIR) { $env:KIMIBRIDGE_INSTALL_DIR } else { Join-Path $env:USERPROFILE ".kimibridge\app" }
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

Write-Host "Cleaning up any existing installation and background services..."
Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}

# Stop any running processes named kimibridge or python running kimibridge
Get-Process -Name "kimibridge" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "python*", "py*" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -and $_.CommandLine -like "*kimibridge*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

Write-Host "Checking for existing binaries to remove..."
$BinaryCandidates = @(
    (Join-Path $InstallDir "bin\kimibridge.exe"),
    (Join-Path $ConfigDir "bin\kimibridge.exe")
)
foreach ($binPath in $BinaryCandidates) {
    if (Test-Path $binPath) {
        Write-Host "Removing existing binary: $binPath"
        Remove-Item -Path $binPath -Force -ErrorAction SilentlyContinue
    }
}

if (-not $Binary) {
    $DistDir = Join-Path $RepoRoot "dist"
    if (Test-Path $DistDir) {
        Write-Host "Removing existing build artifacts: $DistDir"
        Remove-Item -Path $DistDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    $BuildDir = Join-Path $RepoRoot "build"
    if (Test-Path $BuildDir) {
        Remove-Item -Path $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if (Test-Path $InstallDir) {
    Write-Host "Removing previous installation directory: $InstallDir"
    Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

Copy-Item -Path (Join-Path $RepoRoot "*") -Destination $InstallDir -Recurse -Force

$BinaryCandidate = Join-Path $RepoRoot "dist\kimibridge-windows-x86_64.exe"
if ($Binary -and (Test-Path $BinaryCandidate)) {
    Write-Host "Found standalone binary artifact: $BinaryCandidate"
    $BinDir = Join-Path $InstallDir "bin"
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    Copy-Item -Path $BinaryCandidate -Destination (Join-Path $BinDir "kimibridge.exe") -Force
    $ExecPath = Join-Path $BinDir "kimibridge.exe"
    $ExecArgs = "start --auto-port"
} else {
    if ($Binary) {
        Write-Host "Standalone binary not found at $BinaryCandidate. Falling back to Python runtime."
    }
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

if ($Provider) {
    Write-Host ""
    Write-Host "Configuring provider: $Provider"
    if ($ExecPath -eq $PythonBin) {
        if ($BaseUrl) {
            & $PythonBin -m kimibridge.cli setup $Provider --base-url $BaseUrl
        } else {
            & $PythonBin -m kimibridge.cli setup $Provider
        }
    } else {
        if ($BaseUrl) {
            & $ExecPath setup $Provider --base-url $BaseUrl
        } else {
            & $ExecPath setup $Provider
        }
    }
}

Write-Host ""
Write-Host "KimiBridge is installed."
if ($ExecPath -eq $PythonBin) {
    & $PythonBin -m kimibridge.cli config show
} else {
    & $ExecPath config show
}
Write-Host ""
Write-Host "Use the endpoint above in Android Studio as an OpenAI-compatible provider."
