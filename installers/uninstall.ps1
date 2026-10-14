param(
    [string]$Provider = "",
    [switch]$All = $false
)

$ErrorActionPreference = "Stop"

$InstallDir = if ($env:KIMIBRIDGE_INSTALL_DIR) { $env:KIMIBRIDGE_INSTALL_DIR } else { Join-Path $env:USERPROFILE ".kimibridge\app" }
$ConfigDir = Join-Path $env:USERPROFILE ".kimibridge"

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
        "KimiBridge-$TitleProvider",
        "KimiBridge-$NormalizedProvider"
    )

    foreach ($tName in $TaskCandidates) {
        if (Get-ScheduledTask -TaskName $tName -ErrorAction SilentlyContinue) {
            Stop-ScheduledTask -TaskName $tName -ErrorAction SilentlyContinue
            Unregister-ScheduledTask -TaskName $tName -Confirm:$false
        }
    }

    # Stop any python processes explicitly running this provider
    Get-Process -Name "python*", "py*", "kimibridge*" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -and $_.CommandLine -like "*$NormalizedProvider*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    $hasOther = $false
    if (Test-Path $ConfigDir) {
        $otherConfigs = Get-ChildItem -Path $ConfigDir -Filter "config-*.json" -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -ne "config-$NormalizedProvider.json"
        }
        if ($otherConfigs -and $otherConfigs.Count -gt 0) {
            $hasOther = $true
        }
    }

    if ($hasOther) {
        Write-Host "KimiBridge ($NormalizedProvider) background service was stopped and removed."
        Write-Host "Other configured providers remain active. Shared binaries at $InstallDir were preserved."
        Write-Host "User config remains at $ConfigDir\config-$NormalizedProvider.json"
        exit 0
    }
} else {
    Get-ScheduledTask -TaskPath "\" -ErrorAction SilentlyContinue | Where-Object {
        $_.TaskName -like "KimiBridge*"
    } | ForEach-Object {
        Stop-ScheduledTask -TaskName $_.TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false
    }

    Get-Process -Name "kimibridge*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "python*", "py*" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -and $_.CommandLine -like "*kimibridge*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
}

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

if ($NormalizedProvider) {
    Write-Host "KimiBridge ($NormalizedProvider) service, binaries, and app files were removed."
    Write-Host "User config remains at $ConfigDir\config-$NormalizedProvider.json"
} else {
    Write-Host "All KimiBridge services, binaries, and app files were removed."
    Write-Host "User configs remain in $ConfigDir"
}
