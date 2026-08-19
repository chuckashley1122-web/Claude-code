<#
.SYNOPSIS
    Run the acceptance tests from section 7 of the build guide.

.DESCRIPTION
    Read-only apart from an optional container restart (-TestRestart), which is
    a normal restart and never touches volumes. Exits 1 if any test fails.

.EXAMPLE
    .\verify.ps1
    .\verify.ps1 -TestRestart
#>
[CmdletBinding()]
param(
    [string]$InstallPath = (Join-Path 'C:\AI-Workspaces' 'odysseus'),
    [switch]$TestRestart
)

. "$PSScriptRoot\common.ps1"

$root = Resolve-OdysseusRoot -InstallPath $InstallPath
$port = Get-AppPort -Root $root
$failed = 0

Write-Host "Odysseus acceptance tests - $root" -ForegroundColor Cyan

# ------------------------------------------------------------------- 1-2 -----
Write-Head '1. Compose configuration'
$cfg = Invoke-Native -Command 'docker' -Arguments @('compose', 'config') -WorkingDirectory $root
if ($cfg.Success) { Write-Pass 'docker compose config succeeds' }
else { Write-Fail "docker compose config failed:`n$($cfg.Output)"; $failed++ }

Write-Head '2. Containers'
$psJson = Invoke-Native -Command 'docker' -Arguments @('compose', 'ps', '--format', 'json') -WorkingDirectory $root
if (-not $psJson.Success) {
    Write-Fail 'docker compose ps failed. Is the stack up?'
    $failed++
} else {
    # Compose emits one JSON object per line (older) or a JSON array (newer).
    $containers = @()
    $text = $psJson.Output.Trim()
    if ($text.StartsWith('[')) {
        $containers = $text | ConvertFrom-Json
    } else {
        foreach ($line in $text -split "`r?`n") {
            if ($line.Trim()) { $containers += ($line | ConvertFrom-Json) }
        }
    }
    foreach ($svc in @('odysseus', 'searxng', 'chromadb', 'ntfy')) {
        $c = $containers | Where-Object { $_.Service -eq $svc } | Select-Object -First 1
        if (-not $c) { Write-Fail "$svc is not running"; $failed++; continue }
        $health = if ($c.Health) { " ($($c.Health))" } else { '' }
        if ($c.State -eq 'running') { Write-Pass "$svc running$health" }
        else { Write-Fail "$svc is '$($c.State)'$health"; $failed++ }
    }
}

# --------------------------------------------------------------------- 3 -----
Write-Head '3. UI responds locally'
try {
    $r = Invoke-WebRequest -Uri "http://localhost:$port/" -UseBasicParsing -TimeoutSec 15 -MaximumRedirection 5
    Write-Pass "http://localhost:$port/ returned $($r.StatusCode)"
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code -in 200, 302, 401, 403) { Write-Pass "http://localhost:$port/ returned $code" }
    else { Write-Fail "No usable response on port $port - $($_.Exception.Message)"; $failed++ }
}

# --------------------------------------------------------------------- 4 -----
Write-Head '4. Authentication is enforced'
$protected = '/api/settings'
try {
    $r = Invoke-WebRequest -Uri "http://localhost:$port$protected" -UseBasicParsing -TimeoutSec 15 -MaximumRedirection 0
    if ($r.StatusCode -in 401, 403) {
        Write-Pass "$protected rejected an unauthenticated request ($($r.StatusCode))"
    } else {
        Write-Fail "$protected returned $($r.StatusCode) without credentials. Check AUTH_ENABLED and LOCALHOST_BYPASS."
        $failed++
    }
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code -in 401, 403, 302, 307) { Write-Pass "$protected rejected an unauthenticated request ($code)" }
    else { Write-Warn "Could not evaluate $protected ($($_.Exception.Message)). Check by hand in a private browser window."; }
}

$bypass = Get-EnvValue -EnvFile (Join-Path $root '.env') -Key 'LOCALHOST_BYPASS'
$auth   = Get-EnvValue -EnvFile (Join-Path $root '.env') -Key 'AUTH_ENABLED'
if ($auth -eq 'true')    { Write-Pass 'AUTH_ENABLED=true' }    else { Write-Fail "AUTH_ENABLED is '$auth'"; $failed++ }
if ($bypass -eq 'false') { Write-Pass 'LOCALHOST_BYPASS=false' } else { Write-Fail "LOCALHOST_BYPASS is '$bypass'"; $failed++ }

# --------------------------------------------------------------------- 5 -----
Write-Head '5. Ports are loopback-only'
$portOut = Invoke-Native -Command 'docker' -Arguments @('compose', 'ps', '--format', '{{.Service}} {{.Ports}}') -WorkingDirectory $root
if ($portOut.Success) {
    $exposed = $false
    foreach ($line in ($portOut.Output -split "`r?`n")) {
        if (-not $line.Trim()) { continue }
        if ($line -match '0\.0\.0\.0:|\[::\]:') {
            Write-Fail "Exposed beyond loopback: $line"
            $exposed = $true
            $failed++
        }
    }
    if (-not $exposed) { Write-Pass 'Every published port is bound to 127.0.0.1' }
} else {
    Write-Warn 'Could not read port bindings.'
}

# --------------------------------------------------------------------- 6 -----
Write-Head '6. Data survives a restart'
$db = Join-Path $root 'data\app.db'
if (-not (Test-Path $db)) {
    Write-Warn 'data\app.db not found yet. Complete the first login, then re-run.'
} elseif ($TestRestart) {
    $before = (Get-Item $db).Length
    Write-Info 'Restarting containers (volumes untouched)...'
    $rs = Invoke-Native -Command 'docker' -Arguments @('compose', 'restart') -WorkingDirectory $root
    Start-Sleep -Seconds 10
    if (-not $rs.Success) { Write-Fail 'docker compose restart failed'; $failed++ }
    elseif (-not (Test-Path $db)) { Write-Fail 'app.db disappeared after restart'; $failed++ }
    else {
        $after = (Get-Item $db).Length
        Write-Pass "app.db intact across restart ($before -> $after bytes)"
    }
} else {
    Write-Info 'app.db present. Re-run with -TestRestart to prove it survives a restart.'
}

# --------------------------------------------------------------------- 7 -----
Write-Head '7. No secrets tracked by Git'
$tracked = Invoke-Native -Command 'git' -Arguments @('ls-files') -WorkingDirectory $root
if ($tracked.Success) {
    $bad = @()
    foreach ($f in ($tracked.Output -split "`r?`n")) {
        $n = $f.Trim()
        if (-not $n) { continue }
        if (($n -eq '.env') -or (($n -like '.env.*') -and ($n -ne '.env.example'))) { $bad += $n }
        if (($n -like '*.pem') -or ($n -like '*.key') -or ($n -like 'data/*')) { $bad += $n }
    }
    if ($bad.Count -eq 0) { Write-Pass 'No .env, key, or data file is tracked' }
    else { foreach ($b in ($bad | Select-Object -Unique)) { Write-Fail "Tracked by Git: $b" }; $failed++ }

    $status = Invoke-Native -Command 'git' -Arguments @('status', '--porcelain') -WorkingDirectory $root
    if ($status.Output -match '^\?\? \.env$') { Write-Pass '.env exists and is untracked' }
}

# --------------------------------------------------------------------- 8 -----
Write-Head '8. Documentation present'
foreach ($doc in @('BUILD-RECORD.md')) {
    if (Test-Path (Join-Path $root $doc)) { Write-Pass "$doc exists" }
    else { Write-Fail "$doc missing - copy it from odysseus\docs\BUILD-RECORD.template.md and fill it in"; $failed++ }
}
Write-Info 'CAJ-OPERATIONS.md and CAJ-CUSTOMIZATION-PLAN.md live in this repo under odysseus\docs\.'

# --------------------------------------------------------------------- 9 -----
Write-Head '9. Backup and restore (manual)'
$backups = Join-Path $root 'backups'
if (Test-Path $backups) {
    $snaps = @(Get-ChildItem $backups -Filter '*.tar.gz' -ErrorAction SilentlyContinue)
    if ($snaps.Count -gt 0) {
        Write-Pass "$($snaps.Count) snapshot(s) present, newest $(($snaps | Sort-Object LastWriteTime -Descending)[0].Name)"
    } else { Write-Warn 'backups\ exists but is empty. Run backup.ps1.'; }
} else {
    Write-Warn 'No backup taken yet. Run backup.ps1 before putting real data in.'
}
Write-Info 'A restore has to be tested by hand, once, on purpose. An untested backup is a guess.'

# ---------------------------------------------------------------- summary ----
Write-Head 'Summary'
if ($failed -eq 0) {
    Write-Host '  All automated acceptance tests passed.' -ForegroundColor Green
    Write-Host '  Still manual: change the temp password, connect one model, test a restore.' -ForegroundColor Green
    exit 0
} else {
    Write-Host "  $failed test(s) failed. Fix them before adding business workspaces." -ForegroundColor Red
    exit 1
}
