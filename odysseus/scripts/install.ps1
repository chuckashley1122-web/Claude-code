<#
.SYNOPSIS
    Clone, pin, configure, build, and start Odysseus for local use.

.DESCRIPTION
    Implements steps 4-6 of the build guide. Refuses to overwrite an existing
    non-empty directory. Never creates accounts, never buys anything, never binds
    beyond loopback, never prints or stores a secret.

    Run .\preflight.ps1 first.

.PARAMETER WhatIf
    Print the plan and exit without changing anything.

.EXAMPLE
    .\install.ps1 -WhatIf
    .\install.ps1
    .\install.ps1 -AppPort 7001
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$InstallPath = (Join-Path 'C:\AI-Workspaces' 'odysseus'),
    [string]$Branch      = 'main',
    [string]$RepoUrl     = 'https://github.com/odysseus-dev/odysseus.git',
    [int]$AppPort        = 7000,
    [switch]$SkipBuild
)

. "$PSScriptRoot\common.ps1"

Write-Host 'Odysseus install' -ForegroundColor Cyan
Write-Info "repo   : $RepoUrl"
Write-Info "branch : $Branch"
Write-Info "path   : $InstallPath"
Write-Info "port   : $AppPort (bound to 127.0.0.1)"

# ------------------------------------------------------------ gate checks ----
Write-Head 'Gate checks'

if (-not (Test-CommandExists 'git'))  { Write-Fail 'git not found.';    exit 1 }
if (-not (Test-DockerRunning))        { Write-Fail 'Docker daemon not reachable. Start Docker Desktop.'; exit 1 }
Write-Pass 'git and Docker are available'

if (Test-Path $InstallPath) {
    $items = @(Get-ChildItem -Force $InstallPath)
    if ($items.Count -gt 0) {
        Write-Fail "$InstallPath already exists and is not empty."
        Write-Stop 'Not overwriting. Either pass -InstallPath with a fresh location, or clear that directory yourself after checking what is in it.'
        exit 1
    }
}
Write-Pass 'Install path is safe to use'

# Test-PortFree returns $true / $false / $null. Treat the three cases
# separately: -not $null is $true, so folding unknown into "in use" would both
# block the install and say something untrue about why.
$portFree = Test-PortFree -Port $AppPort
if ($portFree -eq $false) {
    Write-Fail "Port $AppPort is already in use."
    Write-Stop "Re-run with -AppPort 7001 (or another free port). Record the choice in BUILD-RECORD.md."
    exit 1
} elseif ($null -eq $portFree) {
    Write-Warn "Could not determine whether port $AppPort is free on this host. Continuing."
    Write-Info "If the container fails to bind, re-run with -AppPort 7001."
} else {
    Write-Pass "Port $AppPort is free"
}

if ($WhatIfPreference) {
    Write-Head 'Plan (nothing executed)'
    Write-Info "1. git clone --branch $Branch $RepoUrl $InstallPath"
    Write-Info '2. git rev-parse HEAD  -> recorded for BUILD-RECORD.md'
    Write-Info '3. Copy .env.example to .env'
    Write-Info "4. Set AUTH_ENABLED=true, LOCALHOST_BYPASS=false, APP_BIND=127.0.0.1, APP_PORT=$AppPort"
    Write-Info '5. docker compose config'
    Write-Info '6. docker compose up -d --build'
    Write-Info '7. docker compose ps, then report the first-login instructions'
    Write-Host ''
    Write-Host '  Re-run without -WhatIf to execute.' -ForegroundColor Yellow
    exit 0
}

# ----------------------------------------------------------------- clone -----
Write-Head 'Clone'

$parent = Split-Path -Parent $InstallPath
if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }

$clone = Invoke-Native -Command 'git' -Arguments @('clone', '--branch', $Branch, $RepoUrl, $InstallPath)
if (-not $clone.Success) {
    Write-Fail "Clone failed:`n$($clone.Output)"
    exit 1
}
Write-Pass "Cloned branch '$Branch'"

$head = (Invoke-Native -Command 'git' -Arguments @('rev-parse', 'HEAD') -WorkingDirectory $InstallPath).Output.Trim()
Write-Pass "Pinned at commit $head"

# ------------------------------------------------- upstream import guard ------
# main at cf4e240 cannot start: src/agent_loop.py annotates dict[str, Any]
# without importing Any, and the module is imported at app startup. Catch it
# here rather than after a 15-minute build. See docs/BUILD-GUIDE.md section 0.
Write-Head 'Upstream sanity check'
$agentLoop = Join-Path $InstallPath 'src\agent_loop.py'
if (Test-Path $agentLoop) {
    $typingLine = (Select-String -Path $agentLoop -Pattern '^from typing import' | Select-Object -First 1).Line
    $usesAny    = Select-String -Path $agentLoop -Pattern '\bAny\b' -Quiet
    if ($usesAny -and $typingLine -and ($typingLine -notmatch '\bAny\b')) {
        Write-Fail 'This commit cannot start: src/agent_loop.py uses Any but does not import it.'
        Write-Info  "  found: $typingLine"
        Write-Info  '  The app raises NameError on import, in Docker and natively alike.'
        Write-Host ''
        Write-Info  'Options:'
        Write-Info  '  1. Use the dev branch, which has the fix:'
        Write-Info  "       git -C $InstallPath checkout dev"
        Write-Info  '  2. Patch this one line, and record it in BUILD-RECORD.md:'
        Write-Info  "       add Any to the typing import in src\agent_loop.py"
        Write-Stop  'Not building. A build now would succeed and the app would still fail to start.'
        exit 1
    }
    Write-Pass 'agent_loop.py imports resolve'
} else {
    Write-Warn 'src/agent_loop.py not found — repository layout changed; read docs/setup.md.'
}

# ----------------------------------------------------------------- .env ------
Write-Head 'Configuration'

$envFile    = Join-Path $InstallPath '.env'
$envExample = Join-Path $InstallPath '.env.example'

if (-not (Test-Path $envExample)) {
    Write-Fail 'Upstream .env.example is missing. The repository layout changed - read docs/setup.md before continuing.'
    exit 1
}

Copy-Item $envExample $envFile
Write-Pass 'Created .env from .env.example'

# Explicit beats implicit: compose already defaults to these, but writing them
# means a future upstream default change cannot move the security posture
# without showing up in a diff.
Set-EnvValue -EnvFile $envFile -Key 'AUTH_ENABLED'     -Value 'true'
Set-EnvValue -EnvFile $envFile -Key 'LOCALHOST_BYPASS' -Value 'false'
Set-EnvValue -EnvFile $envFile -Key 'APP_BIND'         -Value '127.0.0.1'
Set-EnvValue -EnvFile $envFile -Key 'APP_PORT'         -Value "$AppPort"

foreach ($k in @('AUTH_ENABLED', 'LOCALHOST_BYPASS', 'APP_BIND', 'APP_PORT')) {
    Write-Pass "$k=$(Get-EnvValue -EnvFile $envFile -Key $k)"
}
Write-Info 'No API keys were written. Add model providers in the Settings UI after first login.'

# --------------------------------------------------------------- validate ----
Write-Head 'Validate Compose configuration'

$cfg = Invoke-Native -Command 'docker' -Arguments @('compose', 'config') -WorkingDirectory $InstallPath
if (-not $cfg.Success) {
    Write-Fail "docker compose config failed:`n$($cfg.Output)"
    Write-Stop 'The stack was not started. Fix the configuration error above first.'
    exit 1
}
Write-Pass 'docker compose config succeeded'

if ($cfg.Output -match '0\.0\.0\.0:') {
    Write-Fail 'A published port resolves to 0.0.0.0. That exposes the service beyond this machine.'
    Write-Stop 'Not starting. Check APP_BIND, CHROMADB_BIND, and NTFY_BIND in .env.'
    exit 1
}
Write-Pass 'All published ports are loopback-bound'

if ($SkipBuild) {
    Write-Head 'Done (build skipped)'
    Write-Info "Start it yourself with: docker compose up -d --build   (in $InstallPath)"
    exit 0
}

# ------------------------------------------------------------------ build ----
Write-Head 'Build and start'
Write-Info 'First build pulls base images and installs dependencies - 5-15 minutes is normal.'

$up = Invoke-Native -Command 'docker' -Arguments @('compose', 'up', '-d', '--build') -WorkingDirectory $InstallPath
if (-not $up.Success) {
    Write-Fail "docker compose up failed:`n$($up.Output)"
    Write-Stop "Read the first error above. Containers may be partially up - check with: docker compose ps"
    exit 1
}
Write-Pass 'Containers started'

$ps = Invoke-Native -Command 'docker' -Arguments @('compose', 'ps') -WorkingDirectory $InstallPath
Write-Host $ps.Output

# ---------------------------------------------------------------- summary ----
Write-Head 'Next steps'

Write-Host @"
  1. Wait for the odysseus container to leave 'starting' - it waits on the
     SearXNG healthcheck. Watch it with:
         docker compose ps

  2. Find the first-login password in the container log:
         docker compose logs odysseus | Select-String "Temporary password"

  3. Open http://localhost:$AppPort and log in as 'admin'.

  4. Change that password immediately in Settings. Do not paste it into a
     Claude Code prompt, a document, a screenshot, or a commit.

  5. Record this build:
         Copy-Item "<repo>\odysseus\docs\BUILD-RECORD.template.md" "$InstallPath\BUILD-RECORD.md"
     Commit hash for that file:  $head

  6. Run the acceptance tests:
         .\verify.ps1

  Not done here, on purpose: no accounts created, no API keys added, no paid
  service touched, nothing exposed beyond 127.0.0.1.
"@ -ForegroundColor Cyan
