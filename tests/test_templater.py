from __future__ import annotations

from pathlib import Path

from lib.templater import build_template_context, expand_home, render_template


def test_expand_home_replaces_tilde():
    result = expand_home("~/.claude/scripts")
    assert "~" not in result
    assert result.startswith(str(Path.home()))


def test_expand_home_leaves_absolute_paths():
    result = expand_home("/usr/bin/python3")
    assert result == "/usr/bin/python3"


def test_render_template_substitutes_vars(tmp_path):
    tpl = tmp_path / "test.template"
    tpl.write_text("Hello $NAME, home is $HOME")
    result = render_template(tpl, {"NAME": "World", "HOME": "/test"})
    assert result == "Hello World, home is /test"


def test_render_template_safe_substitute_leaves_unknown(tmp_path):
    tpl = tmp_path / "test.template"
    tpl.write_text("$KNOWN and $UNKNOWN")
    result = render_template(tpl, {"KNOWN": "yes"})
    assert "yes" in result
    assert "$UNKNOWN" in result  # safe_substitute leaves unknowns


def test_build_template_context_has_required_keys():
    env = {"os": "Linux", "home": Path.home(), "python_version": "3.10"}
    # Use a minimal fake component list
    from lib.registry import Component

    fake = [
        Component(
            id="test",
            name="Test",
            description="desc",
            category="test",
            component_type="hook",
            default=True,
            source="test.sh",
            prereqs=[],
            registrations=None,
            mcp_config=None,
        )
    ]
    ctx = build_template_context(env, fake)
    assert "HOME" in ctx
    assert "COMPONENTS_TABLE" in ctx
    assert ctx["HOOKS_COUNT"] == "1"
