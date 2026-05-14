# launch-chrome-debug.ps1 — launch Chrome with the CDP debug port so Claude
# Code can attach via chrome-devtools-mcp.
#
# Usage:
#   .\launch-chrome-debug.ps1                # default port 9222, refuse if Chrome is running
#   .\launch-chrome-debug.ps1 -Force         # kill any running Chrome first
#   .\launch-chrome-debug.ps1 -Port 9333
#
# After this script exits, Chrome is running with your normal profile and
# CDP is exposed on http://127.0.0.1:<Port>. The .mcp.json in this repo
# tells Claude Code to attach to that endpoint.
#
# NOTE: --remote-debugging-port is silently ignored if any Chrome process is
# already running. Chrome must be fully closed (including background tasks)
# before relaunching, which is why this script refuses to continue otherwise.

[CmdletBinding()]
param(
    [int]$Port = 9222,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$chromeCandidates = @(
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "${env:LocalAppData}\Google\Chrome\Application\chrome.exe"
)
$chrome = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $chrome) {
    Write-Error "chrome.exe not found in standard locations. Install Chrome or edit this script."
    exit 1
}

$running = @(Get-Process chrome -ErrorAction SilentlyContinue)
if ($running.Count -gt 0) {
    if ($Force) {
        Write-Host "Closing $($running.Count) existing Chrome process(es)..." -ForegroundColor Yellow
        $running | Stop-Process -Force
        # Chrome's background tasks can hold the user-data-dir lock briefly.
        Start-Sleep -Seconds 2
    } else {
        Write-Error @"
Chrome is already running ($($running.Count) process(es)). The remote
debugging port is silently ignored when Chrome attaches to an existing
process, so all Chrome windows must be closed first.

Close Chrome and rerun, or pass -Force to kill it automatically.
"@
        exit 1
    }
}

Write-Host "Launching Chrome with --remote-debugging-port=$Port (main profile)..." -ForegroundColor Cyan
Start-Process -FilePath $chrome -ArgumentList "--remote-debugging-port=$Port"

# Probe the endpoint until DevTools answers, so we fail loudly if the flag
# was rejected (e.g. a stray Chrome process we missed).
$endpoint = "http://127.0.0.1:$Port/json/version"
$deadline = (Get-Date).AddSeconds(15)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri $endpoint -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $ready) {
    Write-Error "Chrome started but CDP endpoint $endpoint never responded. Was another Chrome process still running?"
    exit 1
}

Write-Host "Chrome is ready. CDP endpoint: http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "Claude Code will attach via chrome-devtools-mcp (see .mcp.json)." -ForegroundColor Green
