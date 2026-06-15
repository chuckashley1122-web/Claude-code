#!/usr/bin/env bash
# install-skills.sh — install the Claude Code skills/plugins this setup uses.
#
# Run this on YOUR machine (not a throwaway cloud session). It registers each
# plugin's marketplace and installs the plugin at user scope via the
# non-interactive `claude plugin` CLI. Re-running is safe; already-installed
# plugins are skipped by Claude Code.
#
# Usage:
#   ./install-skills.sh            Install all verified skills
#   ./install-skills.sh --extras   Also copy the standalone file-based skills
#
# Requires: Claude Code CLI (`claude`) v2.1+ and git on PATH.

set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
    echo "Error: 'claude' CLI not found on PATH. Install Claude Code first." >&2
    exit 1
fi

# marketplace_repo  plugin@marketplace  description
# All four below were installed and verified working (versions noted at time of writing).
PLUGINS=(
    "obra/superpowers-marketplace|superpowers@superpowers-marketplace|Superpowers: plan-first/test-first skills framework (v5.1.0)"
    "nextlevelbuilder/ui-ux-pro-max-skill|ui-ux-pro-max@ui-ux-pro-max-skill|UI/UX Pro Max: design system + accessibility audit (v2.5.0)"
    "lackeyjb/playwright-skill|playwright-skill@playwright-skill|Playwright: browser automation skill (v4.1.0)"
    "AgriciDaniel/claude-ads|claude-ads@ai-marketing-hub-claude-ads|claude-ads: paid-ads audit/optimize — provides /ads meta, /ads competitor, /ads creative, /ads audit (v1.7.0)"
)

echo "Installing Claude Code skills (user scope)..."
echo

for entry in "${PLUGINS[@]}"; do
    IFS='|' read -r repo spec desc <<<"$entry"
    echo ">> $desc"
    echo "   marketplace: $repo"
    claude plugin marketplace add "$repo" || echo "   (marketplace add reported an issue; continuing)"
    claude plugin install "$spec" --scope user || echo "   (install reported an issue; continuing)"
    echo
done

# --- Optional standalone, file-based skills (not packaged as plugins) ---
if [[ "${1:-}" == "--extras" ]]; then
    echo ">> Standalone skill: competitive-ads-extractor (ComposioHQ/awesome-claude-skills)"
    skills_dir="$HOME/.claude/skills"
    mkdir -p "$skills_dir"
    tmp="$(mktemp -d)"
    git clone --depth 1 https://github.com/ComposioHQ/awesome-claude-skills "$tmp/awesome-claude-skills"
    if [[ -d "$tmp/awesome-claude-skills/competitive-ads-extractor" ]]; then
        cp -r "$tmp/awesome-claude-skills/competitive-ads-extractor" "$skills_dir/"
        echo "   Installed to $skills_dir/competitive-ads-extractor (model-invoked; no slash command)"
    else
        echo "   Could not find competitive-ads-extractor folder in the repo." >&2
    fi
    rm -rf "$tmp"
    echo
fi

# --- PENDING: sources not yet confirmed ---------------------------------------
# These were requested but their exact upstream source is ambiguous. Fill in the
# repo and plugin@marketplace once you confirm which project you mean, then add
# them to the PLUGINS array above:
#   - "Stop Slop"  -> likely the "Design Anti-Slop" skill (confirm repo)
#   - "The Council" -> ~10 projects share this name (e.g. ngmeyer/council-review,
#                      hex/claude-council, sjsyrek/design-council)
#   - "I Spy"      -> no clear public match found
#   - "bulk creative" / "ads score" -> not standalone skills; covered by
#                      claude-ads commands (/ads creative, /ads generate, /ads audit)

echo "Done. Run 'claude plugin list' to verify, then restart Claude Code."
