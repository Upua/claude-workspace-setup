"""Tests for the interactive TUI wizard."""

from __future__ import annotations

from lib.registry import get_registry
from lib.wizard import apply_prereq_defaults, filter_for_powershell, group_by_category


def test_filter_for_powershell_removes_all_hooks() -> None:
    registry = get_registry()
    filtered = filter_for_powershell(registry)
    hook_count = sum(1 for c in filtered if c.component_type == "hook")
    assert hook_count == 0


def test_filter_for_powershell_keeps_non_hooks() -> None:
    registry = get_registry()
    original_non_hooks = sum(1 for c in registry if c.component_type != "hook")
    filtered = filter_for_powershell(registry)
    assert len(filtered) == original_non_hooks


def test_group_by_category_returns_all_groups() -> None:
    registry = get_registry()
    groups = group_by_category(registry)
    assert len(groups) >= 6  # hooks, skills, plugins, agents, rules, mcps
    # Each group should have items
    for title, items in groups:
        assert len(items) > 0, f"Empty group: {title}"


def test_group_by_category_covers_all_components() -> None:
    registry = get_registry()
    groups = group_by_category(registry)
    total = sum(len(items) for _, items in groups)
    assert total == len(registry)


def test_apply_prereq_defaults_marks_hardware_missing() -> None:
    """Hardware components with missing prereqs should default to False."""
    from unittest.mock import patch

    registry = get_registry()
    hardware = [c for c in registry if c.category == "hardware" and c.prereqs]
    if not hardware:
        return  # skip if no hardware with prereqs

    with patch("lib.detector.check_prereq", return_value=False):
        env: dict = {"os": "Linux"}
        result = apply_prereq_defaults(registry, env)
        hw_result = [c for c in result if c.category == "hardware" and c.prereqs]
        for c in hw_result:
            assert c.default is False
