#!/usr/bin/env bash
# install-skills.sh — install the Claude Code skills/plugins this setup uses.
#
# Run this on YOUR machine (not a throwaway cloud session). It registers each
# plugin's marketplace and installs the plugin at user scope via the
# non-interactive `claude plugin` CLI, and clones the file-based skills into
# ~/.claude/skills. Re-running is safe (idempotent).
#
# Usage:
#   ./install-skills.sh            Install verified plugins + file-based skills
#   ./install-skills.sh --extras   Also install optional/standalone extras
#
# Requires: Claude Code CLI (`claude`) v2.1+ and git on PATH.
# Every plugin/skill below was added and installed successfully during setup.

set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
    echo "Error: 'claude' CLI not found on PATH. Install Claude Code first." >&2
    exit 1
fi
if ! command -v git >/dev/null 2>&1; then
    echo "Error: 'git' not found on PATH." >&2
    exit 1
fi

SKILLS_DIR="$HOME/.claude/skills"
mkdir -p "$SKILLS_DIR"

# ---------------------------------------------------------------------------
# 1) Marketplace plugins:  marketplace_repo | plugin@marketplace | description
#    (frontend-design ships in the built-in claude-plugins-official directory,
#     so it needs no marketplace add — leave the repo field as "-")
# ---------------------------------------------------------------------------
PLUGINS=(
    "obra/superpowers-marketplace|superpowers@superpowers-marketplace|Superpowers: plan-first/test-first dev methodology"
    "nextlevelbuilder/ui-ux-pro-max-skill|ui-ux-pro-max@ui-ux-pro-max-skill|UI/UX Pro Max: design system + accessibility audit"
    "lackeyjb/playwright-skill|playwright-skill@playwright-skill|Playwright: browser automation"
    "AgriciDaniel/claude-ads|claude-ads@ai-marketing-hub-claude-ads|claude-ads: paid-ads audit (/ads meta, /ads competitor, /ads creative, /ads audit)"
    "AgriciDaniel/claude-seo|claude-seo@agricidaniel-claude-seo|claude-seo: SEO/GEO/AEO skill (25 sub-skills, 18 agents)"
    "coreyhaines31/marketingskills|marketing-skills@marketingskills|marketingskills: 40 marketing tools (CRO, copy, SEO, growth)"
    "charlie947/social-media-skills|social-media-skills@social-media-skills|social-media-skills: hooks, posts, carousels"
    "JuliusBrussee/caveman|caveman@caveman|caveman: token-cutting prompt compressor"
    "yamadashy/repomix|repomix-mcp@repomix|repomix: pack a repo into one LLM-friendly file (MCP)"
    "yamadashy/repomix|repomix-commands@repomix|repomix: slash commands for repomix"
    "-|frontend-design@claude-plugins-official|frontend-design: Anthropic official anti-generic-UI design skill"
)

echo "== Installing marketplace plugins (user scope) =="
for entry in "${PLUGINS[@]}"; do
    IFS='|' read -r repo spec desc <<<"$entry"
    echo ">> $desc"
    if [[ "$repo" != "-" ]]; then
        claude plugin marketplace add "$repo" || echo "   (marketplace add issue; continuing)"
    fi
    claude plugin install "$spec" --scope user || echo "   (install issue; continuing)"
done
echo

# ---------------------------------------------------------------------------
# 2) File-based skills cloned into ~/.claude/skills (single SKILL.md repos)
# ---------------------------------------------------------------------------
clone_skill() {  # name  git_url
    local name="$1" url="$2" dest="$SKILLS_DIR/$1"
    echo ">> skill: $name"
    if [[ -d "$dest/.git" ]]; then
        git -C "$dest" pull --ff-only || echo "   (pull issue; continuing)"
    else
        git clone --depth 1 "$url" "$dest" || echo "   (clone issue; continuing)"
    fi
}

echo "== Installing file-based skills into $SKILLS_DIR =="
clone_skill "humanizer"       "https://github.com/blader/humanizer"
clone_skill "ai-second-brain" "https://github.com/charlie947/ai-second-brain"
echo

# ---------------------------------------------------------------------------
# 3) gstack — ships its own setup script that wires into ~/.claude
#    NOTE: gstack's ./setup runs the author's install logic; review the repo
#    before trusting it on your machine.
# ---------------------------------------------------------------------------
echo "== Installing gstack (garrytan/gstack via its own setup) =="
GSTACK_DIR="$SKILLS_DIR/gstack"
if [[ -d "$GSTACK_DIR/.git" ]]; then
    git -C "$GSTACK_DIR" pull --ff-only || true
else
    git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git "$GSTACK_DIR" || echo "   (clone issue; continuing)"
fi
if [[ -x "$GSTACK_DIR/setup" ]]; then
    ( cd "$GSTACK_DIR" && ./setup ) || echo "   (gstack ./setup reported an issue — run it manually to review)"
fi
echo

# ---------------------------------------------------------------------------
# 4) Optional extras
# ---------------------------------------------------------------------------
if [[ "${1:-}" == "--extras" ]]; then
    echo "== Extras =="
    clone_skill "competitive-ads-extractor" "https://github.com/ComposioHQ/awesome-claude-skills"
    # ^ this clones the whole collection; keep only the one folder if you prefer:
    #   mv competitive-ads-extractor/competitive-ads-extractor/* ... (see repo layout)
    echo
fi

# ---------------------------------------------------------------------------
# PENDING — sources not yet confirmed (NOT installed). Confirm a repo, then add
# above. See README/notes:
#   - "I Spy"            -> no public Claude Code skill by this name found
#                           (closest: ellyseum/claude-vision). Provide a URL.
#   - "Stop Slop"        -> multiple repos: mohamedgame/stop-slop,
#                           hardikpandya/stop-slop, wpgaurav/claude-code-skills
#   - "claude-skills"    -> which 263+/337-skill bundle? e.g.
#                           alirezarezvani/claude-skills, daymade/claude-code-skills
#   - "claude-for-legal" / "financial-services" -> official Anthropic ENTERPRISE
#                           marketplaces (reserved names); install via the
#                           official directory / may require org access.
# ---------------------------------------------------------------------------

echo "Done. Run 'claude plugin list' to verify, then restart Claude Code."
