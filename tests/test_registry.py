"""Tests for the component registry."""

from __future__ import annotations


from lib.registry import (
    Component,
    HookRegistration,
    McpServerConfig,
    get_all_prereqs,
    get_by_category,
    get_by_type,
    get_registry,
)


def test_registry_returns_list_of_components() -> None:
    registry = get_registry()
    assert isinstance(registry, list)
    assert len(registry) > 0
    assert all(isinstance(c, Component) for c in registry)


def test_all_hooks_have_registrations() -> None:
    registry = get_registry()
    hooks = [c for c in registry if c.component_type == "hook"]
    for hook in hooks:
        assert hook.registrations is not None, f"{hook.id} missing registrations"
        assert len(hook.registrations) > 0, f"{hook.id} has empty registrations"


def test_all_hooks_require_jq() -> None:
    registry = get_registry()
    hooks = [c for c in registry if c.component_type == "hook"]
    for hook in hooks:
        assert "jq" in hook.prereqs, f"{hook.id} missing jq prereq"


def test_all_mcp_servers_have_config() -> None:
    registry = get_registry()
    mcps = [c for c in registry if c.component_type == "mcp_server"]
    for mcp in mcps:
        assert mcp.mcp_config is not None, f"{mcp.id} missing mcp_config"


def test_no_duplicate_ids() -> None:
    registry = get_registry()
    ids = [c.id for c in registry]
    assert len(ids) == len(set(ids)), (
        f"Duplicate IDs: {[i for i in ids if ids.count(i) > 1]}"
    )


def test_component_types_valid() -> None:
    valid_types = {"hook", "skill", "plugin", "agent", "rule", "mcp_server"}
    registry = get_registry()
    for c in registry:
        assert c.component_type in valid_types, (
            f"{c.id} has invalid type {c.component_type}"
        )


def test_hook_registration_has_timeout() -> None:
    registry = get_registry()
    hooks = [c for c in registry if c.component_type == "hook"]
    for hook in hooks:
        assert hook.registrations is not None
        for reg in hook.registrations:
            assert reg.timeout > 0, f"{hook.id} registration missing timeout"


def test_category_grouping() -> None:
    """Verify all component_type groups are present."""
    registry = get_registry()
    types_found = {c.component_type for c in registry}
    expected_types = {"hook", "skill", "plugin", "agent", "rule", "mcp_server"}
    assert expected_types == types_found


def test_total_component_count() -> None:
    """Verify the registry has exactly 42 components."""
    registry = get_registry()
    assert len(registry) == 42


def test_component_counts_by_type() -> None:
    """Verify expected counts per component type."""
    assert len(get_by_type("hook")) == 6
    assert len(get_by_type("skill")) == 13
    assert len(get_by_type("plugin")) == 10
    assert len(get_by_type("agent")) == 7
    assert len(get_by_type("rule")) == 3
    assert len(get_by_type("mcp_server")) == 3


def test_get_by_category() -> None:
    """Verify category filtering works."""
    essential_skills = get_by_category("essential")
    assert len(essential_skills) == 6
    assert all(c.component_type == "skill" for c in essential_skills)


def test_get_all_prereqs() -> None:
    """Verify prereq collection works."""
    registry = get_registry()
    prereqs = get_all_prereqs(registry)
    assert "jq" in prereqs
    assert "ssh" in prereqs
    assert "openscad" in prereqs
    assert "platformio" in prereqs
    assert "uv" in prereqs


def test_get_registry_returns_copy() -> None:
    """Modifying the returned list should not affect the source."""
    reg1 = get_registry()
    reg1.pop()
    reg2 = get_registry()
    assert len(reg2) == 42


def test_hook_registration_dataclass() -> None:
    """Verify HookRegistration defaults."""
    reg = HookRegistration(event="PreToolUse", matcher="^Bash$", command="test")
    assert reg.timeout == 5000


def test_mcp_server_config_dataclass() -> None:
    """Verify McpServerConfig defaults."""
    cfg = McpServerConfig(command="python3")
    assert cfg.args == []
    assert cfg.env is None
