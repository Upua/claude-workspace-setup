"""Tests for the installer module."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


from lib.installer import (
    backup_file,
    build_hook_additions,
    build_hook_entry,
    merge_settings,
    rollback,
)
from lib.registry import Component, HookRegistration


# ---------------------------------------------------------------------------
# merge_settings — hooks
# ---------------------------------------------------------------------------


class TestMergeSettingsHooks:
    def test_adds_new_hook(self) -> None:
        existing: dict = {"hooks": {}}
        additions = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash test.sh",
                                "timeout": 5000,
                            }
                        ],
                    }
                ]
            }
        }
        result = merge_settings(existing, additions)
        assert len(result["hooks"]["PreToolUse"]) == 1
        assert result["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "bash test.sh"

    def test_skips_duplicate_hook_and_preserves_existing_timeout(self) -> None:
        existing = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash test.sh",
                                "timeout": 5000,
                            }
                        ],
                    }
                ]
            }
        }
        additions = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash test.sh",
                                "timeout": 3000,
                            }
                        ],
                    }
                ]
            }
        }
        result = merge_settings(existing, additions)
        # Should still be 1 hook, not 2 — duplicate by command string
        assert len(result["hooks"]["PreToolUse"][0]["hooks"]) == 1
        # Timeout preserved from existing (5000), not overwritten by addition (3000)
        assert result["hooks"]["PreToolUse"][0]["hooks"][0]["timeout"] == 5000

    def test_appends_to_existing_matcher(self) -> None:
        existing = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash existing.sh",
                                "timeout": 5000,
                            }
                        ],
                    }
                ]
            }
        }
        additions = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash new.sh",
                                "timeout": 5000,
                            }
                        ],
                    }
                ]
            }
        }
        result = merge_settings(existing, additions)
        assert len(result["hooks"]["PreToolUse"][0]["hooks"]) == 2

    def test_preserves_scalar_values(self) -> None:
        existing = {"model": "sonnet", "hooks": {}}
        additions: dict = {"hooks": {}}
        result = merge_settings(existing, additions)
        assert result["model"] == "sonnet"

    def test_creates_hooks_key_when_missing(self) -> None:
        existing: dict = {}
        additions = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash test.sh",
                                "timeout": 5000,
                            }
                        ],
                    }
                ]
            }
        }
        result = merge_settings(existing, additions)
        assert "hooks" in result
        assert len(result["hooks"]["PreToolUse"]) == 1

    def test_adds_new_matcher_group_to_existing_event(self) -> None:
        existing = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash a.sh",
                                "timeout": 5000,
                            }
                        ],
                    }
                ]
            }
        }
        additions = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^(Write|Edit|MultiEdit)$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash b.sh",
                                "timeout": 2000,
                            }
                        ],
                    }
                ]
            }
        }
        result = merge_settings(existing, additions)
        # Should now have 2 matcher groups under PreToolUse
        assert len(result["hooks"]["PreToolUse"]) == 2

    def test_does_not_mutate_existing(self) -> None:
        existing = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash a.sh",
                                "timeout": 5000,
                            }
                        ],
                    }
                ]
            }
        }
        additions = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash b.sh",
                                "timeout": 5000,
                            }
                        ],
                    }
                ]
            }
        }
        merge_settings(existing, additions)
        # Original should still have only 1 hook
        assert len(existing["hooks"]["PreToolUse"][0]["hooks"]) == 1


# ---------------------------------------------------------------------------
# merge_settings — plugins
# ---------------------------------------------------------------------------


class TestMergeSettingsPlugins:
    def test_does_not_override_existing_plugin(self) -> None:
        existing = {"enabledPlugins": {"foo@bar": False}}
        additions = {"enabledPlugins": {"foo@bar": True, "new@bar": True}}
        result = merge_settings(existing, additions)
        assert result["enabledPlugins"]["foo@bar"] is False  # preserved
        assert result["enabledPlugins"]["new@bar"] is True  # added

    def test_adds_new_plugin(self) -> None:
        existing: dict = {"enabledPlugins": {}}
        additions = {"enabledPlugins": {"new@bar": True}}
        result = merge_settings(existing, additions)
        assert result["enabledPlugins"]["new@bar"] is True

    def test_creates_plugins_key_when_missing(self) -> None:
        existing: dict = {}
        additions = {"enabledPlugins": {"new@bar": True}}
        result = merge_settings(existing, additions)
        assert result["enabledPlugins"]["new@bar"] is True


# ---------------------------------------------------------------------------
# merge_settings — MCP servers
# ---------------------------------------------------------------------------


class TestMergeSettingsMcp:
    def test_adds_new_mcp_server(self) -> None:
        existing: dict = {"mcpServers": {}}
        additions = {"mcpServers": {"test": {"command": "python3", "args": []}}}
        result = merge_settings(existing, additions)
        assert "test" in result["mcpServers"]

    def test_does_not_override_existing_mcp(self) -> None:
        existing = {"mcpServers": {"test": {"command": "old"}}}
        additions = {"mcpServers": {"test": {"command": "new"}}}
        result = merge_settings(existing, additions)
        assert result["mcpServers"]["test"]["command"] == "old"

    def test_creates_mcp_key_when_missing(self) -> None:
        existing: dict = {}
        additions = {"mcpServers": {"test": {"command": "python3", "args": []}}}
        result = merge_settings(existing, additions)
        assert "test" in result["mcpServers"]


# ---------------------------------------------------------------------------
# build_hook_entry
# ---------------------------------------------------------------------------


class TestBuildHookEntry:
    def test_produces_correct_format(self) -> None:
        reg = HookRegistration("PreToolUse", "^Bash$", "bash test.sh", 5000)
        entry = build_hook_entry(reg)
        assert entry == {
            "type": "command",
            "command": "bash test.sh",
            "timeout": 5000,
        }

    def test_default_timeout(self) -> None:
        reg = HookRegistration("PreToolUse", "^Bash$", "bash test.sh")
        entry = build_hook_entry(reg)
        assert entry["timeout"] == 5000


# ---------------------------------------------------------------------------
# build_hook_additions
# ---------------------------------------------------------------------------


class TestBuildHookAdditions:
    def test_groups_by_event_and_matcher(self) -> None:
        components = [
            Component(
                id="hook-a",
                name="Hook A",
                description="test",
                category="safety",
                component_type="hook",
                default=True,
                source="hooks/a.sh",
                prereqs=["jq"],
                registrations=[
                    HookRegistration("PreToolUse", "^Bash$", "bash ~/a.sh gate", 5000),
                    HookRegistration(
                        "PostToolUse", "^Bash$", "bash ~/a.sh check", 2000
                    ),
                ],
            ),
            Component(
                id="hook-b",
                name="Hook B",
                description="test",
                category="safety",
                component_type="hook",
                default=True,
                source="hooks/b.sh",
                prereqs=["jq"],
                registrations=[
                    HookRegistration("PreToolUse", "^Bash$", "bash ~/b.sh", 5000),
                ],
            ),
        ]
        home = Path("/test/home")
        result = build_hook_additions(components, home)

        assert "hooks" in result
        # PreToolUse should have one matcher group with 2 hooks
        pre = result["hooks"]["PreToolUse"]
        assert len(pre) == 1
        assert pre[0]["matcher"] == "^Bash$"
        assert len(pre[0]["hooks"]) == 2

        # PostToolUse should have one matcher group with 1 hook
        post = result["hooks"]["PostToolUse"]
        assert len(post) == 1
        assert len(post[0]["hooks"]) == 1

    def test_expands_tilde_in_commands(self) -> None:
        components = [
            Component(
                id="hook-c",
                name="Hook C",
                description="test",
                category="safety",
                component_type="hook",
                default=True,
                source="hooks/c.sh",
                prereqs=["jq"],
                registrations=[
                    HookRegistration(
                        "PreToolUse",
                        "^Bash$",
                        "bash ~/.claude/scripts/hooks/c.sh",
                        5000,
                    ),
                ],
            ),
        ]
        home = Path("/home/testuser")
        result = build_hook_additions(components, home)
        cmd = result["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        assert "~" not in cmd
        assert "/home/testuser/.claude/scripts/hooks/c.sh" in cmd

    def test_skips_components_without_registrations(self) -> None:
        components = [
            Component(
                id="skill-x",
                name="Skill X",
                description="test",
                category="essential",
                component_type="skill",
                default=True,
                source="skills/x",
                registrations=None,
            ),
        ]
        result = build_hook_additions(components, Path("/test"))
        assert result == {"hooks": {}}


# ---------------------------------------------------------------------------
# backup_file
# ---------------------------------------------------------------------------


class TestBackupFile:
    def test_creates_backup(self, tmp_path: Path) -> None:
        target = tmp_path / "settings.json"
        target.write_text('{"model": "original"}')
        backup = backup_file(target)
        assert backup is not None
        assert backup.exists()
        assert backup.read_text() == '{"model": "original"}'

    def test_returns_none_if_source_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "nonexistent.json"
        result = backup_file(target)
        assert result is None

    def test_backup_name_contains_timestamp(self, tmp_path: Path) -> None:
        target = tmp_path / "settings.json"
        target.write_text("{}")
        backup = backup_file(target)
        assert backup is not None
        assert ".backup." in backup.name
        assert backup.suffix == ".json"


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------


class TestRollback:
    def test_restores_latest_backup(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        settings.write_text('{"model": "original"}')
        bp = backup_file(settings)
        assert bp is not None

        # Modify the original
        settings.write_text('{"model": "modified"}')
        assert json.loads(settings.read_text())["model"] == "modified"

        # Rollback should restore
        env = {"claude_dir": str(tmp_path)}
        result = rollback(env)
        assert result == 0
        assert json.loads(settings.read_text())["model"] == "original"

    def test_returns_1_when_no_backups(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"
        settings.write_text('{"model": "current"}')
        env = {"claude_dir": str(tmp_path)}
        result = rollback(env)
        assert result == 1

    def test_restores_most_recent_of_multiple_backups(self, tmp_path: Path) -> None:
        settings = tmp_path / "settings.json"

        # Create first backup
        settings.write_text('{"model": "first"}')
        first_backup = tmp_path / "settings.backup.2026-01-01-120000.json"
        shutil.copy2(settings, first_backup)

        # Create second (more recent) backup
        settings.write_text('{"model": "second"}')
        second_backup = tmp_path / "settings.backup.2026-01-02-120000.json"
        shutil.copy2(settings, second_backup)

        # Modify original
        settings.write_text('{"model": "modified"}')

        env = {"claude_dir": str(tmp_path)}
        result = rollback(env)
        assert result == 0
        # Should restore from the *latest* backup (second)
        assert json.loads(settings.read_text())["model"] == "second"
