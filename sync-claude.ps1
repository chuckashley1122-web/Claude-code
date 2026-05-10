# sync-claude.ps1 — sync ~/.claude between this machine and OneDrive.
#
# Usage:
#   .\sync-claude.ps1 pull              Copy from OneDrive to ~/.claude (restore)
#   .\sync-claude.ps1 push              Copy from ~/.claude to OneDrive (backup)
#   .\sync-claude.ps1 pull -DryRun      Preview without copying
#   $env:CLAUDE_ONEDRIVE_PATH = "D:\OneDrive\ClaudeBackup\.claude"   # override target
#
# OneDrive path auto-detected from $env:OneDrive (personal) or $env:OneDriveCommercial.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('pull', 'push')]
    [string]$Direction,

    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$LocalClaude = Join-Path $env:USERPROFILE '.claude'

if ($env:CLAUDE_ONEDRIVE_PATH) {
    $OneDriveClaude = $env:CLAUDE_ONEDRIVE_PATH
} else {
    $OneDriveRoot = $env:OneDrive
    if (-not $OneDriveRoot) { $OneDriveRoot = $env:OneDriveCommercial }
    if (-not $OneDriveRoot) {
        Write-Error "OneDrive not detected. Set CLAUDE_ONEDRIVE_PATH to your backup folder."
        exit 1
    }
    $OneDriveClaude = Join-Path $OneDriveRoot 'ClaudeBackup\.claude'
}

# Files/dirs that must never sync: credentials, machine-local caches, transient state.
$ExcludeFiles = @('.credentials.json', '.lock', '*.log')
$ExcludeDirs  = @('statsig', 'cache', 'shell-snapshots', 'todos', 'ide', 'logs')

if ($Direction -eq 'pull') {
    $Source = $OneDriveClaude
    $Dest   = $LocalClaude
} else {
    $Source = $LocalClaude
    $Dest   = $OneDriveClaude
}

if (-not (Test-Path $Source)) {
    Write-Error "Source not found: $Source"
    exit 1
}

if (-not (Test-Path $Dest)) {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
}

Write-Host "Syncing $Source -> $Dest" -ForegroundColor Cyan
if ($DryRun) { Write-Host "(dry run — no files will be copied)" -ForegroundColor Yellow }

# robocopy: /E recurse, /COPY:DAT preserve attrs, /R:2 /W:2 quick retries,
# /XO skip older (avoid clobbering newer dest), /XF exclude files, /XD exclude dirs.
# Note: no /MIR — additive sync only. Delete on the target side manually if needed.
$rcArgs = @($Source, $Dest, '/E', '/COPY:DAT', '/R:2', '/W:2', '/XO')
if ($DryRun)         { $rcArgs += '/L' }
if ($ExcludeFiles)   { $rcArgs += '/XF'; $rcArgs += $ExcludeFiles }
if ($ExcludeDirs)    { $rcArgs += '/XD'; $rcArgs += $ExcludeDirs }

& robocopy @rcArgs
$rc = $LASTEXITCODE

# robocopy exit codes 0–7 are success (8+ are real errors).
if ($rc -ge 8) {
    Write-Error "robocopy failed with exit code $rc"
    exit $rc
}

Write-Host "Done." -ForegroundColor Green
exit 0
