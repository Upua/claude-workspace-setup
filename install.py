#!/usr/bin/env python3
"""Claude & Antigravity Workspace Setup Wizard.

Usage:
    python install.py                  # Interactive wizard
    python install.py --dry-run        # Preview without installing
    python install.py --rollback       # Restore from backup
    python install.py --verbose        # Detailed output
    python install.py --all            # Install everything, no prompts
    python install.py --minimal        # Install only essential components
"""
from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Claude & Antigravity Workspace Setup Wizard",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without installing",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Restore settings.json + CLAUDE.md from backup",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Detailed output",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Install everything, no prompts",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Install only essential components (no hardware, no MCP servers)",
    )
    return parser.parse_args()


def ensure_rich() -> bool:
    """Ensure rich is installed. Returns True if available."""
    try:
        import rich  # noqa: F401

        return True
    except ImportError:
        print("The 'rich' library is required for the interactive wizard.")
        print("Install it with: pip install rich>=13.0.0")
        try:
            resp = input("Install now? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        if resp in ("", "y", "yes"):
            import subprocess

            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "rich>=13.0.0"],
                )
                return True
            except subprocess.CalledProcessError:
                print("Failed to install rich. Please install manually.")
                return False
        return False


def main() -> int:
    args = parse_args()

    if not ensure_rich():
        return 1

    from rich.console import Console

    console = Console()

    from lib.detector import detect_environment
    from lib.registry import get_registry

    env = detect_environment()
    registry = get_registry()

    if args.rollback:
        from lib.installer import rollback

        return rollback(env)

    if args.all:
        selected = registry
        console.print(
            f"[bold cyan]Installing all {len(selected)} components...[/bold cyan]"
        )
    elif args.minimal:
        selected = [
            c
            for c in registry
            if c.default
            and c.category not in ("hardware",)
            and c.component_type != "mcp_server"
        ]
        console.print(
            f"[bold cyan]Installing {len(selected)} essential components...[/bold cyan]"
        )
    else:
        from lib.wizard import run_wizard

        selected = run_wizard(registry, env)
        if selected is None:
            console.print("[yellow]Setup cancelled.[/yellow]")
            return 0

    from lib.installer import run_install

    return run_install(selected, env, dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
