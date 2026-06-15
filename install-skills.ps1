# install-skills.ps1 — install the Claude Code skills/plugins this setup uses.
#
# Run this on YOUR machine (not a throwaway cloud session). It registers each
# plugin's marketplace and installs the plugin at user scope via the
# non-interactive `claude plugin` CLI, and clones the file-based skills into
# ~/.claude/skills. Re-running is safe (idempotent).
#
# Usage:
#   .\install-skills.ps1            Install verified plugins + file-based skills
#   .\install-skills.ps1 -Extras    Also install optional/standalone extras
#
# Requires: Claude Code CLI (`claude`) v2.1+ and git on PATH.
# Every plugin/skill below was added and installed successfully during setup.

[CmdletBinding()]
param([switch]$Extras)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Error "'claude' CLI not found on PATH. Install Claude Code first."; exit 1
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "'git' not found on PATH."; exit 1
}

$SkillsDir = Join-Path $env:USERPROFILE '.claude\skills'
New-Item -ItemType Directory -Path $SkillsDir -Force | Out-Null

# 1) Marketplace plugins. Repo '-' means it's in the built-in official directory.
$Plugins = @(
    @{ Repo='obra/superpowers-marketplace';        Spec='superpowers@superpowers-marketplace';        Desc='Superpowers: plan-first/test-first dev methodology' },
    @{ Repo='nextlevelbuilder/ui-ux-pro-max-skill'; Spec='ui-ux-pro-max@ui-ux-pro-max-skill';          Desc='UI/UX Pro Max: design system + accessibility audit' },
    @{ Repo='lackeyjb/playwright-skill';             Spec='playwright-skill@playwright-skill';           Desc='Playwright: browser automation' },
    @{ Repo='AgriciDaniel/claude-ads';              Spec='claude-ads@ai-marketing-hub-claude-ads';      Desc='claude-ads: paid-ads audit (/ads meta, /ads competitor, /ads creative, /ads audit)' },
    @{ Repo='AgriciDaniel/claude-seo';              Spec='claude-seo@agricidaniel-claude-seo';          Desc='claude-seo: SEO/GEO/AEO skill' },
    @{ Repo='coreyhaines31/marketingskills';        Spec='marketing-skills@marketingskills';            Desc='marketingskills: 40 marketing tools' },
    @{ Repo='charlie947/social-media-skills';        Spec='social-media-skills@social-media-skills';     Desc='social-media-skills: hooks, posts, carousels' },
    @{ Repo='JuliusBrussee/caveman';                Spec='caveman@caveman';                             Desc='caveman: token-cutting prompt compressor' },
    @{ Repo='yamadashy/repomix';                    Spec='repomix-mcp@repomix';                         Desc='repomix: pack a repo into one LLM-friendly file (MCP)' },
    @{ Repo='yamadashy/repomix';                    Spec='repomix-commands@repomix';                    Desc='repomix: slash commands' },
    @{ Repo='-';                                    Spec='frontend-design@claude-plugins-official';     Desc='frontend-design: Anthropic official anti-generic-UI skill' },
    @{ Repo='ellyseum/claude-vision';               Spec='claude-vision@ellyseum-claude-vision';        Desc='claude-vision: visual context (clipboard/screenshot/video) - in place of "I Spy"' }
)

Write-Host "== Installing marketplace plugins (user scope) ==" -ForegroundColor Cyan
foreach ($p in $Plugins) {
    Write-Host ">> $($p.Desc)" -ForegroundColor Green
    if ($p.Repo -ne '-') {
        try { claude plugin marketplace add $p.Repo } catch { Write-Host "   (marketplace add issue; continuing)" -ForegroundColor Yellow }
    }
    try { claude plugin install $p.Spec --scope user } catch { Write-Host "   (install issue; continuing)" -ForegroundColor Yellow }
}
Write-Host ""

# 2) File-based skills cloned into ~/.claude/skills
function Clone-Skill($name, $url) {
    $dest = Join-Path $SkillsDir $name
    Write-Host ">> skill: $name" -ForegroundColor Green
    if (Test-Path (Join-Path $dest '.git')) {
        try { git -C $dest pull --ff-only } catch { Write-Host "   (pull issue; continuing)" -ForegroundColor Yellow }
    } else {
        try { git clone --depth 1 $url $dest } catch { Write-Host "   (clone issue; continuing)" -ForegroundColor Yellow }
    }
}

Write-Host "== Installing file-based skills into $SkillsDir ==" -ForegroundColor Cyan
Clone-Skill 'humanizer'       'https://github.com/blader/humanizer'
Clone-Skill 'ai-second-brain' 'https://github.com/charlie947/ai-second-brain'
Clone-Skill 'stop-slop'       'https://github.com/hardikpandya/stop-slop'
Write-Host ""

# 3) gstack — ships its own setup. Review the repo before trusting ./setup.
Write-Host "== Installing gstack (garrytan/gstack via its own setup) ==" -ForegroundColor Cyan
$GstackDir = Join-Path $SkillsDir 'gstack'
if (Test-Path (Join-Path $GstackDir '.git')) {
    try { git -C $GstackDir pull --ff-only } catch {}
} else {
    try { git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git $GstackDir } catch { Write-Host "   (clone issue; continuing)" -ForegroundColor Yellow }
}
if (Test-Path (Join-Path $GstackDir 'setup')) {
    Write-Host "   gstack provides a ./setup script (bash). Run it under WSL/Git Bash to finish:" -ForegroundColor Yellow
    Write-Host "     cd `"$GstackDir`"; ./setup"
}
Write-Host ""

# 4) Large catalog: alirezarezvani/claude-skills (~80 plugins, marketplace
#    'claude-code-skills'). Register only; cherry-pick to avoid context bloat:
#      claude plugin install finance-skills@claude-code-skills
Write-Host "== Registering claude-skills catalog (alirezarezvani/claude-skills) ==" -ForegroundColor Cyan
try { claude plugin marketplace add alirezarezvani/claude-skills } catch { Write-Host "   (marketplace add issue; continuing)" -ForegroundColor Yellow }
Write-Host "   Registered as 'claude-code-skills'. Install individual plugins as needed."
Write-Host ""

# 5) Optional extras
if ($Extras) {
    Write-Host "== Extras ==" -ForegroundColor Cyan
    Clone-Skill 'competitive-ads-extractor' 'https://github.com/ComposioHQ/awesome-claude-skills'
    Write-Host ""
}

# Resolved per user decisions:
#   - "I Spy"      -> using ellyseum/claude-vision instead (no skill named "I Spy").
#   - "Stop Slop"  -> hardikpandya/stop-slop (cloned above).
#   - "claude-skills" -> alirezarezvani/claude-skills registered as a catalog; cherry-pick plugins.
#   - "claude-for-legal" / "financial-services" -> SKIPPED (official enterprise marketplaces).

Write-Host "Done. Run 'claude plugin list' to verify, then restart Claude Code." -ForegroundColor Green
