param(
    [string]$Provider = "",
    [switch]$All = $false
)

$ErrorActionPreference = "Stop"

$InstallDir = if ($env:STUDIORELAY_INSTALL_DIR) {
    $env:STUDIORELAY_INSTALL_DIR
} elseif ($env:KIMIBRIDGE_INSTALL_DIR) {
    $env:KIMIBRIDGE_INSTALL_DIR
} else {
    Join-Path $env:USERPROFILE ".studiorelay\app"
}
$LegacyInstallDir = Join-Path $env:USERPROFILE ".kimibridge\app"
$ConfigDir = Join-Path $env:USERPROFILE ".studiorelay"
$LegacyConfigDir = Join-Path $env:USERPROFILE ".kimibridge"

function Normalize-Provider([string]$p) {
    if (-not $p) { return "" }
    $clean = $p.Trim().ToLowerInvariant()
    if ($clean -eq "moonshot") { return "kimi" }
    return $clean
}

$NormalizedProvider = Normalize-Provider $Provider

if ($NormalizedProvider -and -not $All) {
    $TitleProvider = $NormalizedProvider.Substring(0, 1).ToUpper() + $NormalizedProvider.Substring(1)
    $TaskCandidates = @(
        "StudioRelay-$TitleProvider",
        "StudioRelay-$NormalizedProvider",
        "KimiBridge-$TitleProvider",
        "KimiBridge-$NormalizedProvider"
    )

    foreach ($tName in $TaskCandidates) {
        if (Get-ScheduledTask -TaskName $tName -ErrorAction SilentlyContinue) {
            Stop-ScheduledTask -TaskName $tName -ErrorAction SilentlyContinue
            Unregister-ScheduledTask -TaskName $tName -Confirm:$false
        }
    }

    # Stop processes explicitly running this provider
    Get-Process -Name "python*", "py*", "studiorelay*", "kimibridge*" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -and $_.CommandLine -like "*$NormalizedProvider*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    $hasOther = $false
    foreach ($cdir in @($ConfigDir, $LegacyConfigDir)) {
        if (Test-Path $cdir) {
            $otherConfigs = Get-ChildItem -Path $cdir -Filter "config-*.json" -ErrorAction SilentlyContinue | Where-Object {
                $_.Name -ne "config-$NormalizedProvider.json"
            }
            if ($otherConfigs -and $otherConfigs.Count -gt 0) {
                $hasOther = $true
            }
        }
    }

    if ($hasOther) {
        Write-Host "StudioRelay ($NormalizedProvider) background service was stopped and removed."
        Write-Host "Other configured providers remain active. Shared binaries at $InstallDir were preserved."
        Write-Host "User config remains preserved at $ConfigDir\config-$NormalizedProvider.json"
        exit 0
    }
} else {
    Get-ScheduledTask -TaskPath "\" -ErrorAction SilentlyContinue | Where-Object {
        $_.TaskName -like "StudioRelay*" -or $_.TaskName -like "KimiBridge*"
    } | ForEach-Object {
        Stop-ScheduledTask -TaskName $_.TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false
    }

    Get-Process -Name "studiorelay*", "kimibridge*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "python*", "py*" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -and ($_.CommandLine -like "*studiorelay*" -or $_.CommandLine -like "*kimibridge*")
    } | Stop-Process -Force -ErrorAction SilentlyContinue
}

$BinCandidates = @(
    (Join-Path $InstallDir "bin\studiorelay.exe"),
    (Join-Path $InstallDir "bin\kimibridge.exe"),
    (Join-Path $env:USERPROFILE ".studiorelay\bin\studiorelay.exe"),
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
if ($All -and (Test-Path $LegacyInstallDir)) {
    Remove-Item -Path $LegacyInstallDir -Recurse -Force
}

if ($NormalizedProvider) {
    Write-Host "StudioRelay ($NormalizedProvider) service, binaries, and app files were removed."
    Write-Host "User config remains preserved at $ConfigDir\config-$NormalizedProvider.json"
} else {
    Write-Host "All StudioRelay services, binaries, and app files were removed."
    Write-Host "User configs remain safely preserved in $ConfigDir"
}
