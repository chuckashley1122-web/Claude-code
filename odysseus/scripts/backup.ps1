<#
.SYNOPSIS
    Snapshot the Odysseus data directory.

.DESCRIPTION
    Wraps the upstream scripts/odysseus-backup tool. Safe to run while the app is
    running - SQLite is copied through its own .backup API.

    The snapshot contains the Fernet encryption key, sessions, and any stored
    provider tokens. Treat the tarball like a password: keep it private, keep it
    out of Git, encrypt offsite copies.

.EXAMPLE
    .\backup.ps1
    .\backup.ps1 -List
    .\backup.ps1 -Verify backups\odysseus-backup-20260819-120000.tar.gz
    .\backup.ps1 -Out D:\backups\odysseus-2026-08-19.tar.gz -IncludeResearch
#>
[CmdletBinding(DefaultParameterSetName = 'Snapshot')]
param(
    [string]$InstallPath = (Join-Path 'C:\AI-Workspaces' 'odysseus'),

    [Parameter(ParameterSetName = 'List')]
    [switch]$List,

    [Parameter(ParameterSetName = 'Verify')]
    [string]$Verify,

    [Parameter(ParameterSetName = 'Snapshot')]
    [string]$Out,

    [Parameter(ParameterSetName = 'Snapshot')]
    [switch]$IncludeResearch,

    [Parameter(ParameterSetName = 'Snapshot')]
    [switch]$IncludeAttachments
)

. "$PSScriptRoot\common.ps1"

$root = Resolve-OdysseusRoot -InstallPath $InstallPath
$tool = Join-Path $root 'scripts\odysseus-backup'

if (-not (Test-Path $tool)) {
    Write-Fail "Upstream backup tool not found at $tool."
    Write-Stop 'The repository layout changed. Read docs/backup-restore.md in the Odysseus repo before backing up by hand.'
    exit 1
}

# The tool is stdlib-only Python, so any python3/python on PATH runs it.
$python = if (Test-CommandExists 'python') { 'python' } elseif (Test-CommandExists 'python3') { 'python3' } else { $null }
if (-not $python) {
    Write-Warn 'No Python on PATH. Falling back to running the tool inside the container.'
}

function Invoke-BackupTool([string[]]$ToolArgs) {
    if ($python) {
        return Invoke-Native -Command $python -Arguments (@($tool) + $ToolArgs) -WorkingDirectory $root
    }
    return Invoke-Native -Command 'docker' `
        -Arguments (@('compose', 'exec', '-T', 'odysseus', 'python', 'scripts/odysseus-backup') + $ToolArgs) `
        -WorkingDirectory $root
}

switch ($PSCmdlet.ParameterSetName) {

    'List' {
        Write-Head 'Snapshots'
        $r = Invoke-BackupTool @('list', '--pretty')
        Write-Host $r.Output
        exit ([int](-not $r.Success))
    }

    'Verify' {
        Write-Head "Verifying $Verify"
        $r = Invoke-BackupTool @('verify', $Verify, '--pretty')
        Write-Host $r.Output
        if ($r.Success) { Write-Pass 'Tarball is intact and safe to restore' }
        else { Write-Fail 'Verification failed. Do not rely on this snapshot.' }
        exit ([int](-not $r.Success))
    }

    'Snapshot' {
        Write-Head 'Creating snapshot'
        $toolArgs = @('snapshot', '--pretty')
        if ($Out)                { $toolArgs += @('--out', $Out) }
        if ($IncludeResearch)    { $toolArgs += '--include-research' }
        if ($IncludeAttachments) { $toolArgs += '--include-attachments' }

        $r = Invoke-BackupTool $toolArgs
        Write-Host $r.Output

        if ($r.Success) {
            Write-Pass 'Snapshot created'
            Write-Warn 'This file contains your encryption key and stored tokens. Keep it private and out of Git.'
            Write-Info 'Verify it now:  .\backup.ps1 -Verify <path from the output above>'
        } else {
            Write-Fail 'Snapshot failed. Do not proceed with an update or a risky change.'
        }
        exit ([int](-not $r.Success))
    }
}
