param(
    [string]$Provider = $env:KIMIBRIDGE_PROVIDER,
    [string]$BaseUrl = $env:KIMIBRIDGE_BASE_URL,
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

$NormalizedProvider = if ($Provider) { $Provider.ToLower() } else { "" }
if ($NormalizedProvider -eq "moonshot") { $NormalizedProvider = "kimi" }
$TaskName = if ($NormalizedProvider -and $NormalizedProvider -ne "all") { "KimiBridge-$NormalizedProvider" } else { "KimiBridge" }

$InstallDir = if ($env:KIMIBRIDGE_INSTALL_DIR) { $env:KIMIBRIDGE_INSTALL_DIR } else { Join-Path $env:USERPROFILE ".kimibridge\app" }
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

Write-Host "KimiBridge Installer"
Write-Host "Target Provider: $NormalizedProvider"
Write-Host "Scheduled Task:  $TaskName"
Write-Host "Install directory: $InstallDir"

Write-Host "Checking for existing task: $TaskName..."
Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}

# If migrating from legacy KimiBridge task for this provider
if ($TaskName -ne "KimiBridge") {
    $LegacyConfig = Join-Path $ConfigDir "config.json"
    if (Test-Path $LegacyConfig) {
        try {
            $legacyJson = Get-Content $LegacyConfig -Raw | ConvertFrom-Json
            if ($legacyJson.provider -eq $NormalizedProvider) {
                Write-Host "Migrating legacy KimiBridge task to $TaskName..."
                Get-ScheduledTask -TaskName "KimiBridge" -ErrorAction SilentlyContinue | ForEach-Object {
                    Stop-ScheduledTask -TaskName "KimiBridge" -ErrorAction SilentlyContinue
                    Unregister-ScheduledTask -TaskName "KimiBridge" -Confirm:$false -ErrorAction SilentlyContinue
                }
            }
        } catch {}
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

$ProviderArg = if ($NormalizedProvider -and $NormalizedProvider -ne "all") { "--provider $NormalizedProvider" } else { "" }

$BinaryCandidate = Join-Path $RepoRoot "dist\kimibridge-windows-x86_64.exe"
if ($Binary -and (Test-Path $BinaryCandidate)) {
    Write-Host "Found standalone binary artifact: $BinaryCandidate"
    $BinDir = Join-Path $InstallDir "bin"
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    Copy-Item -Path $BinaryCandidate -Destination (Join-Path $BinDir "kimibridge.exe") -Force
    $ExecPath = Join-Path $BinDir "kimibridge.exe"
    $ExecArgs = "start $ProviderArg --auto-port".Trim()
} else {
    if ($Binary) {
        Write-Host "Standalone binary not found at $BinaryCandidate. Falling back to Python runtime."
    }
    $PythonBin = Find-Python
    $ExecPath = $PythonBin
    $ExecArgs = "-m kimibridge.cli start $ProviderArg --auto-port".Trim()
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
            & $PythonBin -m kimibridge.cli @setupArgs
        } else {
            & $ExecPath @setupArgs
        }
    } else {
        $dryRunArgs = @("start", "--auto-port", "--save-port", "--dry-run")
        if ($Port -gt 0) { $dryRunArgs += @("--port", "$Port") }

        if ($ExecPath -eq $PythonBin) {
            & $PythonBin -m kimibridge.cli @dryRunArgs
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
Write-Host "  KimiBridge ($NormalizedProvider) is installed!"
Write-Host "============================================================"
if ($ExecPath -eq $PythonBin) {
    & $PythonBin -m kimibridge.cli status
} else {
    & $ExecPath status
}
Write-Host "============================================================"
Write-Host "Use the endpoint above in Android Studio as an OpenAI-compatible provider."
