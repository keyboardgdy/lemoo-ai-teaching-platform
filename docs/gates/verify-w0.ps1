[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$docsRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$results = [System.Collections.Generic.List[object]]::new()

function Add-Check {
    param(
        [string]$Id,
        [bool]$Passed,
        [string]$Detail
    )

    $results.Add([pscustomobject]@{
        id = $Id
        status = if ($Passed) { 'PASS' } else { 'FAIL' }
        detail = $Detail
    })
}

function Read-Text {
    param([string]$Path)
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

$paths = [ordered]@{
    PRD = Join-Path $docsRoot 'product\PRD-001 教育机器人云平台.md'
    RTM = Join-Path $docsRoot 'product\RTM-001 教育机器人云平台需求追踪矩阵.md'
    PILOT = Join-Path $docsRoot 'product\PILOT-001 模拟器工程验证范围.md'
    OWNER = Join-Path $docsRoot 'governance\OWNER-001 责任人与AI执行授权.md'
    BASELINES = Join-Path $docsRoot 'governance\BASELINE-REGISTRY.md'
    DECISIONS = Join-Path $docsRoot 'governance\DECISION-LOG.md'
    RISKS = Join-Path $docsRoot 'governance\RISK-REGISTER.md'
    STACK = Join-Path $docsRoot '01 fastapi-vue-modern-tech-stack.md'
    ARCH = Join-Path $docsRoot '02 fastapi-vue-modern-architecture.md'
    DESIGN = Join-Path $docsRoot '03 ai-teaching-platform-design.md'
    READINESS = Join-Path $docsRoot '04 开发前准备与启动门禁.md'
    SOURCE = Join-Path $docsRoot '入职要求详细.md'
}

foreach ($entry in $paths.GetEnumerator()) {
    Add-Check "W0-FILE-$($entry.Key)" (Test-Path -LiteralPath $entry.Value) $entry.Value
}

if (($results | Where-Object status -eq 'FAIL').Count -gt 0) {
    $results | Format-Table -AutoSize | Out-String | Write-Output
    Write-Output 'W0_RESULT=FAIL'
    exit 1
}

$prd = Read-Text $paths.PRD
$rtm = Read-Text $paths.RTM
$pilot = Read-Text $paths.PILOT
$owner = Read-Text $paths.OWNER
$decisions = Read-Text $paths.DECISIONS
$risks = Read-Text $paths.RISKS
$baselines = Read-Text $paths.BASELINES

Add-Check 'W0-PRD-STATUS' ($prd -match '> 版本：1\.0\.0' -and $prd -match '> 状态：Approved for Stage 1A Simulator-only') 'PRD-001 1.0.0 Stage 1A approval'
Add-Check 'W0-RTM-STATUS' ($rtm -match '> 版本：1\.0\.0' -and $rtm -match '> 状态：Approved for Stage 1A Simulator-only') 'RTM-001 1.0.0 Stage 1A approval'

$approvalPattern = '(?m)^\| (Product Owner|技术 Owner|设备 Owner|安全/隐私 Owner|QA/验收 Owner) \|[^\r\n]*\| 高端阳 \| Approved for Stage 1A \| 2026-08-13 \|$'
$approvalCount = ([regex]::Matches($prd, $approvalPattern)).Count
Add-Check 'W0-OWNERS' ($approvalCount -eq 5) "Named Stage 1A approvals: $approvalCount/5"
Add-Check 'W0-AI-BOUNDARY' ($owner -match 'OpenAI Codex' -and $owner -match '不能承担 `A`') 'AI execution is distinct from human accountability'
Add-Check 'W0-ROLE-RISK' ($owner -match '一人多角色、独立性不足' -and $risks -match 'RISK-001') 'Single-person Stage 1A risk is recorded'

$prdIds = [regex]::Matches($prd, '(?m)^\| (PRD-[A-Z]+-\d{3}) \|') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
$rtmIds = [regex]::Matches($rtm, '(?m)^\| [^\r\n]*?\| (PRD-[A-Z]+-\d{3}) \|') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
$requirementDiff = @(Compare-Object $prdIds $rtmIds)
Add-Check 'W0-TRACE-ID-COUNT' ($prdIds.Count -eq 35 -and $rtmIds.Count -eq 35) "PRD=$($prdIds.Count), RTM=$($rtmIds.Count)"
Add-Check 'W0-TRACE-ID-MATCH' ($requirementDiff.Count -eq 0) "Requirement ID differences: $($requirementDiff.Count)"

$traceRows = $rtm -split "`r?`n" | Where-Object { $_ -match '^\| [^|]+ \| PRD-[A-Z]+-\d{3} \|' }
$invalidTraceRows = foreach ($row in $traceRows) {
    $columns = @($row.Trim('|').Split('|') | ForEach-Object { $_.Trim() })
    if ($columns.Count -ne 7 -or @($columns | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -gt 0 -or $columns[6] -ne 'Approved / Evidence Missing') {
        $row
    }
}
Add-Check 'W0-TRACE-COMPLETE' ($traceRows.Count -eq 35 -and @($invalidTraceRows).Count -eq 0) "Complete approved trace rows: $($traceRows.Count); invalid: $(@($invalidTraceRows).Count)"

Add-Check 'W0-PILOT-SCOPE' ($pilot -match 'ORG-SIM-A' -and $pilot -match 'ORG-SIM-B' -and $pilot -match 'SIM_EDU_ROBOT_V1' -and $pilot -match 'production_supported: false') 'Synthetic tenants and non-production virtual combination are fixed'
Add-Check 'W0-PILOT-DEVICES' (([regex]::Matches($pilot, '(?m)^\| `SIM-[AB]-\d{3}` \|')).Count -eq 6) 'Six simulator devices are registered'
Add-Check 'W0-REAL-SCOPE-BLOCKED' ($pilot -match '真实设备组合 \| Blocked' -and $pilot -match 'blocked_no_physical_device') 'Real device and production claims remain blocked'

$requiredDecisionIds = @('D-002','D-003','D-004','D-006','D-007','D-008','D-009','D-010','D-011','D-012','D-013','D-014','D-015','D-016','D-017','D-018')
$missingDecisions = @($requiredDecisionIds | Where-Object { $decisions -notmatch "(?m)^\| $([regex]::Escape($_)) \|" })
Add-Check 'W0-DECISIONS' ($missingDecisions.Count -eq 0) "Missing decision entries: $($missingDecisions -join ', ')"
Add-Check 'W0-RISKS' (([regex]::Matches($risks, '(?m)^\| RISK-\d{3} \|')).Count -ge 10) 'At least ten current risks have owner, mitigation and status'
Add-Check 'W0-BASELINES' ($baselines -match '01 技术栈' -and $baselines -match '02 生产架构' -and $baselines -match '03 产品与系统设计' -and $baselines -match '04 开发前准备与启动门禁') '01/02/03/04 status, owner and change rules are registered'

$linkErrors = [System.Collections.Generic.List[string]]::new()
$formatErrors = [System.Collections.Generic.List[string]]::new()
foreach ($file in $paths.Values) {
    if (-not $file.EndsWith('.md')) { continue }
    $raw = Read-Text $file
    if ($raw.Contains([char]0xFFFD)) { $formatErrors.Add("Replacement character: $file") }
    $fenceCount = ([regex]::Matches($raw, '(?m)^```')).Count
    if ($fenceCount % 2 -ne 0) { $formatErrors.Add("Unbalanced fences: $file ($fenceCount)") }
    foreach ($match in [regex]::Matches($raw, '\[[^\]]+\]\(([^)]+)\)')) {
        $link = [uri]::UnescapeDataString($match.Groups[1].Value)
        if ($link -match '^(https?:|mailto:|#)') { continue }
        $linkWithoutAnchor = ($link -split '#', 2)[0]
        if ([string]::IsNullOrWhiteSpace($linkWithoutAnchor)) { continue }
        $target = Join-Path (Split-Path -Parent $file) $linkWithoutAnchor
        if (-not (Test-Path -LiteralPath $target)) { $linkErrors.Add("$file -> $link") }
    }
}
Add-Check 'W0-LINKS' ($linkErrors.Count -eq 0) "Broken local links: $($linkErrors.Count)"
Add-Check 'W0-FORMAT' ($formatErrors.Count -eq 0) "Encoding/fence errors: $($formatErrors.Count)"

$results | Format-Table -AutoSize | Out-String -Width 240 | Write-Output
$failed = @($results | Where-Object status -eq 'FAIL')
if ($failed.Count -gt 0) {
    if ($linkErrors.Count -gt 0) { $linkErrors | Write-Output }
    if ($formatErrors.Count -gt 0) { $formatErrors | Write-Output }
    Write-Output "W0_RESULT=FAIL; CHECKS=$($results.Count); FAILED=$($failed.Count)"
    exit 1
}

Write-Output "W0_RESULT=PASS; CHECKS=$($results.Count); FAILED=0"
