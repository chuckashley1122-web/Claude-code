# setup-chrome-debug.ps1 — wire Claude Code to a debuggable Chrome instance.
#
# Steps:
#   1. Ensure the Claude Code CLI is installed (`npm i -g @anthropic-ai/claude-code`).
#   2. Launch Chrome with --remote-debugging-port using a dedicated profile.
#   3. Register the chrome-devtools-mcp server with Claude Code so it can drive Chrome.
#
# Usage:
#   .\setup-chrome-debug.ps1                        Run the full setup on port 9222
#   .\setup-chrome-debug.ps1 -Port 9333             Use a different debugging port
#   .\setup-chrome-debug.ps1 -NoLaunch              Skip the Chrome launch step
#   .\setup-chrome-debug.ps1 -ProfileDir "C:\..."   Override the debug profile directory
#   .\setup-chrome-debug.ps1 -Scope project         Register MCP at project scope (default: user)

[CmdletBinding()]
param(
    [int]$Port = 9222,
    [switch]$NoLaunch,
    [string]$ProfileDir = (Join-Path $env:USERPROFILE '.chrome-debug-profile'),
    [ValidateSet('user', 'project', 'local')]
    [string]$Scope = 'user'
)

$ErrorActionPreference = 'Stop'

function Test-DebugEndpoint {
    param([int]$Port)
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/version" -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

# 1. Claude Code CLI
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Error "npm not found. Install Node.js from https://nodejs.org and retry."
        exit 1
    }
    Write-Host "Installing @anthropic-ai/claude-code globally..." -ForegroundColor Cyan
    npm install -g '@anthropic-ai/claude-code'
}
$claudeVersion = & claude --version 2>$null
Write-Host "Claude Code: $claudeVersion" -ForegroundColor Green

# 2. Locate Chrome
$candidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles\Chromium\Application\chrome.exe"
)
$chrome = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $chrome) {
    Write-Error "Could not find Chrome. Install Chrome and retry."
    exit 1
}
Write-Host "Chrome: $chrome" -ForegroundColor Green

# 3. Launch Chrome with remote debugging
if (-not $NoLaunch) {
    if (Test-DebugEndpoint -Port $Port) {
        Write-Host "Chrome already listening on port $Port — skipping launch." -ForegroundColor Yellow
    } else {
        if (-not (Test-Path $ProfileDir)) {
            New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
        }
        Write-Host "Launching Chrome (--remote-debugging-port=$Port, profile=$ProfileDir)..." -ForegroundColor Cyan
        Start-Process -FilePath $chrome -ArgumentList @(
            "--remote-debugging-port=$Port",
            "--user-data-dir=$ProfileDir"
        ) | Out-Null

        $ready = $false
        for ($i = 0; $i -lt 10; $i++) {
            Start-Sleep -Seconds 1
            if (Test-DebugEndpoint -Port $Port) { $ready = $true; break }
        }
        if (-not $ready) {
            Write-Error "Chrome did not open a debugging endpoint on port $Port."
            exit 1
        }
    }
}

# 4. Register chrome-devtools-mcp with Claude Code
Write-Host "Registering chrome-devtools MCP server (scope=$Scope)..." -ForegroundColor Cyan
& claude mcp remove chrome-devtools --scope $Scope 2>$null | Out-Null
& claude mcp add chrome-devtools `
    --scope $Scope `
    -- npx -y 'chrome-devtools-mcp@latest' --browser-url "http://127.0.0.1:$Port"

Write-Host ""
Write-Host "Done. Start a Claude Code session and try:" -ForegroundColor Green
Write-Host "  > open https://example.com and tell me the <h1> text"
