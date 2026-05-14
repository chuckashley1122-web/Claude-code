# Chrome control for Claude Code (desktop)

Lets Claude Code drive any tab in your local Chrome — fill forms, click
buttons, read pages, navigate Gmail/Outlook/etc.

## One-time setup

1. **Install Node.js 20+** if you don't have it: <https://nodejs.org/>
   - Verify in PowerShell: `node -v`

2. **Open this project in Claude Code desktop.** It will prompt you to
   approve the `chrome-devtools` MCP server (defined in `.mcp.json`).
   Click **Approve**.

## Daily use

1. Launch Chrome with debugging enabled by **double-clicking
   `start-chrome-debug.bat`**. To make it a desktop icon: right-click
   the file → **Send to** → **Desktop (create shortcut)**, then rename
   the shortcut to something like "Chrome (Claude)".

   This opens a dedicated debug Chrome window. Sign in to whatever
   accounts you want Claude to use (Gmail, GitHub, etc.) — the profile
   persists between runs at `%LocalAppData%\ChromeDebugProfile`.

   (Power users: `start-chrome-debug.ps1` is the same thing in
   PowerShell, with flags like `-UseDefaultProfile` and `-Port`.)

2. In Claude Code, ask it to do browser things, e.g.:
   - "Open Gmail and summarize my unread inbox"
   - "Go to github.com/anthropics/claude-code and star the repo"
   - "Fill out the form on the current tab with my saved info"

3. Verify the MCP server is loaded any time with `/mcp` inside Claude Code.

## Options

- **Use your real Chrome profile** (signed-in, with extensions). Close
  every Chrome window first, then run:
  ```powershell
  .\start-chrome-debug.ps1 -UseDefaultProfile
  ```
  Trade-off: while debug mode is on, anything Claude does runs in your
  real session. Prefer the dedicated profile unless you specifically
  need your real one.

- **Change debug port** (default 9222):
  ```powershell
  .\start-chrome-debug.ps1 -Port 9333
  ```
  If you change it, also update `--browserUrl` in `.mcp.json`.

## Troubleshooting

- `/mcp` shows `chrome-devtools` as failed → Chrome isn't running with
  the debug port. Run the launcher script.
- "address already in use" → another Chrome instance grabbed port 9222.
  Close it or pick a different port.
- Tools time out → confirm `http://127.0.0.1:9222/json/version` returns
  JSON in your browser. If not, the debug port isn't actually open.
