"""Environment detection for Claude & Antigravity Workspace Setup Wizard.

Detects OS, shell, existing installations, and prerequisites.
Works cross-platform: Linux, macOS (Darwin), and Windows.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Install hints — platform-specific commands for common prerequisites
# ---------------------------------------------------------------------------

INSTALL_HINTS: dict[str, dict[str, str]] = {
    "jq": {
        "Linux": "sudo apt install jq",
        "Darwin": "brew install jq",
        "Windows": "choco install jq",
    },
    "ruff": {
        "Linux": "pip install ruff",
        "Darwin": "pip install ruff",
        "Windows": "pip install ruff",
    },
    "pytest": {
        "Linux": "pip install pytest",
        "Darwin": "pip install pytest",
        "Windows": "pip install pytest",
    },
    "openscad": {
        "Linux": "sudo apt install openscad",
        "Darwin": "brew install openscad",
        "Windows": "choco install openscad",
    },
    "platformio": {
        "Linux": "pip install platformio",
        "Darwin": "pip install platformio",
        "Windows": "pip install platformio",
    },
    "ssh": {
        "Linux": "sudo apt install openssh-client",
        "Darwin": "built-in",
        "Windows": "built-in",
    },
}

# ---------------------------------------------------------------------------
# Shell detection
# ---------------------------------------------------------------------------


def detect_shell() -> str:
    """Detect current shell environment.

    Returns one of: ``'wsl'``, ``'git-bash'``, ``'bash'``, ``'zsh'``,
    ``'powershell'``, ``'cmd'``, or ``'unknown'``.

    Detection logic (evaluated in order):
    1. ``/proc/version`` contains ``microsoft`` → WSL
    2. ``MSYSTEM`` env var is set → Git Bash
    3. ``PSModulePath`` env var is set *and* we are on Windows → PowerShell
    4. ``SHELL`` env var ends with ``zsh`` → zsh
    5. ``SHELL`` env var ends with ``bash`` → bash
    6. ``COMSPEC`` is set (Windows fallback) → cmd
    7. Otherwise → unknown
    """
    # 1. WSL — Linux userspace on Windows
    try:
        proc_version = Path("/proc/version")
        if proc_version.exists():
            content = proc_version.read_text(encoding="utf-8", errors="replace").lower()
            if "microsoft" in content:
                return "wsl"
    except OSError:
        pass

    # 2. Git Bash (MSYS2 / MinGW)
    if os.environ.get("MSYSTEM"):
        return "git-bash"

    # 3. PowerShell on Windows
    if platform.system() == "Windows" and os.environ.get("PSModulePath"):
        return "powershell"

    # 4–5. POSIX shells via $SHELL
    shell_env = os.environ.get("SHELL", "")
    if shell_env:
        shell_base = Path(shell_env).name
        if shell_base == "zsh":
            return "zsh"
        if shell_base == "bash":
            return "bash"

    # 6. Windows CMD fallback
    if os.environ.get("COMSPEC"):
        return "cmd"

    return "unknown"


# ---------------------------------------------------------------------------
# Individual component checks
# ---------------------------------------------------------------------------


def check_prereq(name: str) -> bool:
    """Return ``True`` if *name* is available on ``$PATH``."""
    return shutil.which(name) is not None


def check_bash_available() -> bool:
    """Return ``True`` if a usable ``bash`` binary exists.

    Always ``True`` on Linux/macOS; on Windows we probe ``$PATH``.
    """
    if platform.system() in ("Linux", "Darwin"):
        return True
    return shutil.which("bash") is not None


def check_claude_code() -> bool:
    """Return ``True`` if Claude Code CLI appears to be installed.

    Checks:
    * ``~/.claude/`` directory exists, **and**
    * ``claude --version`` runs successfully.
    """
    claude_dir = Path.home() / ".claude"
    if not claude_dir.is_dir():
        return False

    try:
        subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=10,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def check_antigravity() -> bool:
    """Return ``True`` if Antigravity (VS Code fork) appears to be installed.

    Checks (any one is sufficient):
    * ``~/.config/Antigravity/`` directory exists
    * VS Code extension state DB exists at
      ``~/.config/Antigravity/User/globalStorage/state.vscdb``
    * A bridge token file exists at
      ``~/.config/Antigravity/.bridge-token``
    """
    base = Path.home() / ".config" / "Antigravity"
    if not base.is_dir():
        return False

    # Any of these artefacts indicate an installation
    markers = [
        base / "User" / "globalStorage" / "state.vscdb",
        base / ".bridge-token",
    ]
    return any(m.exists() for m in markers)


# ---------------------------------------------------------------------------
# Component scanner
# ---------------------------------------------------------------------------


def scan_existing() -> dict[str, list[str]]:
    """Scan ``~/.claude/`` for already-installed components.

    Returns a dict with the following keys, each mapping to a list of
    component IDs (stem names) found on disk:

    * ``hooks``  — scripts in ``~/.claude/scripts/hooks/``
    * ``skills`` — directories in ``~/.claude/skills/``
    * ``agents`` — YAML/MD files in ``~/.claude/agents/``
    * ``rules``  — Markdown files in ``~/.claude/rules/``
    * ``mcp_servers`` — keys from ``~/.claude/settings.json`` → ``mcpServers``
    """
    claude_dir = Path.home() / ".claude"
    result: dict[str, list[str]] = {
        "hooks": [],
        "skills": [],
        "agents": [],
        "rules": [],
        "mcp_servers": [],
    }

    # --- hooks ---
    hooks_dir = claude_dir / "scripts" / "hooks"
    if hooks_dir.is_dir():
        result["hooks"] = sorted(p.stem for p in hooks_dir.iterdir() if p.is_file())

    # --- skills ---
    skills_dir = claude_dir / "skills"
    if skills_dir.is_dir():
        result["skills"] = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())

    # --- agents ---
    agents_dir = claude_dir / "agents"
    if agents_dir.is_dir():
        result["agents"] = sorted(
            p.stem
            for p in agents_dir.iterdir()
            if p.is_file() and p.suffix in (".yaml", ".yml", ".md")
        )

    # --- rules ---
    rules_dir = claude_dir / "rules"
    if rules_dir.is_dir():
        result["rules"] = sorted(
            p.stem for p in rules_dir.iterdir() if p.is_file() and p.suffix == ".md"
        )

    # --- mcp_servers ---
    settings_file = claude_dir / "settings.json"
    if settings_file.is_file():
        try:
            import json

            data = json.loads(
                settings_file.read_text(encoding="utf-8", errors="replace")
            )
            mcp = data.get("mcpServers", {})
            if isinstance(mcp, dict):
                result["mcp_servers"] = sorted(mcp.keys())
        except (json.JSONDecodeError, OSError):
            pass

    return result


# ---------------------------------------------------------------------------
# Install-hint helper
# ---------------------------------------------------------------------------


def get_install_hint(prereq: str, os_name: str) -> str:
    """Return a platform-specific install command for *prereq*.

    Parameters
    ----------
    prereq:
        Binary / package name (must be a key in :data:`INSTALL_HINTS`).
    os_name:
        One of ``'Linux'``, ``'Darwin'``, ``'Windows'``.

    Returns
    -------
    str
        The install command, or a generic fallback when no mapping exists.
    """
    hints = INSTALL_HINTS.get(prereq, {})
    return hints.get(os_name, f"Please install '{prereq}' for your platform")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def detect_environment() -> dict:
    """Gather full environment information.

    Returns a dict with the following keys:

    * ``os`` — ``platform.system()`` result (``Linux``, ``Darwin``, ``Windows``)
    * ``shell`` — result of :func:`detect_shell`
    * ``home`` — user home directory as a string
    * ``claude_dir`` — path to ``~/.claude/`` as a string
    * ``claude_installed`` — whether Claude Code CLI is present
    * ``antigravity_installed`` — whether Antigravity IDE is present
    * ``python_version`` — ``sys.version``
    * ``existing_components`` — result of :func:`scan_existing`
    * ``bash_available`` — whether bash can be invoked
    """
    home = Path.home()
    return {
        "os": platform.system(),
        "shell": detect_shell(),
        "home": str(home),
        "claude_dir": str(home / ".claude"),
        "claude_installed": check_claude_code(),
        "antigravity_installed": check_antigravity(),
        "python_version": sys.version,
        "existing_components": scan_existing(),
        "bash_available": check_bash_available(),
    }
