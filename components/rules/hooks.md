---
globs: ["**/hooks/*.sh", "**/hooks.json", "**/settings.json"]
---

# Hook Development Rules

- Exit code 2 = BLOCK the tool call. Exit code 0 = ALLOW.
- Hooks read JSON from stdin via `INPUT=$(cat)`. Extract fields with `jq -r`.
- Always fail silently for monitoring hooks (cortex, logging) — use `|| true`.
- Never use interactive commands or prompts in hooks.
- Test hook changes by simulating stdin: `echo '{"tool_input":{"command":"test"}}' | bash hook.sh mode`
- Hook scripts live in `~/.claude/scripts/hooks/`. Registration is in `~/.claude/settings.json` under the `hooks` key.
- Matchers use regex: `^Bash$`, `^(Edit|Write|MultiEdit)$`, etc.
