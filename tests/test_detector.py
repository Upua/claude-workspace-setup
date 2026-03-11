"""Tests for lib.detector — environment detection module."""

from __future__ import annotations

from pathlib import Path

from lib.detector import (
    INSTALL_HINTS,
    check_bash_available,
    check_prereq,
    detect_environment,
    detect_shell,
    get_install_hint,
    scan_existing,
)


# ---------------------------------------------------------------------------
# detect_environment
# ---------------------------------------------------------------------------


class TestDetectEnvironment:
    """detect_environment() returns a complete info dict."""

    REQUIRED_KEYS = {
        "os",
        "shell",
        "home",
        "claude_dir",
        "claude_installed",
        "antigravity_installed",
        "python_version",
        "existing_components",
        "bash_available",
    }

    def test_returns_dict_with_all_required_keys(self) -> None:
        env = detect_environment()
        assert isinstance(env, dict)
        assert self.REQUIRED_KEYS.issubset(env.keys()), (
            f"Missing keys: {self.REQUIRED_KEYS - env.keys()}"
        )

    def test_os_is_valid(self) -> None:
        env = detect_environment()
        assert env["os"] in ("Windows", "Linux", "Darwin"), (
            f"Unexpected OS: {env['os']}"
        )

    def test_home_exists(self) -> None:
        env = detect_environment()
        assert Path(env["home"]).is_dir()

    def test_python_version_is_string(self) -> None:
        env = detect_environment()
        assert isinstance(env["python_version"], str)
        assert len(env["python_version"]) > 0

    def test_claude_installed_is_bool(self) -> None:
        env = detect_environment()
        assert isinstance(env["claude_installed"], bool)

    def test_antigravity_installed_is_bool(self) -> None:
        env = detect_environment()
        assert isinstance(env["antigravity_installed"], bool)

    def test_bash_available_is_bool(self) -> None:
        env = detect_environment()
        assert isinstance(env["bash_available"], bool)

    def test_existing_components_is_dict(self) -> None:
        env = detect_environment()
        assert isinstance(env["existing_components"], dict)


# ---------------------------------------------------------------------------
# detect_shell
# ---------------------------------------------------------------------------


class TestDetectShell:
    """detect_shell() returns a recognised shell identifier."""

    VALID_SHELLS = {"wsl", "git-bash", "bash", "zsh", "powershell", "cmd", "unknown"}

    def test_returns_valid_string(self) -> None:
        result = detect_shell()
        assert isinstance(result, str)
        assert result in self.VALID_SHELLS, f"Unexpected shell: {result}"


# ---------------------------------------------------------------------------
# check_prereq
# ---------------------------------------------------------------------------


class TestCheckPrereq:
    """check_prereq() probes PATH for a binary."""

    def test_finds_python(self) -> None:
        # At least one of python3 / python must be available
        assert check_prereq("python3") or check_prereq("python")

    def test_missing_binary_returns_false(self) -> None:
        assert check_prereq("this_binary_does_not_exist_xyz_123") is False

    def test_returns_bool(self) -> None:
        assert isinstance(check_prereq("ls"), bool)


# ---------------------------------------------------------------------------
# check_bash_available
# ---------------------------------------------------------------------------


class TestCheckBashAvailable:
    """check_bash_available() returns a bool."""

    def test_returns_bool(self) -> None:
        result = check_bash_available()
        assert isinstance(result, bool)

    def test_true_on_posix(self) -> None:
        import platform

        if platform.system() in ("Linux", "Darwin"):
            assert check_bash_available() is True


# ---------------------------------------------------------------------------
# scan_existing
# ---------------------------------------------------------------------------


class TestScanExisting:
    """scan_existing() inventories ~/.claude/ components."""

    EXPECTED_KEYS = {"hooks", "skills", "agents", "rules", "mcp_servers"}

    def test_returns_dict_with_expected_keys(self) -> None:
        result = scan_existing()
        assert isinstance(result, dict)
        assert self.EXPECTED_KEYS.issubset(result.keys()), (
            f"Missing keys: {self.EXPECTED_KEYS - result.keys()}"
        )

    def test_values_are_lists(self) -> None:
        result = scan_existing()
        for key in self.EXPECTED_KEYS:
            assert isinstance(result[key], list), f"{key} should be a list"

    def test_list_items_are_strings(self) -> None:
        result = scan_existing()
        for key, items in result.items():
            for item in items:
                assert isinstance(item, str), (
                    f"Item in {key} should be str, got {type(item)}"
                )


# ---------------------------------------------------------------------------
# get_install_hint
# ---------------------------------------------------------------------------


class TestGetInstallHint:
    """get_install_hint() returns platform-specific install commands."""

    def test_known_prereq_linux(self) -> None:
        hint = get_install_hint("jq", "Linux")
        assert isinstance(hint, str)
        assert "jq" in hint

    def test_known_prereq_darwin(self) -> None:
        hint = get_install_hint("ruff", "Darwin")
        assert isinstance(hint, str)
        assert "ruff" in hint

    def test_known_prereq_windows(self) -> None:
        hint = get_install_hint("openscad", "Windows")
        assert isinstance(hint, str)
        assert "openscad" in hint

    def test_unknown_prereq_returns_fallback(self) -> None:
        hint = get_install_hint("some_unknown_tool", "Linux")
        assert isinstance(hint, str)
        assert "some_unknown_tool" in hint

    def test_all_hints_have_three_platforms(self) -> None:
        for prereq, platforms in INSTALL_HINTS.items():
            for os_name in ("Linux", "Darwin", "Windows"):
                assert os_name in platforms, (
                    f"INSTALL_HINTS['{prereq}'] missing '{os_name}'"
                )
