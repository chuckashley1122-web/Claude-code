# start-chrome-debug.ps1
# Launches Chrome with remote debugging enabled so Claude Code's
# chrome-devtools MCP server can attach and control tabs.
#
# Usage (PowerShell):
#   .\start-chrome-debug.ps1
#
# Notes:
# - Uses a dedicated user-data directory so this debug session does NOT
#   collide with your normal Chrome window (Chrome refuses to enable the
#   debug port on a profile that already has a running instance).
# - To use your real signed-in profile, close ALL Chrome windows first,
#   then pass -UseDefaultProfile.

[CmdletBinding()]
param(
    [int]$Port = 9222,
    [switch]$UseDefaultProfile,
    [string]$StartUrl = "https://www.google.com"
)

$ErrorActionPreference = "Stop"

# Find chrome.exe in the usual install locations.
$candidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
)
$chrome = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $chrome) {
    Write-Error "chrome.exe not found in standard locations. Install Chrome or edit this script."
    exit 1
}

$chromeArgs = @("--remote-debugging-port=$Port")

if (-not $UseDefaultProfile) {
    $debugProfile = Join-Path $env:LocalAppData "ChromeDebugProfile"
    if (-not (Test-Path $debugProfile)) {
        New-Item -ItemType Directory -Path $debugProfile | Out-Null
    }
    $chromeArgs += "--user-data-dir=$debugProfile"
}

$chromeArgs += $StartUrl

Write-Host "Launching Chrome with debug port $Port..." -ForegroundColor Cyan
Write-Host "  $chrome $($chromeArgs -join ' ')" -ForegroundColor DarkGray

Start-Process -FilePath $chrome -ArgumentList $chromeArgs

Write-Host ""
Write-Host "Chrome is now controllable by Claude Code via http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "Open Claude Code desktop, run /mcp, and you should see chrome-devtools listed." -ForegroundColor Green
