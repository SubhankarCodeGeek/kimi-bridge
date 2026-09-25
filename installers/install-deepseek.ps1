param(
    [string]$BaseUrl = $env:KIMIBRIDGE_BASE_URL
)

$Installer = Join-Path $PSScriptRoot "install.ps1"
if ($BaseUrl) {
    & $Installer -Provider deepseek -BaseUrl $BaseUrl @args
} else {
    & $Installer -Provider deepseek @args
}
