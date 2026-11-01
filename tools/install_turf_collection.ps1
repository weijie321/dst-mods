[CmdletBinding()]
param(
    [switch]$Preview,
    [string]$ConfigPath = (Join-Path $env:USERPROFILE '.ai\local\config\dst-mod-development\config.json'),
    [string]$VerifiedReport
)

$ErrorActionPreference = 'Stop'
try {
    $ConfigPath = (Resolve-Path -LiteralPath $ConfigPath).Path
    $Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $Source = [IO.Path]::GetFullPath((Join-Path $Config.workspace 'turf-collection'))
    $InstallRoot = if ($Config.deploy_dst_root) { $Config.deploy_dst_root } else { $Config.dst_root }
    $Target = Join-Path $InstallRoot 'mods\turf-collection'
    Write-Host "来源：$Source"
    Write-Host "目标：$Target"

    if (-not $Preview -and -not $VerifiedReport) {
        $Candidates = Get-ChildItem -LiteralPath $Config.evidence_root -Directory |
            Sort-Object Name -Descending
        foreach ($Directory in $Candidates) {
            $Candidate = Join-Path $Directory.FullName 'result.json'
            if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) { continue }
            try { $Report = Get-Content -LiteralPath $Candidate -Raw -Encoding UTF8 | ConvertFrom-Json }
            catch { continue }
            if ($Report.command -eq 'verify' -and $Report.status -eq 'passed' -and $Report.mod -eq $Source) {
                $VerifiedReport = $Candidate
                break
            }
        }
        if (-not $VerifiedReport) { throw '未找到地皮合集的成功验收报告，请先运行 tools/dst.ps1 verify --mod turf-collection。' }
    }

    $DeployArgs = @('deploy', '--config', $ConfigPath, '--mod', 'turf-collection', '--target-root', $InstallRoot)
    $Output = & $Config.python -X utf8 -B (Join-Path $PSScriptRoot 'dst_workflow.py') @DeployArgs
    if ($LASTEXITCODE -ne 0) { throw ($Output -join "`n") }
    $Plan = ($Output -join "`n") | ConvertFrom-Json
    if ($Plan.status -ne 'preview') { throw '部署入口没有返回有效预览，已停止。' }
    Write-Host "预览：新增 $(@($Plan.changes.add).Count)，更新 $(@($Plan.changes.update).Count)，删除 $(@($Plan.changes.delete).Count)，不变 $($Plan.changes.unchanged)。"
    if ($Preview) { Write-Host '仅预览，未复制文件。'; exit 0 }

    Write-Host "验收报告：$VerifiedReport"
    $Output = & $Config.python -X utf8 -B (Join-Path $PSScriptRoot 'dst_workflow.py') @DeployArgs --apply --verified $VerifiedReport
    if ($LASTEXITCODE -ne 0) { throw ($Output -join "`n") }
    $Result = ($Output -join "`n") | ConvertFrom-Json
    if ($Result.status -notin @('applied', 'unchanged') -or -not $Result.hash_verify) { throw '复制未完成或哈希校验未通过。' }
    Write-Host '完成：运行文件已同步并通过哈希校验。'
    if ($Result.backup_dir) { Write-Host "备份：$($Result.backup_dir)" }
    Write-Host "部署报告：$($Result.evidence_dir)"
    Write-Host '客户端：重启游戏，在“创建世界 → 模组 → 服务器模组”中启用“321自用dp”。'
    Write-Host '独立专服：在对应分片的 modoverrides.lua 中启用 turf-collection，重启服务器加载。'
    exit 0
}
catch {
    Write-Host "安装失败：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
