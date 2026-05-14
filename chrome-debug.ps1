# chrome-debug.ps1 — launch Chrome with the DevTools Protocol enabled so that
# the chrome-devtools MCP server (see .mcp.json) can drive it from Claude Code.
#
# Usage:
#   .\chrome-debug.ps1
#   .\chrome-debug.ps1 -Url https://example.com -Port 9222
#
# Chrome runs against an isolated profile (default: $env:TEMP\claude-chrome-debug)
# so it does not touch your normal browsing data. Leave the window open while
# you work with Claude Code; close it to stop.

param(
    [string]$Url = "about:blank",
    [int]$Port = 9222,
    [string]$ProfileDir = (Join-Path $env:TEMP "claude-chrome-debug"),
    [string]$ChromePath = ""
)

$ErrorActionPreference = "Stop"

if (-not $ChromePath) {
    $candidates = @(
        (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
        (Join-Path $env:LocalAppData "Google\Chrome\Application\chrome.exe")
    )
    $ChromePath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $ChromePath -or -not (Test-Path $ChromePath)) {
    Write-Error "Chrome not found. Install Google Chrome or pass -ChromePath."
    exit 1
}

if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir | Out-Null
}

Write-Host "Launching Chrome with remote debugging on port $Port"
Write-Host "Profile:      $ProfileDir"
Write-Host "DevTools URL: http://127.0.0.1:$Port"

& $ChromePath `
    "--remote-debugging-port=$Port" `
    "--user-data-dir=$ProfileDir" `
    "--no-first-run" `
    "--no-default-browser-check" `
    $Url
