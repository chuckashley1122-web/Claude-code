<#
.SYNOPSIS
    Deploy the CA&J workspace skills into a running Odysseus install.

.DESCRIPTION
    Builds the SKILL.md files from source, validates them against Odysseus's own
    parser, and copies them to <odysseus>/data/skills/<category>/<name>/.

    Creates no users and sets no privileges — those are admin actions done in
    the UI, and they must exist first or the skills load for nobody. See
    docs/WORKSPACE-DEPLOYMENT.md.

    A skill already on disk under a different owner is skipped, never
    overwritten.

.EXAMPLE
    .\deploy-workspaces.ps1 -WhatIf
    .\deploy-workspaces.ps1
    .\deploy-workspaces.ps1 -SkipRestart
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$InstallPath = (Join-Path 'C:\AI-Workspaces' 'odysseus'),
    [switch]$SkipRestart
)

. "$PSScriptRoot\common.ps1"

$root     = Resolve-OdysseusRoot -InstallPath $InstallPath
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$tools    = Join-Path $repoRoot 'odysseus\tools'

Write-Host 'Deploy CA&J workspace skills' -ForegroundColor Cyan
Write-Info "odysseus : $root"
Write-Info "kit      : $repoRoot"

# ----------------------------------------------------------------- python ----
Write-Head 'Python'
$python = if (Test-CommandExists 'python') { 'python' } elseif (Test-CommandExists 'python3') { 'python3' } else { $null }
if (-not $python) {
    Write-Fail 'No Python on PATH. The build and validation tools need Python 3.'
    Write-Info 'Install Python 3.11+ from https://www.python.org/downloads/ and re-run.'
    exit 1
}
Write-Pass "$python available"

# ------------------------------------------------------------------ build ----
Write-Head 'Build'
$build = Invoke-Native -Command $python -Arguments @((Join-Path $tools 'build_skills.py'), '--odysseus-root', $root, '--check')
if ($build.Success) {
    Write-Pass 'Committed SKILL.md files are current'
} else {
    Write-Warn 'Committed SKILL.md files are out of date:'
    Write-Host $build.Output
    if ($WhatIfPreference) {
        Write-Info 'Would regenerate them. Nothing written in -WhatIf.'
    } else {
        $regen = Invoke-Native -Command $python -Arguments @((Join-Path $tools 'build_skills.py'), '--odysseus-root', $root)
        if (-not $regen.Success) {
            Write-Fail "Build failed:`n$($regen.Output)"
            exit 1
        }
        Write-Pass 'Regenerated. Commit the result.'
    }
}

# --------------------------------------------------------------- validate ----
Write-Head 'Validate'
$val = Invoke-Native -Command $python -Arguments @((Join-Path $tools 'validate_skills.py'), '--odysseus-root', $root)
Write-Host $val.Output
if (-not $val.Success) {
    Write-Fail 'Validation failed.'
    Write-Stop 'Nothing was deployed. Fix the problems above first — a skill that fails validation may load for nobody, or corrupt itself on first save.'
    exit 1
}
Write-Pass 'All skills valid'

# ------------------------------------------------------- validate sources ----
Write-Head 'Validate knowledge manifests'
$src = Invoke-Native -Command $python -Arguments @((Join-Path $tools 'validate_sources.py'))
Write-Host $src.Output
if (-not $src.Success) {
    Write-Fail 'Manifest validation failed.'
    Write-Stop 'Nothing was deployed. A broken manifest means a source silently never loads, or loads without an approver on record.'
    exit 1
}
Write-Pass 'Manifests and reference sources valid'

# ----------------------------------------------------------- users warning ---
Write-Head 'Prerequisite: business user accounts'
Write-Host @"
  Skills are filtered by owner. These three users must exist in Odysseus, or the
  skills load for nobody:

      caj-enterprises      CA-J Enterprises
      caj-consulting       CA-J Consulting
      caj-grind            Chuck's Daily Grind

  Create them as admin in Settings -> Users, non-admin, one password each.
  The username IS the isolation key — a typo silently hides that business's
  skills rather than erroring.
"@ -ForegroundColor Yellow

if ($WhatIfPreference) {
    Write-Head 'Plan (nothing written)'
    $plan = Invoke-Native -Command $python -Arguments @((Join-Path $tools 'build_skills.py'), '--odysseus-root', $root, '--check')
    Write-Info "Would copy 15 SKILL.md files into $root\data\skills\<category>\<name>\"
    Write-Info 'Would skip any skill already on disk under a different owner.'
    Write-Info "Would then restart the odysseus container$(if ($SkipRestart) { ' (suppressed by -SkipRestart)' })."
    exit 0
}

# ----------------------------------------------------------------- deploy ----
Write-Head 'Deploy'
$dep = Invoke-Native -Command $python -Arguments @((Join-Path $tools 'build_skills.py'), '--odysseus-root', $root, '--deploy')
Write-Host $dep.Output
if (-not $dep.Success) {
    Write-Fail 'Deploy failed.'
    exit 1
}

if ($dep.Output -match 'SKIP') {
    Write-Warn 'One or more skills were skipped because a different owner holds them on disk.'
    Write-Info 'Review those before assuming this workspace is fully deployed.'
}

# ---------------------------------------------------------------- restart ----
if ($SkipRestart) {
    Write-Head 'Restart skipped'
    Write-Info 'Odysseus re-indexes skills on start. Restart before testing:  docker compose restart odysseus'
} else {
    Write-Head 'Restart so Odysseus re-indexes'
    $rs = Invoke-Native -Command 'docker' -Arguments @('compose', 'restart', 'odysseus') -WorkingDirectory $root
    if ($rs.Success) { Write-Pass 'odysseus restarted' }
    else { Write-Warn "Restart failed:`n$($rs.Output)"; Write-Info 'Restart by hand: docker compose restart odysseus' }
}

# ------------------------------------------------------------------- next ----
Write-Head 'Next'
Write-Host @"
  1. Sign in as each business user and confirm Skills shows exactly its own 5.
  2. Paste each workspace system prompt from workspaces\<business>\system-prompt.md
     into that user's assistant settings. They are not auto-deployed.
  3. Run the six tests in workspaces\<business>\tests.md — including the
     prompt-injection test. A workspace is not live until all six pass.

  Order still matters: CA-J Enterprises first, Chuck's Daily Grind second,
  CA-J Consulting last.
"@ -ForegroundColor Cyan
