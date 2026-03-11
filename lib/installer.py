"""Core install logic for the Claude & Antigravity Workspace Setup Wizard.

Handles file copying, settings merge, plugin installation, MCP registration,
backup/rollback, and post-install verification.
"""

from __future__ import annotations

import filecmp
import json
import shutil
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .registry import Component, HookRegistration

COMPONENTS_DIR = Path(__file__).parent.parent / "components"

# Target directories relative to ~/.claude/
_TARGET_DIRS: dict[str, str] = {
    "hook": "scripts/hooks",
    "skill": "skills",
    "agent": "agents",
    "rule": "rules",
    "mcp_server": "mcp-servers",
}


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def run_install(
    selected: list[Component],
    env: dict,
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> int:
    """Main install orchestrator. Returns 0 on success, 1 on failure.

    Steps:
    1. Backup settings.json + CLAUDE.md
    2. Copy hooks to ~/.claude/scripts/hooks/
    3. Copy skills to ~/.claude/skills/ (full recursive)
    4. Install plugins via ``claude plugin install <id>@claude-plugins-official``
    5. Copy agents to ~/.claude/agents/
    6. Copy rules to ~/.claude/rules/
    7. Register MCP servers via ``claude mcp add``
    8. Merge hook registrations into settings.json
    9. Render + write/merge CLAUDE.md
    10. Write install log to ~/.claude/.wizard-install-log
    11. Run verification
    """
    claude_dir = Path(env["claude_dir"])
    home = Path(env["home"])
    settings_path = claude_dir / "settings.json"
    claude_md_path = home / ".claude" / "CLAUDE.md"

    errors: list[str] = []
    installed: list[Component] = []

    # Step 1: Backup
    if not dry_run:
        if settings_path.exists():
            bp = backup_file(settings_path)
            if verbose and bp:
                _log(f"Backed up settings.json -> {bp}")
        if claude_md_path.exists():
            bp = backup_file(claude_md_path)
            if verbose and bp:
                _log(f"Backed up CLAUDE.md -> {bp}")

    # Categorise selected components
    hooks = [c for c in selected if c.component_type == "hook"]
    skills = [c for c in selected if c.component_type == "skill"]
    plugins = [c for c in selected if c.component_type == "plugin"]
    agents = [c for c in selected if c.component_type == "agent"]
    rules = [c for c in selected if c.component_type == "rule"]
    mcp_servers = [c for c in selected if c.component_type == "mcp_server"]

    # Steps 2-6: Copy file-based components
    for component_list in [hooks, skills, agents, rules]:
        for component in component_list:
            ok = copy_component(
                component,
                COMPONENTS_DIR,
                claude_dir,
                dry_run=dry_run,
                verbose=verbose,
            )
            if ok:
                installed.append(component)
            else:
                errors.append(f"Failed to copy {component.id}")

    # Step 4: Install plugins
    for component in plugins:
        ok = install_plugin(component.source, dry_run=dry_run)
        if ok:
            installed.append(component)
        else:
            errors.append(f"Failed to install plugin {component.id}")

    # Step 7: Register MCP servers (copy source if bundled + register)
    for component in mcp_servers:
        source_path = COMPONENTS_DIR / component.source
        if source_path.exists():
            # Bundled source — copy then register
            ok = copy_component(
                component,
                COMPONENTS_DIR,
                claude_dir,
                dry_run=dry_run,
                verbose=verbose,
            )
            if not ok:
                errors.append(f"Failed to copy MCP server {component.id}")
                continue
        # Register via `claude mcp add` (works for both bundled and external packages)
        reg_ok = register_mcp(component, env, dry_run=dry_run)
        if reg_ok:
            installed.append(component)
        else:
            errors.append(f"Failed to register MCP server {component.id}")

    # Step 8: Merge hook registrations into settings.json
    if hooks and not dry_run:
        additions = build_hook_additions(hooks, home)
        try:
            existing = {}
            if settings_path.exists():
                existing = json.loads(settings_path.read_text(encoding="utf-8"))
            merged = merge_settings(existing, additions)
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(
                json.dumps(merged, indent=2) + "\n", encoding="utf-8"
            )
            if verbose:
                _log("Merged hook registrations into settings.json")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"Failed to merge settings.json: {exc}")

    # Step 9: Render + write/merge CLAUDE.md
    # This is handled by the templater module in the full wizard flow.
    # The installer provides the merge infrastructure; the wizard calls
    # templater.render_template() and writes the result.

    # Step 10: Write install log
    if not dry_run:
        write_install_log(installed, env)

    # Step 11: Verify
    issues = verify_installation(installed, env)
    if issues:
        errors.extend(issues)

    if errors:
        _log("Installation completed with issues:")
        for err in errors:
            _log(f"  - {err}")
        return 1

    if verbose or not dry_run:
        _log(f"Successfully installed {len(installed)} components.")
    return 0


# ---------------------------------------------------------------------------
# Settings merge
# ---------------------------------------------------------------------------


def merge_settings(existing: dict, additions: dict) -> dict:
    """Deep merge settings.json with hook-aware duplicate detection.

    CRITICAL: The hook schema is nested::

        hooks -> event_type -> [{matcher, hooks: [{type, command, timeout}]}]

    Rules:
    - Never overwrite scalar values (model, permissions)
    - Hooks: find matching event+matcher group, append if command not duplicate
    - Plugins: add new keys, never override existing true/false
    - MCP servers: add new, never touch existing
    - Duplicate detection for hooks is by command string only (ignore timeout)
    """
    merged = deepcopy(existing)

    # --- Hooks ---
    for event, new_groups in additions.get("hooks", {}).items():
        event_list = merged.setdefault("hooks", {}).setdefault(event, [])
        for new_group in new_groups:
            matcher = new_group["matcher"]
            existing_group = next(
                (g for g in event_list if g["matcher"] == matcher), None
            )
            if existing_group is None:
                event_list.append(deepcopy(new_group))
            else:
                existing_cmds = {h["command"] for h in existing_group["hooks"]}
                for hook_obj in new_group["hooks"]:
                    if hook_obj["command"] not in existing_cmds:
                        existing_group["hooks"].append(deepcopy(hook_obj))

    # --- Plugins ---
    for plugin, enabled in additions.get("enabledPlugins", {}).items():
        if plugin not in merged.get("enabledPlugins", {}):
            merged.setdefault("enabledPlugins", {})[plugin] = enabled

    # --- MCP Servers ---
    for server, config in additions.get("mcpServers", {}).items():
        if server not in merged.get("mcpServers", {}):
            merged.setdefault("mcpServers", {})[server] = deepcopy(config)

    return merged


# ---------------------------------------------------------------------------
# Backup / rollback
# ---------------------------------------------------------------------------


def backup_file(path: Path) -> Path | None:
    """Create timestamped backup. Returns backup path, or None if source doesn't exist."""
    if not path.exists():
        return None
    ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup = path.parent / f"{path.stem}.backup.{ts}{path.suffix}"
    shutil.copy2(path, backup)
    return backup


def rollback(env: dict) -> int:
    """Restore settings.json + CLAUDE.md from latest timestamped backup.

    Scans ``claude_dir`` for ``*.backup.*`` files matching settings.json
    and CLAUDE.md, picks the most recent by filename timestamp, and copies
    it back over the original.

    Returns 0 on success, 1 on failure.
    """
    claude_dir = Path(env["claude_dir"])
    restored = 0
    errors = 0

    for target_name in ("settings.json", "CLAUDE.md"):
        target = claude_dir / target_name
        stem = Path(target_name).stem
        suffix = Path(target_name).suffix

        # Find all backups matching the pattern: <stem>.backup.<timestamp><suffix>
        pattern = f"{stem}.backup.*{suffix}"
        backups = sorted(claude_dir.glob(pattern))

        if not backups:
            _log(f"No backup found for {target_name}")
            continue

        latest = backups[-1]  # sorted alphabetically = chronologically
        try:
            shutil.copy2(latest, target)
            _log(f"Restored {target_name} from {latest.name}")
            restored += 1
        except OSError as exc:
            _log(f"Failed to restore {target_name}: {exc}")
            errors += 1

    if errors > 0:
        return 1
    if restored == 0:
        _log("No backups found to restore.")
        return 1
    return 0


# ---------------------------------------------------------------------------
# File copy
# ---------------------------------------------------------------------------


def copy_component(
    component: "Component",
    source_dir: Path,
    claude_dir: Path,
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Copy a component file or directory to its target location.

    Conflict resolution:
    - Target doesn't exist: copy
    - Target exists, same content: skip silently
    - Target exists, different content: overwrite with backup

    For hooks (single files): copy to ``~/.claude/scripts/hooks/``
    For skills (directories): ``shutil.copytree`` to ``~/.claude/skills/<name>/``
    For agents (files): copy to ``~/.claude/agents/``
    For rules (files): copy to ``~/.claude/rules/``
    For MCP servers (directories): ``shutil.copytree`` to ``~/.claude/mcp-servers/<name>/``
    """
    comp_type = component.component_type
    subdir = _TARGET_DIRS.get(comp_type)
    if subdir is None:
        return False

    source = source_dir / component.source
    target_parent = claude_dir / subdir

    if not source.exists():
        if verbose:
            _log(f"Source not found: {source}")
        return False

    if dry_run:
        if source.is_dir():
            _log(
                f"[dry-run] Would copy directory {source} -> {target_parent / source.name}"
            )
        else:
            _log(f"[dry-run] Would copy {source} -> {target_parent / source.name}")
        return True

    target_parent.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        target = target_parent / source.name
        if target.exists():
            # Check if contents are identical
            dcmp = filecmp.dircmp(str(source), str(target))
            if not dcmp.diff_files and not dcmp.left_only and not dcmp.right_only:
                if verbose:
                    _log(f"Skipped (identical): {component.id}")
                return True
            # Different content — backup and overwrite
            backup_dir = (
                target.parent
                / f"{target.name}.backup.{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
            )
            shutil.copytree(target, backup_dir)
            shutil.rmtree(target)

        shutil.copytree(source, target)
        if verbose:
            _log(f"Copied directory: {component.id} -> {target}")
    else:
        target = target_parent / source.name
        if target.exists():
            if filecmp.cmp(str(source), str(target), shallow=False):
                if verbose:
                    _log(f"Skipped (identical): {component.id}")
                return True
            # Different content — backup and overwrite
            backup_file(target)

        shutil.copy2(source, target)
        if verbose:
            _log(f"Copied: {component.id} -> {target}")

    return True


# ---------------------------------------------------------------------------
# Plugin installation
# ---------------------------------------------------------------------------


def install_plugin(plugin_id: str, *, dry_run: bool = False) -> bool:
    """Run ``claude plugin install <id>``. Returns True on success.

    The *plugin_id* is expected to include the marketplace suffix,
    e.g. ``superpowers@claude-plugins-official``.
    """
    if dry_run:
        _log(f"[dry-run] Would install plugin: {plugin_id}")
        return True

    try:
        result = subprocess.run(
            ["claude", "plugin", "install", plugin_id],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------


def register_mcp(component: "Component", env: dict, *, dry_run: bool = False) -> bool:
    """Register MCP server via ``claude mcp add``.

    Expands ``~`` in paths to the actual home directory before registering.
    """
    if component.mcp_config is None:
        return False

    home = Path(env["home"])
    config = component.mcp_config

    # Expand ~ in args
    expanded_args = [
        arg.replace("~", str(home)) if "~" in arg else arg for arg in config.args
    ]

    if dry_run:
        _log(
            f"[dry-run] Would register MCP: claude mcp add {component.id} "
            f"{config.command} {' '.join(expanded_args)}"
        )
        return True

    cmd = ["claude", "mcp", "add", component.id, config.command, *expanded_args]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


# ---------------------------------------------------------------------------
# Hook addition builder
# ---------------------------------------------------------------------------


def build_hook_additions(components: list[Component], home: Path) -> dict:
    """Build the hooks dict to merge into settings.json.

    Expands ``~`` in command strings to the actual home path.
    Groups registrations by event and matcher.

    Returns a structure like::

        {"hooks": {"PreToolUse": [{"matcher": "^Bash$", "hooks": [...]}]}}
    """
    # Intermediate: event -> matcher -> list of hook entry dicts
    grouped: dict[str, dict[str, list[dict]]] = {}

    for component in components:
        if component.registrations is None:
            continue
        for reg in component.registrations:
            expanded_command = reg.command.replace("~", str(home))
            entry = {
                "type": "command",
                "command": expanded_command,
                "timeout": reg.timeout,
            }

            event_group = grouped.setdefault(reg.event, {})
            matcher_list = event_group.setdefault(reg.matcher, [])
            matcher_list.append(entry)

    # Convert intermediate structure to final schema
    hooks: dict[str, list[dict]] = {}
    for event, matchers in grouped.items():
        event_list: list[dict] = []
        for matcher, hook_entries in matchers.items():
            event_list.append(
                {
                    "matcher": matcher,
                    "hooks": hook_entries,
                }
            )
        hooks[event] = event_list

    return {"hooks": hooks}


def build_hook_entry(reg: "HookRegistration") -> dict:
    """Convert a HookRegistration to the JSON object format."""
    return {"type": "command", "command": reg.command, "timeout": reg.timeout}


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify_installation(selected: list[Component], env: dict) -> list[str]:
    """Health check all installed components. Returns list of issues."""
    claude_dir = Path(env["claude_dir"])
    issues: list[str] = []

    for component in selected:
        comp_type = component.component_type

        if comp_type == "hook":
            # Check file exists
            hook_file = claude_dir / "scripts" / "hooks" / Path(component.source).name
            if not hook_file.exists():
                issues.append(f"Hook file missing: {hook_file}")

        elif comp_type == "skill":
            skill_dir = claude_dir / "skills" / Path(component.source).name
            if not skill_dir.is_dir():
                issues.append(f"Skill directory missing: {skill_dir}")

        elif comp_type == "agent":
            agent_file = claude_dir / "agents" / Path(component.source).name
            if not agent_file.exists():
                issues.append(f"Agent file missing: {agent_file}")

        elif comp_type == "rule":
            rule_file = claude_dir / "rules" / Path(component.source).name
            if not rule_file.exists():
                issues.append(f"Rule file missing: {rule_file}")

        elif comp_type == "mcp_server":
            mcp_dir = claude_dir / "mcp-servers" / Path(component.source).name
            # openscad is registered only, not always copied
            if component.id != "openscad" and not mcp_dir.is_dir():
                issues.append(f"MCP server directory missing: {mcp_dir}")

        elif comp_type == "plugin":
            # Plugin verification would require running `claude plugin list`
            # which is slow — skip for now, trust install exit code
            pass

    return issues


# ---------------------------------------------------------------------------
# Install log
# ---------------------------------------------------------------------------


def write_install_log(selected: list[Component], env: dict) -> None:
    """Log all installed component IDs and paths to ~/.claude/.wizard-install-log."""
    claude_dir = Path(env["claude_dir"])
    log_path = claude_dir / ".wizard-install-log"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# Wizard install log - {ts}", ""]

    for component in selected:
        comp_type = component.component_type
        subdir = _TARGET_DIRS.get(comp_type, "")
        if comp_type == "plugin":
            lines.append(f"plugin: {component.source}")
        else:
            target = claude_dir / subdir / Path(component.source).name
            lines.append(f"{comp_type}: {target}")

    lines.append("")
    try:
        log_path.write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _log(msg: str) -> None:
    """Print a message to stderr."""
    print(msg, file=sys.stderr)
