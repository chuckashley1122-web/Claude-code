# Claude Code on Your Desktop — Step-by-Step

A simple setup guide. Read it like a recipe: do one step, then the next.

## What you're building

Claude Code is a coding assistant that runs in your terminal. By the end of this
guide, you'll be able to open a terminal, type `claude`, and start chatting with
it about your code.

## Before you start

You need:

- A Windows, Mac, or Linux computer.
- An internet connection.
- A Claude account (free to make at https://claude.ai).
- About 10 minutes.

---

## Windows

### Step 1 — Open PowerShell

1. Press the **Windows key** on your keyboard.
2. Type `PowerShell`.
3. Click **Windows PowerShell** when it shows up.

A black or blue window opens with a blinking cursor. That's the terminal.

### Step 2 — Run the installer

Copy this line, paste it into PowerShell, and press **Enter**:

```powershell
irm https://claude.ai/install.ps1 | iex
```

You should see:

```
Setting up Claude Code...
Claude Code successfully installed!
```

That's the same screen you already saw — you're done with the install.

### Step 3 — Close and reopen PowerShell

This makes Windows notice the new `claude` command. Close the window, then open
PowerShell again the same way as Step 1.

### Step 4 — Check it works

In the new PowerShell window, type:

```powershell
claude --version
```

You should see a version number like `2.1.140`. If you do, it works.

### Step 5 — Log in

Type:

```powershell
claude
```

A message appears with a link. Click the link (or copy it into your browser),
log into your Claude account, and copy the code it gives you back into
PowerShell.

After that, you're chatting with Claude Code. Type a question and press Enter.
To leave, type `/exit` or press **Ctrl + C** twice.

### Optional — Git Bash setup

If you use Git Bash on Windows, tell Claude Code where it lives by adding this
to your settings (in `~/.claude/settings.json`):

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

That's what the top of your screenshot showed — it's already done for you.

---

## Mac

### Step 1 — Open Terminal

1. Press **Cmd + Space** to open Spotlight.
2. Type `Terminal`.
3. Press **Enter**.

### Step 2 — Run the installer

Paste this and press Enter:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### Step 3 — Close and reopen Terminal

Same idea as Windows — the new `claude` command needs a fresh window to show up.

### Step 4 — Check and log in

```bash
claude --version
claude
```

Click the login link, paste the code back, done.

---

## Linux

Same steps as Mac:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Then close the terminal, open a new one, and run `claude`.

---

## Day-to-day use

1. Open a terminal.
2. Move into your project folder. Example:
   ```bash
   cd C:\Users\chuck\my-project   # Windows
   cd ~/my-project                # Mac/Linux
   ```
3. Type `claude` and press Enter.
4. Ask it to do things in plain English: *"Add a button that says Hello"*,
   *"Fix the bug in app.js"*, *"Explain what this file does"*.

To quit: type `/exit` or press **Ctrl + C** twice.

To update later: run `claude update`.

---

## If something breaks

- **`claude` not found** — Close every terminal window and open a fresh one.
  The command only appears after a restart.
- **Login link won't open** — Copy the whole URL into your browser by hand.
- **Stuck mid-chat** — Press **Ctrl + C** twice to get back to your prompt.
- **Want a clean slate** — Run `claude` and type `/clear` to wipe the
  conversation without quitting.

You're set. Open a terminal, type `claude`, and start building.
