#!/bin/bash
# Hook: Auto-lint Python files after edit
# PostToolUse for ^(Write|Edit|MultiEdit)$
INPUT=$(cat 2>/dev/null || true)
[ -z "$INPUT" ] && exit 0
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.file // ""' 2>/dev/null)
[ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ] && exit 0
# Only process Python files
[[ "$FILE_PATH" != *.py ]] && exit 0
# Skip virtual environments, caches, migrations
case "$FILE_PATH" in
    *__pycache__*|*.venv*|*/venv/*|*/migrations/*|*/.tox/*|*/node_modules/*) exit 0 ;;
esac
# Auto-fix with ruff (quiet mode)
if command -v ruff &>/dev/null; then
    ruff check --fix --quiet "$FILE_PATH" 2>/dev/null && \
        echo "Auto-lint: ruff fixed $FILE_PATH" || true
fi
# Informational mypy check (never blocks, first 5 lines only)
if command -v mypy &>/dev/null; then
    MYPY_OUT=$(mypy --no-error-summary "$FILE_PATH" 2>/dev/null | head -5)
    [ -n "$MYPY_OUT" ] && echo "Mypy hints: $MYPY_OUT" || true
fi
exit 0
