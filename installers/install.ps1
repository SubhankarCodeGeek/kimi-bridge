param(
    [string]$Provider = $(if ($env:STUDIORELAY_PROVIDER) { $env:STUDIORELAY_PROVIDER } else { $env:KIMIBRIDGE_PROVIDER }),
    [string]$BaseUrl = $(if ($env:STUDIORELAY_BASE_URL) { $env:STUDIORELAY_BASE_URL } else { $env:KIMIBRIDGE_BASE_URL }),
    [int]$Port = 0,
    [switch]$DeepSeek,
    [switch]$Kimi,
    [switch]$All,
    [switch]$Binary
)

$ErrorActionPreference = "Stop"

if ($DeepSeek) { $Provider = "deepseek" }
if ($Kimi) { $Provider = "kimi" }
if ($All) { $Provider = "all" }

$ConfigDir = Join-Path $env:USERPROFILE ".studiorelay"
$LegacyConfigDir = Join-Path $env:USERPROFILE ".kimibridge"

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
        if (-not (Test-Path (Join-Path $ConfigDir "config.json")) -and -not (Test-Path (Join-Path $LegacyConfigDir "config.json"))) {
            $Provider = "deepseek"
        }
    }
}

$NormalizedProvider = if ($Provider) { $Provider.ToLower() } else { "" }
if ($NormalizedProvider -eq "moonshot") { $NormalizedProvider = "kimi" }
$TaskName = if ($NormalizedProvider -and $NormalizedProvider -ne "all") { "StudioRelay-$NormalizedProvider" } else { "StudioRelay" }

$InstallDir = if ($env:STUDIORELAY_INSTALL_DIR) {
    $env:STUDIORELAY_INSTALL_DIR
} elseif ($env:KIMIBRIDGE_INSTALL_DIR) {
    $env:KIMIBRIDGE_INSTALL_DIR
} else {
    Join-Path $env:USERPROFILE ".studiorelay\app"
}
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

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

Write-Host "StudioRelay Installer"
Write-Host "Target Provider: $NormalizedProvider"
Write-Host "Scheduled Task:  $TaskName"
Write-Host "Install directory: $InstallDir"

Write-Host "Checking for existing task: $TaskName..."
Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}

# Also remove legacy KimiBridge scheduled tasks to prevent port collision
$LegacyTaskCandidates = @("KimiBridge", "KimiBridge-$NormalizedProvider")
foreach ($legTask in $LegacyTaskCandidates) {
    Get-ScheduledTask -TaskName $legTask -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "Found legacy task $legTask. Stopping and removing to prevent conflict..."
        Stop-ScheduledTask -TaskName $legTask -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $legTask -Confirm:$false -ErrorAction SilentlyContinue
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
        Write-Host "Removing existing build artifacts: $BuildDir"
        Remove-Item -Path $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

Copy-Item -Path (Join-Path $RepoRoot "*") -Destination $InstallDir -Recurse -Force

# Migrate legacy configs if present and new config missing
if ((Test-Path $LegacyConfigDir) -and -not (Test-Path (Join-Path $ConfigDir "config.json"))) {
    try {
        $py = Find-Python
        & $py -c "import sys; sys.path.insert(0, '$RepoRoot'); from studiorelay.config import migrate_legacy_configuration; migrate_legacy_configuration()"
    } catch {}
}

$ProviderArg = if ($NormalizedProvider -and $NormalizedProvider -ne "all") { "--provider $NormalizedProvider" } else { "" }

$BinaryCandidate = Join-Path $RepoRoot "dist\studiorelay-windows-x86_64.exe"
if (-not (Test-Path $BinaryCandidate)) {
    $BinaryCandidate = Join-Path $RepoRoot "dist\kimibridge-windows-x86_64.exe"
}

if ($Binary -and (Test-Path $BinaryCandidate)) {
    Write-Host "Found standalone binary artifact: $BinaryCandidate"
    $BinDir = Join-Path $InstallDir "bin"
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    Copy-Item -Path $BinaryCandidate -Destination (Join-Path $BinDir "studiorelay.exe") -Force
    Copy-Item -Path $BinaryCandidate -Destination (Join-Path $BinDir "kimibridge.exe") -Force
    $ExecPath = Join-Path $BinDir "studiorelay.exe"
    $ExecArgs = "start $ProviderArg --auto-port".Trim()
} else {
    if ($Binary) {
        Write-Host "Standalone binary not found at $BinaryCandidate. Falling back to Python runtime."
    }
    $PythonBin = Find-Python
    $ExecPath = $PythonBin
    $ExecArgs = "-m studiorelay.cli start $ProviderArg --auto-port".Trim()
}

Push-Location $InstallDir
try {
    if ($NormalizedProvider) {
        Write-Host ""
        Write-Host "Configuring provider settings: $NormalizedProvider"
        $setupArgs = @("setup", $NormalizedProvider, "--no-restart")
        if ($BaseUrl) { $setupArgs += @("--base-url", $BaseUrl) }
        if ($Port -gt 0) { $setupArgs += @("--port", "$Port") }

        if ($ExecPath -eq $PythonBin) {
            & $PythonBin -m studiorelay.cli @setupArgs
        } else {
            & $ExecPath @setupArgs
        }
    } else {
        $dryRunArgs = @("start", "--auto-port", "--save-port", "--dry-run")
        if ($Port -gt 0) { $dryRunArgs += @("--port", "$Port") }

        if ($ExecPath -eq $PythonBin) {
            & $PythonBin -m studiorelay.cli @dryRunArgs
        } else {
            & $ExecPath @dryRunArgs
        }
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
Write-Host "============================================================"
Write-Host "  StudioRelay ($NormalizedProvider) is installed!"
Write-Host "============================================================"
if ($ExecPath -eq $PythonBin) {
    & $PythonBin -m studiorelay.cli status
} else {
    & $ExecPath status
}
Write-Host "============================================================"
Write-Host "Use the endpoint above in Android Studio as an OpenAI-compatible provider."
