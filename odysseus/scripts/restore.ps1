<#
.SYNOPSIS
    Restore the Odysseus data directory from a snapshot.

.DESCRIPTION
    DESTRUCTIVE. Replaces data/ with the contents of the tarball. The script
    verifies the tarball, stops the stack, restores, and leaves the stack
    stopped so you can start it deliberately.

    Requires -Confirm:$false or an interactive 'yes' to proceed.

.EXAMPLE
    .\restore.ps1 -Path backups\odysseus-backup-20260819-120000.tar.gz
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Path,
    [string]$InstallPath = (Join-Path 'C:\AI-Workspaces' 'odysseus'),
    [switch]$Force
)

. "$PSScriptRoot\common.ps1"

$root = Resolve-OdysseusRoot -InstallPath $InstallPath
$tool = Join-Path $root 'scripts\odysseus-backup'

if (-not (Test-Path $tool)) {
    Write-Fail "Upstream backup tool not found at $tool."
    exit 1
}

$python = if (Test-CommandExists 'python') { 'python' } elseif (Test-CommandExists 'python3') { 'python3' } else { $null }

function Invoke-BackupTool([string[]]$ToolArgs) {
    if ($python) {
        return Invoke-Native -Command $python -Arguments (@($tool) + $ToolArgs) -WorkingDirectory $root
    }
    return Invoke-Native -Command 'docker' `
        -Arguments (@('compose', 'exec', '-T', 'odysseus', 'python', 'scripts/odysseus-backup') + $ToolArgs) `
        -WorkingDirectory $root
}

# --------------------------------------------------------------- verify ------
Write-Head 'Verify the snapshot before trusting it'
$v = Invoke-BackupTool @('verify', $Path, '--pretty')
Write-Host $v.Output
if (-not $v.Success) {
    Write-Fail 'Verification failed.'
    Write-Stop 'Nothing was changed. Do not restore from a snapshot that will not verify.'
    exit 1
}
Write-Pass 'Snapshot verified'

# -------------------------------------------------------------- confirm ------
Write-Head 'Confirm'
Write-Host "  This REPLACES $root\data - the database, memory, vault, RAG index, and uploads." -ForegroundColor Yellow
Write-Host '  Current data is not automatically saved first.' -ForegroundColor Yellow

if (-not $Force) {
    $answer = Read-Host "  Type 'yes' to restore from $Path"
    if ($answer -ne 'yes') {
        Write-Info 'Cancelled. Nothing changed.'
        exit 0
    }
}

# ------------------------------------------------------------------ stop -----
Write-Head 'Stopping the stack'
$down = Invoke-Native -Command 'docker' -Arguments @('compose', 'down') -WorkingDirectory $root
if (-not $down.Success) {
    Write-Fail "docker compose down failed:`n$($down.Output)"
    Write-Stop 'Not restoring into a running stack. Resolve the above first.'
    exit 1
}
Write-Pass 'Stack stopped (volumes untouched)'

# --------------------------------------------------------------- restore -----
Write-Head 'Restoring'
# The container is down, so this path needs local Python.
if (-not $python) {
    Write-Fail 'Restore needs Python on the host, because the container is stopped.'
    Write-Info "Install Python 3, then run:  python scripts\odysseus-backup restore `"$Path`" --yes"
    exit 1
}
$r = Invoke-Native -Command $python -Arguments @($tool, 'restore', $Path, '--yes', '--pretty') -WorkingDirectory $root
Write-Host $r.Output

if (-not $r.Success) {
    Write-Fail 'Restore failed. The stack is still stopped.'
    Write-Stop 'Do not start the stack until you know what state data/ is in.'
    exit 1
}

Write-Pass 'Restore complete'
Write-Head 'Next'
Write-Info 'Start the stack:   docker compose up -d'
Write-Info 'Then re-run:       .\verify.ps1'
Write-Info 'Log the restore in BUILD-RECORD.md.'
