[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$ToolArguments)
$ErrorActionPreference = 'Stop'
$ConfigPath = Join-Path $env:USERPROFILE '.ai\local\config\dst-mod-development\config.json'
for ($i = 0; $i -lt $ToolArguments.Count - 1; $i++) {
    if ($ToolArguments[$i] -eq '--config') { $ConfigPath = $ToolArguments[$i + 1] }
}
if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw '缺少配置。先运行 ~/.ai/tools/scripts/setup-dst-mod-workflow.ps1。'
}
$Config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
if (-not (Test-Path -LiteralPath $Config.python -PathType Leaf)) {
    throw '配置中的 Python 不存在，请重新运行 setup-dst-mod-workflow.ps1。'
}
& $Config.python -X utf8 -B (Join-Path $PSScriptRoot 'dst_workflow.py') @ToolArguments
exit $LASTEXITCODE
