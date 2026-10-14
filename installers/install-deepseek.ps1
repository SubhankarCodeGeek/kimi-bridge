param(
    [string]$BaseUrl = $env:KIMIBRIDGE_BASE_URL,
    [int]$Port = 0
)

$Installer = Join-Path $PSScriptRoot "install.ps1"
$splat = @{
    Provider = "deepseek"
}
if ($BaseUrl) { $splat["BaseUrl"] = $BaseUrl }
if ($Port -gt 0) { $splat["Port"] = $Port }
& $Installer @splat @args
