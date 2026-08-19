<#
.SYNOPSIS
    Safely update Odysseus to the latest commit on the tracked branch.

.DESCRIPTION
    Default run is a dry run: it snapshots, fetches, and shows you exactly what
    would land, then stops. Pass -Apply to actually pull and rebuild.

    Uses --ff-only on purpose. If the pull is refused, you have local changes and
    that is a decision for you to make, not for Git to guess at.

.EXAMPLE
    .\update.ps1
    .\update.ps1 -Apply
#>
[CmdletBinding()]
param(
    [string]$InstallPath = (Join-Path 'C:\AI-Workspaces' 'odysseus'),
    [string]$Branch = 'main',
    [switch]$Apply,
    [switch]$SkipBackup
)

. "$PSScriptRoot\common.ps1"

$root = Resolve-OdysseusRoot -InstallPath $InstallPath
Write-Host "Odysseus update - $root (branch $Branch)" -ForegroundColor Cyan

# ------------------------------------------------------------ local state ----
Write-Head 'Local state'
$before = (Invoke-Native -Command 'git' -Arguments @('rev-parse', 'HEAD') -WorkingDirectory $root).Output.Trim()
Write-Info "Current commit: $before"

$status = Invoke-Native -Command 'git' -Arguments @('status', '--porcelain') -WorkingDirectory $root
$dirty = @()
foreach ($line in ($status.Output -split "`r?`n")) {
    $l = $line.Trim()
    if (-not $l) { continue }
    # .env and data/ are expected to be untracked; everything else is a real edit.
    if ($l -match '^\?\? (\.env|data/|logs/|backups/)') { continue }
    $dirty += $l
}
if ($dirty.Count -gt 0) {
    Write-Warn 'Working tree has changes beyond the expected untracked files:'
    foreach ($d in $dirty) { Write-Host "        $d" }
    Write-Info 'A --ff-only pull will still work if these are untracked, but tracked edits will block it.'
} else {
    Write-Pass 'Working tree is clean apart from .env / data / logs / backups'
}

# ---------------------------------------------------------------- backup -----
if (-not $SkipBackup) {
    Write-Head 'Backup first'
    $b = & "$PSScriptRoot\backup.ps1" -InstallPath $root
    if ($LASTEXITCODE -ne 0) {
        Write-Fail 'Backup failed.'
        Write-Stop 'Not updating without a working backup. Fix the backup first, or re-run with -SkipBackup if you have accepted that risk deliberately.'
        exit 1
    }
} else {
    Write-Warn 'Backup skipped by request. Rollback will only cover code, not data.'
}

# ----------------------------------------------------------------- fetch -----
Write-Head 'Fetch'
$fetch = Invoke-Native -Command 'git' -Arguments @('fetch', '--all', '--prune') -WorkingDirectory $root
if (-not $fetch.Success) {
    Write-Fail "git fetch failed:`n$($fetch.Output)"
    exit 1
}
Write-Pass 'Fetched'

$incoming = Invoke-Native -Command 'git' -Arguments @('log', '--oneline', "HEAD..origin/$Branch") -WorkingDirectory $root
if (-not $incoming.Output.Trim()) {
    Write-Pass "Already up to date with origin/$Branch. Nothing to do."
    exit 0
}

Write-Head "Incoming commits (HEAD..origin/$Branch)"
Write-Host $incoming.Output

$breaking = @()
foreach ($line in ($incoming.Output -split "`r?`n")) {
    if ($line -match '(?i)breaking|migrat|schema|BREAKING CHANGE|remove|drop ') { $breaking += $line }
}
if ($breaking.Count -gt 0) {
    Write-Warn 'These commits mention migrations or removals - read them properly before applying:'
    foreach ($b in $breaking) { Write-Host "        $b" -ForegroundColor Yellow }
}

if (-not $Apply) {
    Write-Head 'Dry run complete'
    Write-Info 'Nothing was pulled or rebuilt.'
    Write-Info 'Read the commits above and the upstream release notes, then re-run with -Apply.'
    exit 0
}

# ------------------------------------------------------------------ pull -----
Write-Head 'Pull'
$pull = Invoke-Native -Command 'git' -Arguments @('pull', '--ff-only', 'origin', $Branch) -WorkingDirectory $root
if (-not $pull.Success) {
    Write-Fail "git pull --ff-only failed:`n$($pull.Output)"
    Write-Stop 'You have local commits or edits that would need merging. Decide what to do with them before updating. Nothing was rebuilt.'
    exit 1
}
$after = (Invoke-Native -Command 'git' -Arguments @('rev-parse', 'HEAD') -WorkingDirectory $root).Output.Trim()
Write-Pass "Updated $before -> $after"

# ---------------------------------------------------------------- rebuild ----
Write-Head 'Rebuild and restart'
$up = Invoke-Native -Command 'docker' -Arguments @('compose', 'up', '-d', '--build') -WorkingDirectory $root
if (-not $up.Success) {
    Write-Fail "docker compose up failed:`n$($up.Output)"
    Write-Head 'Rollback'
    Write-Host @"
        docker compose down
        git checkout $before
        docker compose up -d --build
"@ -ForegroundColor Yellow
    Write-Info 'If the failed version already migrated the database, restore the snapshot taken above as well.'
    exit 1
}
Write-Pass 'Rebuilt and started'

Write-Head 'Next'
Write-Info 'Run the acceptance tests:  .\verify.ps1'
Write-Info "Record in BUILD-RECORD.md:  $before -> $after, plus the backup filename."
Write-Info "Rollback commit if needed:  $before"
