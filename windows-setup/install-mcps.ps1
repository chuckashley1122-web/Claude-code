# install-mcps.ps1 — register MCP servers with the Claude Code CLI.
#
# Adds Playwright, Chrome DevTools, and Gmail MCP servers at user scope so
# they're available in every Claude Code session on this machine.
#
# Requirements:
#   - Claude Code installed (claude.exe on PATH)
#   - Node.js + npx on PATH (winget install OpenJS.NodeJS.LTS)
#   - For the gmail server: an OAuth client JSON saved per the README in
#     https://github.com/GongRzhe/Gmail-MCP-Server (see chat instructions).
#
# Usage:
#   .\install-mcps.ps1

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Require-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Error "$Name not found on PATH. $Hint"
        exit 1
    }
}

Require-Command 'claude' 'Install Claude Code first: irm https://claude.ai/install.ps1 | iex'
Require-Command 'npx'    'Install Node.js LTS: winget install OpenJS.NodeJS.LTS, then open a new PowerShell.'

# --scope user puts these in %USERPROFILE%\.claude.json so every project sees them.
$servers = @(
    @{ Name = 'playwright'      ; Pkg = '@playwright/mcp@latest' },
    @{ Name = 'chrome-devtools' ; Pkg = 'chrome-devtools-mcp@latest' },
    @{ Name = 'gmail'           ; Pkg = '@gongrzhe/server-gmail-autoauth-mcp' }
)

foreach ($s in $servers) {
    Write-Host "Adding MCP server: $($s.Name)" -ForegroundColor Cyan
    & claude mcp add $s.Name --scope user -- npx -y $s.Pkg
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to add $($s.Name) (exit $LASTEXITCODE). Continuing."
    }
}

Write-Host ""
Write-Host "Registered servers:" -ForegroundColor Green
& claude mcp list

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open a NEW PowerShell window (PATH refresh)."
Write-Host "  2. cd into a project folder and run: claude"
Write-Host "  3. For gmail: complete the OAuth setup per chat instructions"
Write-Host "     before the gmail server will work."
