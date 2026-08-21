# Shared helpers for the CA&J Odysseus scripts.
# Dot-source it:  . "$PSScriptRoot\common.ps1"

$ErrorActionPreference = 'Stop'

# Ports published by docker-compose.yml. All loopback-bound by default.
$script:OdysseusPorts = @(
    @{ Port = 7000; Service = 'odysseus'; Note = 'web UI' },
    @{ Port = 8080; Service = 'searxng';  Note = 'search'  },
    @{ Port = 8100; Service = 'chromadb'; Note = 'vectors' },
    @{ Port = 8091; Service = 'ntfy';     Note = 'notify'  }
)

function Write-Head($text) {
    Write-Host ''
    Write-Host "== $text" -ForegroundColor Cyan
}

function Write-Pass($text) { Write-Host "  [pass] $text" -ForegroundColor Green }
function Write-Fail($text) { Write-Host "  [FAIL] $text" -ForegroundColor Red }
function Write-Warn($text) { Write-Host "  [warn] $text" -ForegroundColor Yellow }
function Write-Info($text) { Write-Host "  [info] $text" }

function Write-Stop($text) {
    Write-Host ''
    Write-Host "  [STOP] $text" -ForegroundColor Magenta
    Write-Host '         This needs a human decision. Nothing further was changed.' -ForegroundColor Magenta
}

# Default install location. Override with -InstallPath on any script.
function Get-DefaultInstallPath { 'C:\AI-Workspaces\odysseus' }

function Test-CommandExists($name) {
    $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

# Run a native command, returning stdout+stderr and the exit code, without
# throwing. PowerShell's $ErrorActionPreference='Stop' does not apply to native
# exit codes, but stderr-to-exception behaviour differs between hosts, so this
# normalises it.
function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$Command,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $pushed = $false
    try {
        if ($WorkingDirectory) { Push-Location $WorkingDirectory; $pushed = $true }
        $out = & $Command @Arguments 2>&1 | Out-String
        return [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output   = $out.TrimEnd()
            Success  = ($LASTEXITCODE -eq 0)
        }
    } finally {
        if ($pushed) { Pop-Location }
        $ErrorActionPreference = $prev
    }
}

function Test-DockerRunning {
    if (-not (Test-CommandExists 'docker')) { return $false }
    (Invoke-Native -Command 'docker' -Arguments @('info', '--format', '{{.ServerVersion}}')).Success
}

function Test-PortFree {
    <#
      Returns $true (free), $false (in use), or $null (could not determine).

      Never throws. The earlier version called netstat from the catch block, so
      a host without Get-NetTCPConnection AND without netstat threw from inside
      the handler and killed the caller outright — which is what happens on a
      locked-down box where netstat is absent or blocked.
    #>
    param([Parameter(Mandatory)][int]$Port)

    if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
        try {
            $conns = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
            return ($null -eq $conns -or @($conns).Count -eq 0)
        } catch {
            # fall through to the command-line probes
        }
    }

    foreach ($probe in @(
        @{ Cmd = 'netstat'; Args = @('-ano');  Pattern = ":$Port\s+.*LISTEN" },
        @{ Cmd = 'ss';      Args = @('-ltn');  Pattern = ":$Port\s" }
    )) {
        if (-not (Get-Command $probe.Cmd -ErrorAction SilentlyContinue)) { continue }
        try {
            $r = Invoke-Native -Command $probe.Cmd -Arguments $probe.Args
            if ($r.Success -or $r.Output) { return -not ($r.Output -match $probe.Pattern) }
        } catch {
            continue
        }
    }

    return $null   # unknown — the caller decides what to do about that
}

function Resolve-OdysseusRoot {
    param([string]$InstallPath)
    if (-not $InstallPath) { $InstallPath = Get-DefaultInstallPath }
    if (-not (Test-Path $InstallPath)) {
        throw "Odysseus is not installed at '$InstallPath'. Run install.ps1 first, or pass -InstallPath."
    }
    if (-not (Test-Path (Join-Path $InstallPath 'docker-compose.yml'))) {
        throw "'$InstallPath' exists but has no docker-compose.yml. Wrong path?"
    }
    (Resolve-Path $InstallPath).Path
}

# Read a value from .env, ignoring comments. Returns $null if absent.
function Get-EnvValue {
    param(
        [Parameter(Mandatory)][string]$EnvFile,
        [Parameter(Mandatory)][string]$Key
    )
    if (-not (Test-Path $EnvFile)) { return $null }
    foreach ($line in Get-Content $EnvFile) {
        $t = $line.Trim()
        if ($t.StartsWith('#') -or -not $t.Contains('=')) { continue }
        $name = $t.Substring(0, $t.IndexOf('=')).Trim()
        if ($name -eq $Key) { return $t.Substring($t.IndexOf('=') + 1).Trim() }
    }
    return $null
}

# Ensure "Key=Value" is present and uncommented in .env. Rewrites a commented
# "# Key=..." line in place so the file keeps its original ordering/comments.
function Set-EnvValue {
    param(
        [Parameter(Mandatory)][string]$EnvFile,
        [Parameter(Mandatory)][string]$Key,
        [Parameter(Mandatory)][string]$Value
    )
    $lines = @(Get-Content $EnvFile)
    $done = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $t = $lines[$i].Trim()
        if ($t -match "^\s*#?\s*$([regex]::Escape($Key))\s*=") {
            $lines[$i] = "$Key=$Value"
            $done = $true
            break
        }
    }
    if (-not $done) { $lines += "$Key=$Value" }
    Set-Content -Path $EnvFile -Value $lines -Encoding UTF8
}

function Get-AppPort {
    param([Parameter(Mandatory)][string]$Root)
    $v = Get-EnvValue -EnvFile (Join-Path $Root '.env') -Key 'APP_PORT'
    if ($v) { return [int]$v }
    return 7000
}
