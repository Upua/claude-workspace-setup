"""Component registry — single source of truth for all installable components."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HookRegistration:
    """A single hook registration entry for settings.json."""

    event: str
    matcher: str
    command: str
    timeout: int = 5000


@dataclass
class McpServerConfig:
    """MCP server launch configuration."""

    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None


@dataclass
class Component:
    """A single installable workspace component."""

    id: str
    name: str
    description: str
    category: str
    component_type: str
    default: bool
    source: str
    prereqs: list[str] = field(default_factory=list)
    registrations: list[HookRegistration] | None = None
    mcp_config: McpServerConfig | None = None


# ---------------------------------------------------------------------------
# Complete registry — 42 components
# ---------------------------------------------------------------------------

REGISTRY: list[Component] = [
    # ===== HOOKS (6) =====
    Component(
        id="dangerous-command-blocker",
        name="Dangerous Command Blocker",
        description="Blocks destructive commands like rm -rf /, fdisk, mkfs",
        category="safety",
        component_type="hook",
        default=True,
        source="hooks/dangerous-command-blocker.sh",
        prereqs=["jq"],
        registrations=[
            HookRegistration(
                event="PreToolUse",
                matcher="^Bash$",
                command="bash ~/.claude/scripts/hooks/dangerous-command-blocker.sh",
                timeout=5000,
            ),
        ],
    ),
    Component(
        id="test-gate",
        name="Test Gate",
        description="Requires tests to pass before committing; tracks pass/fail state",
        category="ci-cd",
        component_type="hook",
        default=True,
        source="hooks/test-gate.sh",
        prereqs=["jq"],
        registrations=[
            HookRegistration(
                event="PreToolUse",
                matcher="^Bash$",
                command="bash ~/.claude/scripts/hooks/test-gate.sh gate",
                timeout=3000,
            ),
            HookRegistration(
                event="PostToolUse",
                matcher="^Bash$",
                command="bash ~/.claude/scripts/hooks/test-gate.sh check-pass",
                timeout=2000,
            ),
            HookRegistration(
                event="PostToolUse",
                matcher="^(Write|Edit|MultiEdit)$",
                command="bash ~/.claude/scripts/hooks/test-gate.sh invalidate",
                timeout=2000,
            ),
        ],
    ),
    Component(
        id="quality-gate",
        name="Quality Gate",
        description="Requires security scan before committing; tracks scan state",
        category="ci-cd",
        component_type="hook",
        default=True,
        source="hooks/quality-gate.sh",
        prereqs=["jq"],
        registrations=[
            HookRegistration(
                event="PreToolUse",
                matcher="^Bash$",
                command="bash ~/.claude/scripts/hooks/quality-gate.sh gate",
                timeout=5000,
            ),
            HookRegistration(
                event="PostToolUse",
                matcher="^Bash$",
                command="bash ~/.claude/scripts/hooks/quality-gate.sh check-security",
                timeout=2000,
            ),
            HookRegistration(
                event="PostToolUse",
                matcher="^(Write|Edit|MultiEdit)$",
                command="bash ~/.claude/scripts/hooks/quality-gate.sh invalidate",
                timeout=2000,
            ),
        ],
    ),
    Component(
        id="sensitive-file-blocker",
        name="Sensitive File Blocker",
        description="Prevents writing to .env, credentials, and secret files",
        category="safety",
        component_type="hook",
        default=True,
        source="hooks/sensitive-file-blocker.sh",
        prereqs=["jq"],
        registrations=[
            HookRegistration(
                event="PreToolUse",
                matcher="^(Write|Edit|MultiEdit)$",
                command="bash ~/.claude/scripts/hooks/sensitive-file-blocker.sh",
                timeout=5000,
            ),
        ],
    ),
    Component(
        id="auto-lint-python",
        name="Auto Lint Python",
        description="Automatically runs ruff on Python files after edits",
        category="quality",
        component_type="hook",
        default=True,
        source="hooks/auto-lint-python.sh",
        prereqs=["jq"],
        registrations=[
            HookRegistration(
                event="PostToolUse",
                matcher="^(Write|Edit|MultiEdit)$",
                command="bash ~/.claude/scripts/hooks/auto-lint-python.sh",
                timeout=5000,
            ),
        ],
    ),
    Component(
        id="pre-compact-save",
        name="Pre-Compact Save",
        description="Saves session context before memory compaction",
        category="quality",
        component_type="hook",
        default=True,
        source="hooks/pre-compact-save.sh",
        prereqs=["jq"],
        registrations=[
            HookRegistration(
                event="PreCompact",
                matcher="",
                command="bash ~/.claude/scripts/hooks/pre-compact-save.sh 2>/dev/null || true",
                timeout=5000,
            ),
        ],
    ),
    # ===== SKILLS (13) =====
    # -- Essential (6) --
    Component(
        id="code-quality",
        name="Code Quality",
        description="Linting, formatting, and code quality enforcement",
        category="essential",
        component_type="skill",
        default=True,
        source="skills/code-quality",
    ),
    Component(
        id="security",
        name="Security",
        description="Security scanning, vulnerability detection, hardening",
        category="essential",
        component_type="skill",
        default=True,
        source="skills/security",
    ),
    Component(
        id="documentation",
        name="Documentation",
        description="Auto-generate docs, docstrings, and API references",
        category="essential",
        component_type="skill",
        default=True,
        source="skills/documentation",
    ),
    Component(
        id="deployment",
        name="Deployment",
        description="Deploy workflows for Docker, systemd, cloud",
        category="essential",
        component_type="skill",
        default=True,
        source="skills/deployment",
    ),
    Component(
        id="self-healing-ci",
        name="Self-Healing CI",
        description="Automatically diagnose and fix CI pipeline failures",
        category="essential",
        component_type="skill",
        default=True,
        source="skills/self-healing-ci",
    ),
    Component(
        id="project-wizard",
        name="Project Wizard",
        description="Scaffold new projects with best-practice templates",
        category="essential",
        component_type="skill",
        default=True,
        source="skills/project-wizard",
    ),
    # -- Domain (4) --
    Component(
        id="architecture",
        name="Architecture",
        description="System design, dependency analysis, refactoring guidance",
        category="domain",
        component_type="skill",
        default=False,
        source="skills/architecture",
    ),
    Component(
        id="browser-automation",
        name="Browser Automation",
        description="Web scraping, testing, and browser control via MCP",
        category="domain",
        component_type="skill",
        default=False,
        source="skills/browser-automation",
    ),
    Component(
        id="performance-optimizer",
        name="Performance Optimizer",
        description="Profiling, bottleneck detection, optimization guidance",
        category="domain",
        component_type="skill",
        default=False,
        source="skills/performance-optimizer",
    ),
    Component(
        id="accessibility-auditor",
        name="Accessibility Auditor",
        description="WCAG compliance checking and accessibility improvements",
        category="domain",
        component_type="skill",
        default=False,
        source="skills/accessibility-auditor",
    ),
    # -- Hardware (3) --
    Component(
        id="rpi-controller",
        name="Raspberry Pi Controller",
        description="Remote Pi management, deployment, and monitoring",
        category="hardware",
        component_type="skill",
        default=False,
        source="skills/rpi-controller",
        prereqs=["ssh"],
    ),
    Component(
        id="cad-3d-printing",
        name="CAD & 3D Printing",
        description="OpenSCAD model generation, STL export, print optimization",
        category="hardware",
        component_type="skill",
        default=False,
        source="skills/cad-3d-printing",
        prereqs=["openscad"],
    ),
    Component(
        id="autonomous-flash",
        name="Autonomous Flash",
        description="PlatformIO firmware build, flash, and debug",
        category="hardware",
        component_type="skill",
        default=False,
        source="skills/autonomous-flash",
        prereqs=["platformio"],
    ),
    # ===== PLUGINS (10) =====
    Component(
        id="superpowers",
        name="Superpowers",
        description="Brainstorming, TDD, debugging workflows",
        category="workflow",
        component_type="plugin",
        default=True,
        source="superpowers@claude-plugins-official",
    ),
    Component(
        id="code-review",
        name="Code Review",
        description="Structured code review",
        category="workflow",
        component_type="plugin",
        default=True,
        source="code-review@claude-plugins-official",
    ),
    Component(
        id="pr-review-toolkit",
        name="PR Review Toolkit",
        description="PR review checklists",
        category="workflow",
        component_type="plugin",
        default=True,
        source="pr-review-toolkit@claude-plugins-official",
    ),
    Component(
        id="feature-dev",
        name="Feature Dev",
        description="Feature development workflows",
        category="workflow",
        component_type="plugin",
        default=True,
        source="feature-dev@claude-plugins-official",
    ),
    Component(
        id="frontend-design",
        name="Frontend Design",
        description="Frontend design and UI helpers",
        category="workflow",
        component_type="plugin",
        default=False,
        source="frontend-design@claude-plugins-official",
    ),
    Component(
        id="plugin-dev",
        name="Plugin Dev",
        description="Plugin development tools",
        category="workflow",
        component_type="plugin",
        default=False,
        source="plugin-dev@claude-plugins-official",
    ),
    Component(
        id="claude-md-management",
        name="CLAUDE.md Management",
        description="CLAUDE.md file management",
        category="workflow",
        component_type="plugin",
        default=True,
        source="claude-md-management@claude-plugins-official",
    ),
    Component(
        id="security-guidance",
        name="Security Guidance",
        description="Security best practices",
        category="workflow",
        component_type="plugin",
        default=True,
        source="security-guidance@claude-plugins-official",
    ),
    Component(
        id="supabase",
        name="Supabase",
        description="Supabase backend integration",
        category="workflow",
        component_type="plugin",
        default=False,
        source="supabase@claude-plugins-official",
    ),
    Component(
        id="rust-analyzer-lsp",
        name="Rust Analyzer LSP",
        description="Rust language server",
        category="workflow",
        component_type="plugin",
        default=False,
        source="rust-analyzer-lsp@claude-plugins-official",
    ),
    # ===== AGENTS (7) =====
    Component(
        id="analyst",
        name="Analyst",
        description="Data analysis and investigation agent",
        category="agent",
        component_type="agent",
        default=True,
        source="agents/analyst.md",
    ),
    Component(
        id="architect",
        name="Architect",
        description="System design and architecture review agent",
        category="agent",
        component_type="agent",
        default=True,
        source="agents/architect.md",
    ),
    Component(
        id="code-reviewer",
        name="Code Reviewer",
        description="Automated code review agent",
        category="agent",
        component_type="agent",
        default=True,
        source="agents/code-reviewer.md",
    ),
    Component(
        id="learning-guide",
        name="Learning Guide",
        description="Interactive learning and tutorial agent",
        category="agent",
        component_type="agent",
        default=False,
        source="agents/learning-guide.md",
    ),
    Component(
        id="security-auditor",
        name="Security Auditor",
        description="Security audit and vulnerability assessment agent",
        category="agent",
        component_type="agent",
        default=True,
        source="agents/security-auditor.md",
    ),
    Component(
        id="socratic-mentor",
        name="Socratic Mentor",
        description="Guided problem-solving through questions",
        category="agent",
        component_type="agent",
        default=False,
        source="agents/socratic-mentor.md",
    ),
    Component(
        id="test-generator",
        name="Test Generator",
        description="Automated test case generation agent",
        category="agent",
        component_type="agent",
        default=True,
        source="agents/test-generator.md",
    ),
    # ===== RULES (3) =====
    Component(
        id="workflow",
        name="Workflow Rules",
        description="Debugging, session orientation, commit flow rules",
        category="rules",
        component_type="rule",
        default=True,
        source="rules/workflow.md",
    ),
    Component(
        id="python",
        name="Python Rules",
        description="Ruff, type hints, pathlib, f-string conventions",
        category="rules",
        component_type="rule",
        default=True,
        source="rules/python.md",
    ),
    Component(
        id="hooks",
        name="Hooks Rules",
        description="Hook development exit codes, stdin parsing, testing",
        category="rules",
        component_type="rule",
        default=True,
        source="rules/hooks.md",
    ),
    # ===== MCP SERVERS (3) =====
    Component(
        id="antigravity-bridge",
        name="Antigravity Bridge",
        description="Multi-model routing to Gemini and other LLMs",
        category="llm",
        component_type="mcp_server",
        default=False,
        source="mcp-servers/antigravity-bridge",
        mcp_config=McpServerConfig(
            command="python3",
            args=["~/.claude/mcp-servers/antigravity-bridge/__main__.py"],
        ),
    ),
    Component(
        id="pi-status",
        name="Pi Status",
        description="Raspberry Pi SSH monitoring and health checks",
        category="hardware",
        component_type="mcp_server",
        default=False,
        source="mcp-servers/pi-status",
        prereqs=["ssh"],
        mcp_config=McpServerConfig(
            command="python3",
            args=["~/.claude/mcp-servers/pi-status/__main__.py"],
        ),
    ),
    Component(
        id="openscad",
        name="OpenSCAD MCP",
        description="CAD rendering, STL generation, and mesh validation",
        category="hardware",
        component_type="mcp_server",
        default=False,
        source="mcp-servers/openscad",
        prereqs=["uv", "openscad"],
        mcp_config=McpServerConfig(
            command="uv",
            args=[
                "run",
                "--directory",
                "~/.claude/mcp-servers/openscad",
                "python3",
                "-m",
                "openscad_mcp",
            ],
        ),
    ),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_registry() -> list[Component]:
    """Return a copy of the full component registry."""
    return list(REGISTRY)


def get_by_type(component_type: str) -> list[Component]:
    """Return all components of a given type."""
    return [c for c in REGISTRY if c.component_type == component_type]


def get_by_category(category: str) -> list[Component]:
    """Return all components in a given category."""
    return [c for c in REGISTRY if c.category == category]


def get_all_prereqs(components: list[Component]) -> set[str]:
    """Collect all unique prerequisites from a list of components."""
    prereqs: set[str] = set()
    for c in components:
        prereqs.update(c.prereqs)
    return prereqs
