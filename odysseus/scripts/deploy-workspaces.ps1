<#
.SYNOPSIS
    Set up all three CA&J business workspaces on a running Odysseus install.

.DESCRIPTION
    Phase two, end to end, in one command:

        validate  →  deploy skills  →  restart  →  provision  →  verify

    Provisioning creates the three business users, sets their privileges, and
    loads each one's system prompt and tool allowlist. The tool allowlist is
    what makes draft-only real: send_email and reply_to_email are not granted,
    so the agent cannot call them regardless of what any prompt says.

    Requires the Odysseus admin password, which is typed interactively, never
    stored, and never echoed. The three generated user passwords are printed
    once at the end — save them before closing the terminal.

    Nothing here sends, publishes, or exposes anything.

.EXAMPLE
    .\deploy-workspaces.ps1 -WhatIf
    .\deploy-workspaces.ps1
    .\deploy-workspaces.ps1 -Model "gpt-4o" -SkipRestart
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$InstallPath = (Join-Path 'C:\AI-Workspaces' 'odysseus'),
    [string]$Url         = '',
    [string]$AdminUser   = 'admin',
    [string]$Model       = '',
    [switch]$SkipRestart
)

. "$PSScriptRoot\common.ps1"

$root     = Resolve-OdysseusRoot -InstallPath $InstallPath
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$tools    = Join-Path $repoRoot 'odysseus\tools'
if (-not $Url) { $Url = "http://localhost:$(Get-AppPort -Root $root)" }

Write-Host 'CA&J workspace deployment' -ForegroundColor Cyan
Write-Info "odysseus : $root"
Write-Info "kit      : $repoRoot"
Write-Info "url      : $Url"

# ----------------------------------------------------------------- python ----
Write-Head 'Python'
$python = if (Test-CommandExists 'python') { 'python' } elseif (Test-CommandExists 'python3') { 'python3' } else { $null }
if (-not $python) {
    Write-Fail 'No Python on PATH. The build, validation, and provisioning tools need Python 3.'
    Write-Info 'Install Python 3.11+ from https://www.python.org/downloads/ and re-run.'
    exit 1
}
Write-Pass "$python available"

function Invoke-Tool([string]$Name, [string[]]$ToolArgs) {
    Invoke-Native -Command $python -Arguments (@((Join-Path $tools $Name)) + $ToolArgs)
}

# --------------------------------------------------------------- validate ----
Write-Head 'Validate'

$build = Invoke-Tool 'build_skills.py' @('--odysseus-root', $root, '--check')
if ($build.Success) {
    Write-Pass 'Committed SKILL.md files are current'
} elseif ($WhatIfPreference) {
    Write-Warn 'SKILL.md files are out of date; would regenerate.'
} else {
    Write-Warn 'SKILL.md files are out of date; regenerating.'
    $regen = Invoke-Tool 'build_skills.py' @('--odysseus-root', $root)
    if (-not $regen.Success) { Write-Fail "Build failed:`n$($regen.Output)"; exit 1 }
    Write-Pass 'Regenerated — commit the result'
}

$vs = Invoke-Tool 'validate_skills.py' @('--odysseus-root', $root)
Write-Host $vs.Output
if (-not $vs.Success) {
    Write-Fail 'Skill validation failed.'
    Write-Stop 'Nothing deployed. A skill that fails validation may load for nobody, or corrupt itself on first save.'
    exit 1
}

$vsrc = Invoke-Tool 'validate_sources.py' @()
Write-Host $vsrc.Output
if (-not $vsrc.Success) {
    Write-Fail 'Manifest validation failed.'
    Write-Stop 'Nothing deployed. A broken manifest means a source silently never loads, or loads with no approver on record.'
    exit 1
}
Write-Pass 'Skills and manifests valid'

# ------------------------------------------------------------------- plan ----
if ($WhatIfPreference) {
    Write-Head 'Plan (nothing written)'
    Write-Info '1. Create users caj-enterprises, caj-consulting, caj-grind; set privileges'
    Write-Info "2. Copy 15 SKILL.md files into $root\data\skills\<category>\<name>\"
    Write-Info "3. Restart odysseus$(if ($SkipRestart) { ' (suppressed)' }) — users MUST exist by now,"
    Write-Info '   or Odysseus reassigns every skill to admin and isolation is lost'
    Write-Info '4. Load each system prompt and tool allowlist'
    Write-Info '5. Verify: prompts loaded, no denied tool granted, isolation holds'
    Write-Host ''
    $plan = Invoke-Tool 'provision_workspaces.py' @('--url', $Url)
    Write-Host $plan.Output
    exit 0
}

# -------------------------------------------------------------- provision ----
# Order matters and is not cosmetic. Odysseus reassigns any skill whose owner is
# not a current user to the primary admin at startup (backfill_owner, called
# from app.py). Deploying skills before the business users exist rewrites all
# fifteen SKILL.md files to owner: admin on disk, silently, and isolation is
# gone. Verified against a live install.
#
# provision_workspaces.py --orchestrate runs the whole sequence in one process,
# in the only order that survives that: create users -> deploy skills ->
# restart -> configure -> verify. Keeping it in one process also means the
# generated passwords stay in memory for the verify step.
Write-Head 'Provision all three workspaces'
Write-Host @"
  Creates users caj-enterprises, caj-consulting and caj-grind, deploys the 15
  skills, restarts Odysseus, loads each system prompt and tool allowlist, then
  verifies that isolation holds.

  You will be asked once for the Odysseus admin password. It is not stored, not
  logged, and not echoed.

  Three generated passwords print once at the end. Save them then.
"@ -ForegroundColor Yellow

$provArgs = @(
    (Join-Path $tools 'provision_workspaces.py'),
    '--url', $Url,
    '--admin-user', $AdminUser,
    '--apply', '--orchestrate', '--then-verify',
    '--odysseus-root', $root
)
if ($Model)       { $provArgs += @('--model', $Model) }
if ($SkipRestart) { $provArgs += @('--restart-cmd', '') }

# Foreground, not through Invoke-Native: the admin password prompt needs the
# real console, and the output must not be captured into a variable that could
# end up in a transcript.
& $python @provArgs
$provisionExit = $LASTEXITCODE

Write-Head 'Result'
if ($provisionExit -eq 0) {
    Write-Pass 'All three workspaces provisioned, isolated, and verified'
    Write-Host @"

  Still to do, and no script can do them:

    1. Connect one model in Settings, if you have not already.
    2. Fill in each workspace's approved/ documents — brand voice, product
       catalogue, pricing. Skills refuse unsourced claims, so they produce
       flagged placeholders until these exist.
    3. Run the six tests in workspaces\<business>\tests.md, signed in as that
       business user. A workspace is not live until all six pass.

  Order by risk: CA-J Enterprises, then Chuck's Daily Grind, then CA-J Consulting.
"@ -ForegroundColor Cyan
} else {
    Write-Fail 'Provisioning reported problems — read the output above.'
    Write-Info "Re-run just this step:  $python $tools\provision_workspaces.py --url $Url --verify"
    exit 1
}
