[CmdletBinding()]
param(
    [string]$Mod = 'wanda-skilltree',
    [ValidateSet('static', 'server', 'full')][string]$Mode = 'server',
    [int]$RuntimeTimeout = 240,
    [string]$Plan,
    [string]$Config,
    [switch]$Strict,
    [switch]$KeepTemp,
    [string]$DstRoot,
    [string]$KleiRoot,
    [int]$ServerPort,
    [int]$ClientTimeout
)
$ErrorActionPreference = 'Stop'
# 常用旧命令转发；不再读取历史分析目录中的自测器。Strict 始终生效。
foreach ($Legacy in @('KeepTemp', 'DstRoot', 'KleiRoot', 'ServerPort', 'ClientTimeout')) {
    if ($PSBoundParameters.ContainsKey($Legacy)) {
        throw "旧参数 -$Legacy 已停用。环境路径请使用 -Config；测试端口和临时目录由统一入口隔离管理。"
    }
}
$Command = @{ static = 'check'; server = 'test'; full = 'verify' }[$Mode]
$Forward = @($Command, '--mod', $Mod)
if ($Mode -ne 'static') { $Forward += @('--timeout', $RuntimeTimeout.ToString()) }
if ($Plan) {
    if ($Mode -eq 'server') { throw '-Plan 用于 static/full；独立服务端场景请使用 dst.ps1 test --script。' }
    $Forward += @('--plan', $Plan)
}
if ($Config) { $Forward += @('--config', $Config) }
& (Join-Path $PSScriptRoot 'dst.ps1') @Forward
exit $LASTEXITCODE
