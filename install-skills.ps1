# install-skills.ps1 — install the Claude Code skills/plugins this setup uses.
#
# Run this on YOUR machine (not a throwaway cloud session). It registers each
# plugin's marketplace and installs the plugin at user scope via the
# non-interactive `claude plugin` CLI. Re-running is safe; already-installed
# plugins are skipped by Claude Code.
#
# Usage:
#   .\install-skills.ps1            Install all verified skills
#   .\install-skills.ps1 -Extras   Also copy the standalone file-based skills
#
# Requires: Claude Code CLI (`claude`) v2.1+ and git on PATH.

[CmdletBinding()]
param(
    [switch]$Extras
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Error "'claude' CLI not found on PATH. Install Claude Code first."
    exit 1
}

# repo | plugin@marketplace | description
# All four below were installed and verified working (versions noted at time of writing).
$Plugins = @(
    @{ Repo = 'obra/superpowers-marketplace';        Spec = 'superpowers@superpowers-marketplace';        Desc = 'Superpowers: plan-first/test-first skills framework (v5.1.0)' },
    @{ Repo = 'nextlevelbuilder/ui-ux-pro-max-skill'; Spec = 'ui-ux-pro-max@ui-ux-pro-max-skill';          Desc = 'UI/UX Pro Max: design system + accessibility audit (v2.5.0)' },
    @{ Repo = 'lackeyjb/playwright-skill';             Spec = 'playwright-skill@playwright-skill';           Desc = 'Playwright: browser automation skill (v4.1.0)' },
    @{ Repo = 'AgriciDaniel/claude-ads';              Spec = 'claude-ads@ai-marketing-hub-claude-ads';      Desc = 'claude-ads: paid-ads audit/optimize - provides /ads meta, /ads competitor, /ads creative, /ads audit (v1.7.0)' }
)

Write-Host "Installing Claude Code skills (user scope)..." -ForegroundColor Cyan
Write-Host ""

foreach ($p in $Plugins) {
    Write-Host ">> $($p.Desc)" -ForegroundColor Green
    Write-Host "   marketplace: $($p.Repo)"
    try { claude plugin marketplace add $p.Repo } catch { Write-Host "   (marketplace add reported an issue; continuing)" -ForegroundColor Yellow }
    try { claude plugin install $p.Spec --scope user } catch { Write-Host "   (install reported an issue; continuing)" -ForegroundColor Yellow }
    Write-Host ""
}

# --- Optional standalone, file-based skills (not packaged as plugins) ---
if ($Extras) {
    Write-Host ">> Standalone skill: competitive-ads-extractor (ComposioHQ/awesome-claude-skills)" -ForegroundColor Green
    $SkillsDir = Join-Path $env:USERPROFILE '.claude\skills'
    New-Item -ItemType Directory -Path $SkillsDir -Force | Out-Null
    $Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString())
    git clone --depth 1 https://github.com/ComposioHQ/awesome-claude-skills $Tmp
    $src = Join-Path $Tmp 'competitive-ads-extractor'
    if (Test-Path $src) {
        Copy-Item -Recurse -Force $src (Join-Path $SkillsDir 'competitive-ads-extractor')
        Write-Host "   Installed to $SkillsDir\competitive-ads-extractor (model-invoked; no slash command)"
    } else {
        Write-Warning "Could not find competitive-ads-extractor folder in the repo."
    }
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
    Write-Host ""
}

# --- PENDING: sources not yet confirmed ---------------------------------------
# These were requested but their exact upstream source is ambiguous. Fill in the
# repo and plugin@marketplace once you confirm which project you mean, then add
# them to the $Plugins array above:
#   - "Stop Slop"   -> likely the "Design Anti-Slop" skill (confirm repo)
#   - "The Council" -> ~10 projects share this name (ngmeyer/council-review,
#                      hex/claude-council, sjsyrek/design-council, ...)
#   - "I Spy"       -> no clear public match found
#   - "bulk creative" / "ads score" -> not standalone skills; covered by
#                      claude-ads commands (/ads creative, /ads generate, /ads audit)

Write-Host "Done. Run 'claude plugin list' to verify, then restart Claude Code." -ForegroundColor Green
