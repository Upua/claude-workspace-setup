"""Simple template engine using string.Template (no Jinja2)."""

from __future__ import annotations

import string
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .registry import Component


def render_template(template_path: Path, context: dict) -> str:
    """Render a .template file using string.Template substitution.
    $VAR_NAME placeholders are replaced with context values.
    """
    content = template_path.read_text()
    tmpl = string.Template(content)
    return tmpl.safe_substitute(context)


def expand_home(path_str: str) -> str:
    """Expand ~ to actual home directory path."""
    return str(Path(path_str).expanduser())


def build_template_context(env: dict, selected: list[Component]) -> dict:
    """Build the variable context for template rendering.

    Returns dict with keys:
    - HOME: expanded home directory
    - PYTHON: python command (python3 or python)
    - OS: operating system name
    - COMPONENTS_TABLE: markdown table of installed components
    - HOOKS_COUNT: number of hooks installed
    - SKILLS_COUNT: number of skills installed
    - PLUGINS_COUNT: number of plugins installed
    - AGENTS_COUNT: number of agents installed
    - RULES_COUNT: number of rules installed
    - MCP_COUNT: number of MCP servers installed
    """
    components_table = build_components_table(selected)

    return {
        "HOME": str(env.get("home", Path.home())),
        "PYTHON": "python3" if env.get("os") != "Windows" else "python",
        "OS": str(env.get("os", "Unknown")),
        "COMPONENTS_TABLE": components_table,
        "HOOKS_COUNT": str(sum(1 for c in selected if c.component_type == "hook")),
        "SKILLS_COUNT": str(sum(1 for c in selected if c.component_type == "skill")),
        "PLUGINS_COUNT": str(
            sum(1 for c in selected if c.component_type == "plugin")
        ),
        "AGENTS_COUNT": str(sum(1 for c in selected if c.component_type == "agent")),
        "RULES_COUNT": str(sum(1 for c in selected if c.component_type == "rule")),
        "MCP_COUNT": str(
            sum(1 for c in selected if c.component_type == "mcp_server")
        ),
    }


def build_components_table(selected: list[Component]) -> str:
    """Build a markdown table of installed components."""
    lines = ["| Type | Name | Description |", "|------|------|-------------|"]
    for c in sorted(selected, key=lambda x: (x.component_type, x.name)):
        lines.append(f"| {c.component_type} | {c.name} | {c.description} |")
    return "\n".join(lines)
