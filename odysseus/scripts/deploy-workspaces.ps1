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
    [switch]$SkipProvision,
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
    Write-Info "1. Copy 15 SKILL.md files into $root\data\skills\<category>\<name>\"
    Write-Info '   Skipping any skill already on disk under a different owner.'
    Write-Info "2. Restart the odysseus container$(if ($SkipRestart) { ' (suppressed)' })"
    Write-Info '3. Create users caj-enterprises, caj-consulting, caj-grind'
    Write-Info '   Set privileges, load system prompts, apply tool allowlists'
    Write-Info '4. Verify: prompts loaded, no denied tool granted, isolation holds'
    Write-Host ''
    $plan = Invoke-Tool 'provision_workspaces.py' @('--url', $Url)
    Write-Host $plan.Output
    exit 0
}

# ----------------------------------------------------------------- deploy ----
# Skills first: they are files, need no auth, and must be on disk before the
# restart so Odysseus indexes them and the verify step can see them.
Write-Head 'Deploy skills'
$dep = Invoke-Tool 'build_skills.py' @('--odysseus-root', $root, '--deploy')
Write-Host $dep.Output
if (-not $dep.Success) { Write-Fail 'Deploy failed.'; exit 1 }
if ($dep.Output -match 'SKIP') {
    Write-Warn 'Some skills were skipped — a different owner holds them on disk. Review before assuming this is fully deployed.'
}

# ---------------------------------------------------------------- restart ----
if ($SkipRestart) {
    Write-Head 'Restart skipped'
    Write-Warn 'Odysseus indexes skills at start. Provisioning will verify against a stale index until you restart.'
} else {
    Write-Head 'Restart so Odysseus indexes the skills'
    $rs = Invoke-Native -Command 'docker' -Arguments @('compose', 'restart', 'odysseus') -WorkingDirectory $root
    if ($rs.Success) {
        Write-Pass 'odysseus restarted'
        Write-Info 'Waiting for it to come back...'
        $ready = $false
        foreach ($attempt in 1..30) {
            Start-Sleep -Seconds 2
            try {
                $null = Invoke-WebRequest -Uri "$Url/" -UseBasicParsing -TimeoutSec 5 -MaximumRedirection 5
                $ready = $true; break
            } catch {
                $code = $_.Exception.Response.StatusCode.value__
                if ($code -in 200, 302, 401, 403) { $ready = $true; break }
            }
        }
        if ($ready) { Write-Pass 'Odysseus is responding' }
        else { Write-Warn 'Odysseus did not respond within 60s. Check: docker compose logs --tail=120 odysseus' }
    } else {
        Write-Warn "Restart failed:`n$($rs.Output)"
        Write-Info 'Restart by hand: docker compose restart odysseus'
    }
}

# -------------------------------------------------------------- provision ----
if ($SkipProvision) {
    Write-Head 'Provisioning skipped'
    Write-Info 'Run it later:'
    Write-Info "  $python $tools\provision_workspaces.py --url $Url --apply --then-verify"
    exit 0
}

Write-Head 'Provision the three workspaces'
Write-Host @"
  This creates users caj-enterprises, caj-consulting and caj-grind, then loads
  each workspace's system prompt and tool allowlist.

  You will be asked for the Odysseus admin password. It is not stored, not
  logged, and not echoed.

  Three generated passwords print once at the end. Save them then.
"@ -ForegroundColor Yellow

$provArgs = @((Join-Path $tools 'provision_workspaces.py'), '--url', $Url, '--admin-user', $AdminUser, '--apply', '--then-verify')
if ($Model) { $provArgs += @('--model', $Model) }

# Run in the foreground, not through Invoke-Native: the admin password prompt
# needs the real console, and the output must not be captured into a variable
# that could end up in a transcript.
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
