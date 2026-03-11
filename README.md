# Claude & Antigravity Workspace Setup Wizard

Bring your Claude Code + Antigravity setup from vanilla to fully loaded. One command, interactive wizard, you pick what you want.

## What You Get

| Category | Count | Includes |
|----------|-------|----------|
| **Hooks** | 6 | Dangerous command blocker, test gate, quality gate, sensitive file blocker, auto-lint Python, pre-compact save |
| **Skills** | 13 | Code quality, security, documentation, deployment, self-healing CI, project wizard, architecture, browser automation, performance optimizer, accessibility auditor, RPi controller, CAD/3D printing, autonomous flash |
| **Plugins** | 10 | Superpowers, code review, PR review toolkit, feature dev, frontend design, plugin dev, CLAUDE.md management, security guidance, Supabase, Rust analyzer |
| **Agents** | 7 | Analyst, architect, code reviewer, learning guide, security auditor, Socratic mentor, test generator |
| **Rules** | 3 | Workflow, Python, hooks |
| **MCP Servers** | 3 | Antigravity bridge, Pi status, OpenSCAD |

## Prerequisites

- **Python 3.8+**
- **Claude Code** installed and working
- **Antigravity** installed (optional — bridge MCP auto-disables if not detected)

## Quick Start

### Windows (Martin & Norman — double-click and go)

1. Clone or download this repo
2. Double-click **`start.bat`**
3. Pick your shell (Git Bash recommended) — the wizard launches automatically

### Any Platform

```bash
git clone https://github.com/Upua/claude-workspace-setup.git
cd claude-workspace-setup
python install.py
```

The wizard will:
1. Detect your OS, shell, and existing installations
2. Walk you through each component category with checkboxes
3. Check prerequisites and offer to install missing ones
4. Show a review summary before installing anything
5. Install selected components with a progress bar
6. Verify everything was installed correctly

## CLI Options

```
python install.py                  # Interactive wizard (default)
python install.py --dry-run        # Preview what would be installed
python install.py --rollback       # Restore settings.json + CLAUDE.md from backup
python install.py --verbose        # Show every file operation
python install.py --all            # Install everything, skip wizard
python install.py --minimal        # Install essentials only (no hardware/MCPs)
```

## Windows Users

**Just double-click `start.bat`** — it detects what you have (Git Bash, WSL, PowerShell), lets you pick, and launches the wizard. No terminal knowledge needed.

Hook scripts require a bash-compatible shell. If neither Git Bash nor WSL is found, hooks are skipped automatically (everything else installs normally). For the full experience, install [Git for Windows](https://gitforwindows.org).

### Prerequisites on Windows

```bash
# If using Chocolatey:
choco install jq

# If using winget:
winget install jqlang.jq

# Python packages:
pip install ruff pytest
```

## How It Works

- **Non-destructive**: Existing settings.json is backed up before any changes
- **Merge, don't replace**: Hooks and MCP servers are appended to your existing config
- **Your choices are respected**: Existing plugin enable/disable states are never overwritten
- **Rollback**: `--rollback` restores settings.json and CLAUDE.md from the latest backup

### What Gets Installed Where

| Component Type | Target Location |
|---------------|-----------------|
| Hooks | `~/.claude/scripts/hooks/` + registered in `settings.json` |
| Skills | `~/.claude/skills/<name>/` |
| Plugins | Via `claude plugin install` |
| Agents | `~/.claude/agents/` |
| Rules | `~/.claude/rules/` |
| MCP Servers | `~/.claude/mcp-servers/` + registered via `claude mcp add` |

## Troubleshooting

**"rich not found"** — The wizard needs the `rich` library. It will offer to install it automatically, or run `pip install rich` first.

**Hooks not firing on Windows** — Make sure you're running Claude Code through WSL or Git Bash, not native PowerShell.

**"jq not found"** — All hooks require `jq` for JSON parsing. Install it via your package manager (see Windows section above).

**Plugin install fails** — Ensure you have internet access and `claude` CLI is in your PATH.

**Rollback only restores config files** — `--rollback` restores `settings.json` and `CLAUDE.md`. Copied files (skills, agents, etc.) remain in place. Check `~/.claude/.wizard-install-log` for the full list of installed files.
