"""Interactive TUI wizard for the Claude & Antigravity Workspace Setup.

Uses ``rich`` to present a beautiful interactive setup wizard that walks
users through selecting components to install.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

if TYPE_CHECKING:
    from .registry import Component

console = Console()

# Category definitions for the wizard screens
WIZARD_CATEGORIES: list[tuple[str, str, str | None]] = [
    ("Hooks -- Safety", "hook", "safety"),
    ("Hooks -- CI/CD", "hook", "ci-cd"),
    ("Hooks -- Quality", "hook", "quality"),
    ("Skills -- Essential", "skill", "essential"),
    ("Skills -- Domain", "skill", "domain"),
    ("Skills -- Hardware", "skill", "hardware"),
    ("Plugins", "plugin", None),
    ("Agents", "agent", None),
    ("Rules", "rule", None),
    ("MCP Servers -- Core", "mcp_server", "llm"),
    ("MCP Servers -- Hardware", "mcp_server", "hardware"),
]


# ---------------------------------------------------------------------------
# Main wizard flow
# ---------------------------------------------------------------------------


def run_wizard(registry: list[Component], env: dict) -> list[Component] | None:
    """Main wizard flow. Returns selected components or ``None`` if cancelled."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Claude & Antigravity Workspace Setup[/bold cyan]\n"
            "[dim]Bring your Claude Code setup to full power[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # Step 1: Show detection results
    show_detection_panel(env)

    # Step 2: Shell question (Windows only)
    if env.get("os") == "Windows":
        shell_choice = ask_shell_environment()
        if shell_choice == "powershell":
            show_powershell_warning()
            registry = filter_for_powershell(registry)
        env["shell_choice"] = shell_choice

    # Step 3: Auto-disable components with missing prereqs
    registry = apply_prereq_defaults(registry, env)

    # Step 4: Category walkthrough
    selected: list[Component] = []
    for title, comp_type, category in WIZARD_CATEGORIES:
        items = [
            c
            for c in registry
            if c.component_type == comp_type
            and (category is None or c.category == category)
        ]
        if not items:
            continue
        choices = show_category_screen(title, items, env)
        selected.extend(choices)

    if not selected:
        console.print("[yellow]No components selected. Nothing to install.[/yellow]")
        return None

    # Step 5: Prereq check
    if not show_prereq_check(selected, env):
        return None

    # Step 6: Review summary
    if not show_review_summary(selected):
        return None

    return selected


# ---------------------------------------------------------------------------
# Filter / transform helpers
# ---------------------------------------------------------------------------


def filter_for_powershell(registry: list[Component]) -> list[Component]:
    """Remove all hooks when running in PowerShell/cmd (no bash available)."""
    return [c for c in registry if c.component_type != "hook"]


def apply_prereq_defaults(
    registry: list[Component], env: dict
) -> list[Component]:
    """Auto-set ``default=False`` for hardware components whose prereqs are missing."""
    from dataclasses import replace

    from .detector import check_prereq

    result: list[Component] = []
    for c in registry:
        if c.prereqs and c.category == "hardware":
            missing = [p for p in c.prereqs if not check_prereq(p)]
            if missing:
                c = replace(c, default=False)
        result.append(c)
    return result


def group_by_category(
    registry: list[Component],
) -> list[tuple[str, list[Component]]]:
    """Group components by wizard category. Returns list of ``(title, components)``."""
    groups: list[tuple[str, list[Component]]] = []
    for title, comp_type, category in WIZARD_CATEGORIES:
        items = [
            c
            for c in registry
            if c.component_type == comp_type
            and (category is None or c.category == category)
        ]
        if items:
            groups.append((title, items))
    return groups


# ---------------------------------------------------------------------------
# Detection panel
# ---------------------------------------------------------------------------


def show_detection_panel(env: dict) -> None:
    """Display a rich table showing detected environment details."""
    table = Table(
        title="Detected Environment",
        box=box.ROUNDED,
        show_header=False,
        title_style="bold white",
        padding=(0, 2),
    )
    table.add_column("Property", style="bold", min_width=20)
    table.add_column("Value", min_width=40)

    ok = "[green]OK[/green]"
    miss = "[red]X[/red]"

    table.add_row("OS", str(env.get("os", "unknown")))
    table.add_row("Shell", str(env.get("shell", "unknown")))
    table.add_row("Home", str(env.get("home", "~")))

    claude_status = ok if env.get("claude_installed") else miss
    table.add_row("Claude Code", claude_status)

    ag_status = ok if env.get("antigravity_installed") else miss
    table.add_row("Antigravity", ag_status)

    py_ver = str(env.get("python_version", "unknown")).split("\n")[0]
    table.add_row("Python", py_ver)

    bash_status = ok if env.get("bash_available") else miss
    table.add_row("Bash", bash_status)

    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Shell environment (Windows-only)
# ---------------------------------------------------------------------------


def ask_shell_environment() -> str:
    """Ask the user which shell they are using on Windows.

    Returns one of ``'wsl'``, ``'git-bash'``, ``'powershell'``, or ``'unsure'``.
    """
    console.print(
        Panel(
            "[bold]Which shell environment are you running?[/bold]\n\n"
            "  [cyan]wsl[/cyan]        - Windows Subsystem for Linux\n"
            "  [cyan]git-bash[/cyan]   - Git Bash / MSYS2\n"
            "  [cyan]powershell[/cyan] - PowerShell or cmd.exe\n"
            "  [cyan]unsure[/cyan]     - Not sure (we'll assume PowerShell)",
            title="Shell Environment",
            border_style="blue",
        )
    )
    choice = Prompt.ask(
        "Shell",
        choices=["wsl", "git-bash", "powershell", "unsure"],
        default="unsure",
    )
    if choice == "unsure":
        return "powershell"
    return choice


def show_powershell_warning() -> None:
    """Show a warning that hooks will be skipped under PowerShell."""
    console.print(
        Panel(
            "[bold yellow]PowerShell detected[/bold yellow]\n\n"
            "Hooks require bash and will be [bold]skipped[/bold].\n"
            "Skills, plugins, agents, rules, and MCP servers will still "
            "be available.\n\n"
            "[dim]Tip: Install WSL or Git Bash to enable hooks.[/dim]",
            title="Warning",
            border_style="yellow",
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Category screen with toggle selection
# ---------------------------------------------------------------------------


def show_category_screen(
    title: str, items: list[Component], env: dict
) -> list[Component]:
    """Show one category screen with numbered toggle checkboxes.

    Users type numbers to toggle, ``a`` for all on, ``n`` for all off,
    or press Enter to accept the current selection and continue.

    Returns the list of selected components from this category.
    """
    selected = [c.default for c in items]

    while True:
        console.print()
        console.print(
            Panel(
                f"[bold]{title}[/bold]",
                border_style="cyan",
                padding=(0, 2),
            )
        )

        for idx, comp in enumerate(items, 1):
            mark = "[green]x[/green]" if selected[idx - 1] else " "
            prereq_warn = ""
            if comp.prereqs:
                from .detector import check_prereq

                missing = [p for p in comp.prereqs if not check_prereq(p)]
                if missing:
                    prereq_warn = (
                        f"  [dim yellow](needs: {', '.join(missing)})[/dim yellow]"
                    )

            console.print(
                f"  [bold]{idx:>2}[/bold]) [{mark}] "
                f"[bold white]{comp.name}[/bold white] "
                f"[dim]-- {comp.description}[/dim]{prereq_warn}"
            )

        console.print()
        console.print(
            "[dim]Toggle: type numbers (e.g. 1 3 5) | "
            "[bold]a[/bold]=all on | [bold]n[/bold]=all off | "
            "Enter=continue[/dim]"
        )

        answer = Prompt.ask("Selection", default="").strip()

        if answer == "":
            break
        elif answer.lower() == "a":
            selected = [True] * len(items)
        elif answer.lower() == "n":
            selected = [False] * len(items)
        else:
            # Parse space-separated or comma-separated numbers
            tokens = answer.replace(",", " ").split()
            for token in tokens:
                try:
                    num = int(token)
                    if 1 <= num <= len(items):
                        selected[num - 1] = not selected[num - 1]
                    else:
                        console.print(
                            f"[yellow]  {num} is out of range "
                            f"(1-{len(items)})[/yellow]"
                        )
                except ValueError:
                    console.print(
                        f"[yellow]  '{token}' is not a valid number[/yellow]"
                    )

    return [comp for comp, sel in zip(items, selected) if sel]


# ---------------------------------------------------------------------------
# Prerequisite check
# ---------------------------------------------------------------------------


def show_prereq_check(selected: list[Component], env: dict) -> bool:
    """Show prerequisite status for all selected components.

    Returns ``True`` if the user wants to continue, ``False`` to abort.
    """
    from .detector import check_prereq, get_install_hint

    # Aggregate unique prereqs across selected components
    all_prereqs: set[str] = set()
    for comp in selected:
        all_prereqs.update(comp.prereqs)

    if not all_prereqs:
        return True

    os_name = env.get("os", "Linux")

    table = Table(
        title="Prerequisite Check",
        box=box.ROUNDED,
        title_style="bold white",
    )
    table.add_column("Prerequisite", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Install Hint", style="dim")

    has_missing = False
    for prereq in sorted(all_prereqs):
        found = check_prereq(prereq)
        if found:
            status = "[green]found[/green]"
            hint = ""
        else:
            status = "[red]missing[/red]"
            hint = get_install_hint(prereq, os_name)
            has_missing = True
        table.add_row(prereq, status, hint)

    console.print()
    console.print(table)
    console.print()

    if has_missing:
        console.print(
            "[yellow]Some prerequisites are missing. Components that depend "
            "on them may not work correctly.[/yellow]"
        )
        return Confirm.ask("Continue anyway?", default=True)

    return True


# ---------------------------------------------------------------------------
# Review summary
# ---------------------------------------------------------------------------


def show_review_summary(selected: list[Component]) -> bool:
    """Show a summary of selected components and ask for confirmation.

    Returns ``True`` to proceed, ``False`` to abort.
    """
    # Count by type
    type_counts: dict[str, int] = {}
    type_names: dict[str, list[str]] = {}
    for comp in selected:
        ctype = comp.component_type
        type_counts[ctype] = type_counts.get(ctype, 0) + 1
        type_names.setdefault(ctype, []).append(comp.name)

    # Friendly type labels
    labels: dict[str, str] = {
        "hook": "Hooks",
        "skill": "Skills",
        "plugin": "Plugins",
        "agent": "Agents",
        "rule": "Rules",
        "mcp_server": "MCP Servers",
    }

    # Summary counts table
    summary_table = Table(
        title="Installation Summary",
        box=box.ROUNDED,
        title_style="bold white",
    )
    summary_table.add_column("Type", style="bold")
    summary_table.add_column("Count", justify="right", style="cyan")
    summary_table.add_column("Components", style="dim")

    display_order = ["hook", "skill", "plugin", "agent", "rule", "mcp_server"]
    for ctype in display_order:
        if ctype in type_counts:
            names_str = ", ".join(sorted(type_names[ctype]))
            summary_table.add_row(
                labels.get(ctype, ctype),
                str(type_counts[ctype]),
                names_str,
            )

    # Total row
    summary_table.add_section()
    summary_table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{len(selected)}[/bold]",
        "",
    )

    console.print()
    console.print(summary_table)
    console.print()

    return Confirm.ask("Proceed with installation?", default=True)
